"""
Harness PMIC — mesure d'energie REELLE sur Raspberry Pi 5 (partie Amine).

Le Pi 5 a une puce d'alimentation (PMIC) qui mesure tension + courant de chaque
rail interne (CPU, RAM, ...). On l'interroge avec `vcgencmd pmic_read_adc`.
Ce module echantillonne le PMIC en arriere-plan (~5 fois/seconde) pendant
qu'on fait autre chose (une inference), puis calcule :
    energie (J) = somme( puissance (W) x duree (s) )   [integration trapeze]

Utilisation (c'est tout) :
    from pmic import MesurePMIC

    with MesurePMIC() as pmic:
        sortie = modele(prompt, max_tokens=64)   # ce qu'on veut mesurer

    print(pmic.energie_joules, pmic.puissance_moyenne_w, pmic.duree_s)

Mode MOCK : si `vcgencmd` n'existe pas (PC Windows/Linux), le module genere de
fausses valeurs plausibles -> on peut developper/tester le code sans le Pi.
Les chiffres mock ne veulent RIEN dire, c'est juste pour la plomberie.
"""

import csv
import re
import shutil
import subprocess
import threading
import time

# Y a-t-il un vrai PMIC ici ? (vcgencmd n'existe que sur le Pi)
PMIC_DISPONIBLE = shutil.which("vcgencmd") is not None

# Une ligne de vcgencmd ressemble a :  " VDD_CORE_A current(15)=0.39000000A"
#                                      " VDD_CORE_V volt(15)=0.75000000V"
# -> on capture le nom du rail (VDD_CORE), le type (A ou V) et la valeur.
LIGNE_ADC = re.compile(r"^\s*(\w+)_([AV])\s+\w+\(\d+\)=([\d.]+)[AV]\s*$")


def lire_rails():
    """Interroge le PMIC une fois. Renvoie {rail: puissance_W} + cle 'TOTAL'."""
    sortie = subprocess.run(
        ["vcgencmd", "pmic_read_adc"], capture_output=True, text=True
    ).stdout

    courants, tensions = {}, {}
    for ligne in sortie.splitlines():
        m = LIGNE_ADC.match(ligne)
        if m:
            rail, type_mesure, valeur = m.group(1), m.group(2), float(m.group(3))
            (courants if type_mesure == "A" else tensions)[rail] = valeur

    # puissance d'un rail = tension x courant (uniquement si on a les deux)
    puissances = {
        rail: tensions[rail] * courants[rail]
        for rail in courants
        if rail in tensions
    }
    puissances["TOTAL"] = sum(puissances.values())
    return puissances


def lire_rails_mock():
    """Fausses valeurs pour developper sans Pi (idle ~1,5 W + un peu de bruit)."""
    import random

    p = {
        "VDD_CORE": 0.39 + random.uniform(-0.05, 0.05),
        "DDR_VDD2": 0.25 + random.uniform(-0.02, 0.02),
        "AUTRES":   0.90 + random.uniform(-0.05, 0.05),
    }
    p["TOTAL"] = sum(p.values())
    return p


class MesurePMIC:
    """Echantillonne le PMIC dans un thread pendant le bloc `with`."""

    def __init__(self, hz=5):
        self.intervalle = 1.0 / hz
        self.echantillons = []          # liste de (instant_s, {rail: W})
        # Resultats (remplis a la sortie du `with`) :
        self.duree_s = 0.0
        self.energie_joules = 0.0       # energie TOTALE onboard sur la duree
        self.energie_par_rail = {}      # detail par composant (VDD_CORE = CPU...)
        self.puissance_moyenne_w = 0.0
        self.mock = not PMIC_DISPONIBLE
        self._stop = threading.Event()
        self._thread = None

    def _boucle(self):
        lire = lire_rails_mock if self.mock else lire_rails
        while not self._stop.is_set():
            self.echantillons.append((time.perf_counter(), lire()))
            self._stop.wait(self.intervalle)

    def __enter__(self):
        if self.mock:
            print("[pmic] vcgencmd absent -> mode MOCK (fausses valeurs, dev seulement)")
        self._stop.clear()
        self._thread = threading.Thread(target=self._boucle, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()
        self._calculer()
        return False  # ne pas avaler les exceptions du bloc mesure

    def _calculer(self):
        """Integration trapeze : energie = somme( (P1+P2)/2 x dt ) entre echantillons."""
        if len(self.echantillons) < 2:
            return
        rails = self.echantillons[0][1].keys()
        energie = dict.fromkeys(rails, 0.0)
        for (t1, p1), (t2, p2) in zip(self.echantillons, self.echantillons[1:]):
            dt = t2 - t1
            for rail in rails:
                energie[rail] += (p1[rail] + p2[rail]) / 2 * dt

        self.duree_s = self.echantillons[-1][0] - self.echantillons[0][0]
        self.energie_par_rail = energie
        self.energie_joules = energie["TOTAL"]
        self.puissance_moyenne_w = energie["TOTAL"] / self.duree_s

    def sauver_courbe_csv(self, chemin):
        """Ecrit tous les echantillons (la courbe de puissance) dans un CSV."""
        if not self.echantillons:
            return
        t0 = self.echantillons[0][0]
        rails = list(self.echantillons[0][1].keys())
        with open(chemin, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t_s"] + [f"{r}_w" for r in rails])
            for t, p in self.echantillons:
                w.writerow([round(t - t0, 3)] + [round(p[r], 4) for r in rails])


# Petit test autonome : `python pmic.py --duree 10 --csv courbe.csv`
# (lancer une charge a cote, ex. `yes > /dev/null`, pour voir VDD_CORE monter)
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Mesure PMIC pendant N secondes")
    ap.add_argument("--duree", type=float, default=10, help="duree de mesure (s)")
    ap.add_argument("--hz", type=float, default=5, help="echantillons par seconde")
    ap.add_argument("--csv", help="sauver la courbe de puissance dans ce fichier")
    args = ap.parse_args()

    with MesurePMIC(hz=args.hz) as pmic:
        time.sleep(args.duree)

    print(f"Duree            : {pmic.duree_s:.2f} s ({len(pmic.echantillons)} echantillons)")
    print(f"Energie totale   : {pmic.energie_joules:.2f} J")
    print(f"Puissance moyenne: {pmic.puissance_moyenne_w:.3f} W")
    for rail, e in sorted(pmic.energie_par_rail.items(), key=lambda x: -x[1]):
        if rail != "TOTAL" and e > 0.01:
            print(f"  - {rail:<12} {e:7.2f} J")
    if args.csv:
        pmic.sauver_courbe_csv(args.csv)
        print(f"Courbe sauvee dans {args.csv}")
