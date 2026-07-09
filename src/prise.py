"""
Harness PRISE — mesure d'energie au MUR via prise connectee Aeotec Smart Switch 7
(ZW175-C16, Z-Wave) lue avec la cle Z-Stick 7 (partie Amine, methode 3).

C'est la 3e methode de mesure du projet, complementaire :
    - CodeCarbon  -> estimation logicielle (TDP / %CPU)
    - PMIC        -> mesure ONBOARD du Pi 5 (rails internes, vcgencmd)
    - PRISE       -> mesure au MUR (systeme complet : Pi + pertes de l'alim PD)

La prise n'a PAS d'ecran : on l'interroge a travers un controleur Z-Wave logiciel
(zwave-js-ui) qui expose une API websocket (port 3000). Ce module s'y connecte,
lit le REGISTRE D'ENERGIE CUMULE (kWh) du firmware aux bornes d'un bloc de mesure,
et ecoute en parallele les remontees de PUISSANCE (W) pour tracer une courbe.

    energie (J) = ( kWh_fin - kWh_debut ) x 3 600 000

On utilise le compteur kWh du firmware (et PAS l'integration de la puissance W)
car cet accumulateur materiel est bien plus precis que d'integrer une puissance
bruitee, lente et imprecise (la ZW175 est donnee a +/- 3 W en instantane).

ATTENTION methodo (a cause de la lenteur radio + resolution du compteur) :
  - La prise se mesure au niveau d'un LOT de requetes, pas d'une requete isolee :
    sur un lot court, le delta kWh peut etre sous la resolution du compteur (=> 0 J).
    Faire tourner un lot assez long pour que le compteur bouge de plusieurs crans.
  - La prise mesure TOUT le systeme (Pi au repos + inference + pertes alim).
    Pour isoler l'energie MARGINALE d'inference, soustraire une baseline idle :
    passer `baseline_w` (puissance au mur Pi au repos, mesuree a part).

Utilisation (meme esprit que pmic.MesurePMIC) :
    from prise import MesurePrise

    with MesurePrise(node_id=2) as prise:
        ...                                  # le lot de requetes a mesurer

    print(prise.energie_joules, prise.puissance_moyenne_w, prise.duree_s)

Mode MOCK : si le module `websocket` (websocket-client) est absent ou si la
connexion au controleur echoue, on genere de fausses valeurs plausibles
(~6 W au mur) -> on developpe/teste la plomberie sans la prise. Les chiffres
mock ne veulent RIEN dire.

Pre-requis cote Pi : zwave-js-ui lance (voir docs/prise_zwave_setup.md), prise
appairee, et `pip install websocket-client`.
"""

import csv
import json
import threading
import time

# Client websocket synchrone (leger). Absent -> on bascule en mock.
try:
    import websocket  # paquet pip : websocket-client
    WS_DISPONIBLE = True
except ImportError:
    WS_DISPONIBLE = False

# ============================================================
#  REGLAGES PRISE  (a confirmer sur ton appareil apres appairage)
# ============================================================
URL_WS = "ws://localhost:3000"   # API zwave-js-server (embarquee dans zwave-js-ui)
NODE_ID = 3                      # /!\ numero du noeud de la prise apres inclusion (a verifier dans l'UI)

# Identifiants des valeurs Meter (Command Class 50 / 0x32) cote zwave-js.
# Le `propertyKey` encode (type, scale). Valeurs typiques de la ZW175 :
#   kWh cumule (Electric_kWh_Consumed, scale 0) -> 65537
#   Puissance W (Electric_W_Consumed,  scale 2) -> 66049
# /!\ A VERIFIER dans l'onglet "Values" de zwave-js-ui (varie selon firmware).
CC_METER = 50
ENDPOINT = 0
CLE_KWH = 65537
CLE_W = 66049

TIMEOUT_LECTURE = 8.0            # s : attente max d'une reponse de lecture kWh
# ============================================================


def _valueid(cle):
    """Construit le valueId zwave-js pour une mesure Meter (kWh ou W)."""
    return {"commandClass": CC_METER, "endpoint": ENDPOINT, "property": "value", "propertyKey": cle}


class MesurePrise:
    """Mesure l'energie au mur sur la duree du bloc `with`, via la prise Z-Wave.

    energie_joules    : energie au mur (delta du compteur kWh du firmware)
    puissance_moyenne_w : energie_joules / duree_s
    echantillons      : liste de (instant_s, W) remontes par la prise (courbe)
    energie_marginale_joules : energie_joules - baseline_w * duree_s (si baseline fournie)
    """

    def __init__(self, node_id=NODE_ID, url=URL_WS, baseline_w=0.0):
        self.node_id = node_id
        self.url = url
        self.baseline_w = baseline_w        # puissance idle au mur a soustraire (W)
        # Resultats (remplis a la sortie du `with`) :
        self.duree_s = 0.0
        self.kwh_debut = None
        self.kwh_fin = None
        self.energie_joules = 0.0
        self.energie_marginale_joules = 0.0
        self.puissance_moyenne_w = 0.0
        self.echantillons = []              # (instant_s, W)
        self.mock = not WS_DISPONIBLE
        # Plomberie websocket :
        self._ws = None
        self._t0 = 0.0
        self._mid = 0                       # compteur de messageId
        self._resultats = {}                # messageId -> valeur de reponse
        self._events = {}                   # messageId -> threading.Event
        self._stop = threading.Event()
        self._thread = None

    # ---- connexion + protocole zwave-js-server -------------------------------

    def _connecter(self):
        """Ouvre le websocket, negocie le schema et demarre le flux d'evenements."""
        self._ws = websocket.create_connection(self.url, timeout=TIMEOUT_LECTURE)
        version = json.loads(self._ws.recv())          # 1er message pousse par le serveur
        schema = version.get("maxSchemaVersion", 0)    # on s'aligne sur le serveur
        self._envoyer({"command": "set_api_schema", "schemaVersion": schema})
        self._ws.recv()                                # ack du set_api_schema
        self._envoyer({"command": "start_listening"})  # -> etat complet puis events live
        self._ws.recv()                                # etat initial (ignore)

    def _envoyer(self, msg):
        """Envoie une commande avec un messageId unique. Renvoie ce messageId."""
        self._mid += 1
        mid = str(self._mid)
        msg["messageId"] = mid
        self._ws.send(json.dumps(msg))
        return mid

    def _lire_kwh(self):
        """Lit le compteur kWh via une connexion COURTE et FRAICHE, dediee a cette lecture.

        /!\ Ne PAS reutiliser self._ws ici : sur une connexion gardee ouverte tout le
        lot (campagne longue), interroger deux fois la meme connexion renvoie le MEME
        snapshot fige au moment de la connexion (kwh_debut == kwh_fin garanti, meme
        apres des heures) -> delta toujours 0. Une connexion neuve a chaque lecture
        force le serveur a renvoyer l'etat CACHE ACTUEL (celui que l'UI affiche aussi).
        """
        ws = websocket.create_connection(self.url, timeout=TIMEOUT_LECTURE)
        try:
            version = json.loads(ws.recv())
            schema = version.get("maxSchemaVersion", 0)
            ws.send(json.dumps({"messageId": "s", "command": "set_api_schema", "schemaVersion": schema}))
            ws.recv()
            ws.send(json.dumps({
                "messageId": "g",
                "command": "node.get_value",
                "nodeId": self.node_id,
                "valueId": _valueid(CLE_KWH),
            }))
            rep = json.loads(ws.recv())
            res = rep.get("result") if isinstance(rep, dict) else None
            val = res.get("value") if isinstance(res, dict) else res
            if val is not None:
                return float(val)
        finally:
            ws.close()
        # repli : derniere valeur kWh vue passer dans les events de la connexion longue
        return getattr(self, "_dernier_kwh", None)

    def _boucle_ws(self):
        """Thread lecteur : recoit messages, range les reponses, collecte la courbe W."""
        while not self._stop.is_set():
            try:
                msg = json.loads(self._ws.recv())
            except Exception:
                break                                  # ws ferme -> on sort
            type_ = msg.get("type")
            if type_ == "result":
                mid = msg.get("messageId")
                res = msg.get("result") or {}
                # selon les versions la valeur est sous result.value ou directement
                self._resultats[mid] = res.get("value", res) if isinstance(res, dict) else res
                ev = self._events.pop(mid, None)
                if ev:
                    ev.set()
            elif type_ == "event":
                e = msg.get("event", {})
                if e.get("event") == "value updated":
                    a = e.get("args", {})
                    if a.get("commandClass") == CC_METER:
                        if a.get("propertyKey") == CLE_W:
                            self.echantillons.append((time.perf_counter(), float(a["newValue"])))
                        elif a.get("propertyKey") == CLE_KWH:
                            self._dernier_kwh = float(a["newValue"])

    # ---- contexte de mesure --------------------------------------------------

    def __enter__(self):
        if self.mock:
            print("[prise] websocket/controleur absent -> mode MOCK (fausses valeurs, dev seulement)")
            self._t0 = time.perf_counter()
            return self
        self._connecter()
        self._stop.clear()
        self._thread = threading.Thread(target=self._boucle_ws, daemon=True)
        self._thread.start()
        self._t0 = time.perf_counter()
        self.kwh_debut = self._lire_kwh()
        return self

    def __exit__(self, *exc):
        if self.mock:
            self._calculer_mock()
            return False
        self.kwh_fin = self._lire_kwh()
        self.duree_s = time.perf_counter() - self._t0
        self._stop.set()
        try:
            self._ws.close()                           # debloque le recv() du thread
        except Exception:
            pass
        if self._thread:
            self._thread.join(timeout=2.0)
        self._calculer()
        return False  # ne pas avaler les exceptions du bloc mesure

    def _calculer(self):
        if self.kwh_debut is not None and self.kwh_fin is not None:
            self.energie_joules = (self.kwh_fin - self.kwh_debut) * 3_600_000
        if self.duree_s > 0:
            self.puissance_moyenne_w = self.energie_joules / self.duree_s
        self.energie_marginale_joules = self.energie_joules - self.baseline_w * self.duree_s

    def _calculer_mock(self):
        """Fausse mesure : ~6 W au mur + bruit, pour valider la plomberie sans prise."""
        import random
        self.duree_s = time.perf_counter() - self._t0
        w = 6.0 + random.uniform(-0.3, 0.3)
        self.kwh_debut = 0.0
        self.kwh_fin = w * self.duree_s / 3_600_000
        self.energie_joules = w * self.duree_s
        self.puissance_moyenne_w = w
        self.energie_marginale_joules = self.energie_joules - self.baseline_w * self.duree_s
        # quelques faux echantillons W repartis sur la duree
        n = max(2, int(self.duree_s))
        for i in range(n):
            self.echantillons.append((self._t0 + i * self.duree_s / n, w + random.uniform(-0.3, 0.3)))

    def sauver_courbe_csv(self, chemin):
        """Ecrit la courbe de puissance au mur (echantillons W) dans un CSV."""
        if not self.echantillons:
            return
        t0 = self.echantillons[0][0]
        with open(chemin, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t_s", "w_mur"])
            for t, p in self.echantillons:
                w.writerow([round(t - t0, 3), round(p, 3)])


# ============================================================
#  Reglage des parametres de report de la ZW175 (a faire UNE fois)
#  -> report dense : kWh + W toutes les 30 s + sur variation >= 1 W
#  Equivalent a le faire a la main dans l'onglet "Configuration" de zwave-js-ui.
# ============================================================
PARAMS_RECOMMANDES = {
    101: 3,    # contenu du report periodique (bitmask : 1=kWh, 2=W) -> kWh + W
    111: 30,   # intervalle du report periodique (s) : 30 = plancher conseille
    91: 1,     # seuil report sur variation de puissance (W)
    92: 1,     # seuil report sur variation d'energie
}


def configurer_prise(node_id=NODE_ID, url=URL_WS, params=PARAMS_RECOMMANDES):
    """Ecrit les parametres de report (Configuration CC 112) via l'API websocket."""
    if not WS_DISPONIBLE:
        print("[prise] websocket absent -> impossible de configurer (mode dev).")
        return
    ws = websocket.create_connection(url, timeout=TIMEOUT_LECTURE)
    version = json.loads(ws.recv())
    ws.send(json.dumps({"messageId": "s", "command": "set_api_schema",
                        "schemaVersion": version.get("maxSchemaVersion", 0)}))
    ws.recv()
    for i, (param, valeur) in enumerate(params.items()):
        ws.send(json.dumps({
            "messageId": f"c{i}",
            "command": "node.set_value",
            "nodeId": node_id,
            "valueId": {"commandClass": 112, "endpoint": 0, "property": param},
            "value": valeur,
        }))
        rep = json.loads(ws.recv())
        ok = rep.get("success", False)
        print(f"  param {param} = {valeur}  -> {'OK' if ok else 'ECHEC ' + str(rep.get('errorCode',''))}")
    ws.close()


# Petit test autonome :
#   python prise.py --duree 30 --csv courbe_prise.csv     (mesure 30 s)
#   python prise.py --config                              (regle les params ZW175)
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Mesure prise Z-Wave (au mur) pendant N secondes")
    ap.add_argument("--duree", type=float, default=30, help="duree de mesure (s)")
    ap.add_argument("--node", type=int, default=NODE_ID, help="node_id de la prise")
    ap.add_argument("--baseline", type=float, default=0.0, help="puissance idle au mur a soustraire (W)")
    ap.add_argument("--csv", help="sauver la courbe de puissance dans ce fichier")
    ap.add_argument("--config", action="store_true", help="regler les parametres de report de la prise puis quitter")
    args = ap.parse_args()

    if args.config:
        configurer_prise(node_id=args.node)
        raise SystemExit

    with MesurePrise(node_id=args.node, baseline_w=args.baseline) as prise:
        time.sleep(args.duree)

    print(f"Duree              : {prise.duree_s:.1f} s ({len(prise.echantillons)} echantillons W)")
    print(f"kWh debut / fin    : {prise.kwh_debut} -> {prise.kwh_fin}")
    print(f"Energie au mur     : {prise.energie_joules:.1f} J")
    if args.baseline:
        print(f"Energie marginale  : {prise.energie_marginale_joules:.1f} J (apres -{args.baseline} W idle)")
    print(f"Puissance moyenne  : {prise.puissance_moyenne_w:.2f} W")
    if prise.energie_joules == 0 and not prise.mock:
        print("  /!\\ delta kWh = 0 : lot trop court pour la resolution du compteur -> rallonger.")
    if args.csv:
        prise.sauver_courbe_csv(args.csv)
        print(f"Courbe sauvee dans {args.csv}")
