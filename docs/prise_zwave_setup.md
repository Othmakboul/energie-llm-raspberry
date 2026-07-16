# Mise en place de la prise connectée (méthode 3 : mesure au mur)

> Matériel : prise **Aeotec Smart Switch 7 (ZW175-C16)** + clé contrôleur **Z-Stick 7 (ZWA010-C)**, Z-Wave EU 868 MHz.
> Objectif : lire par script l'énergie au mur (compteur kWh cumulé + puissance W) pendant les campagnes,
> comme 3e méthode à côté de CodeCarbon (méthode 1) et du PMIC (méthode 2).

La ZW175 **n'a pas d'écran** : on ne peut la lire qu'à travers un contrôleur Z-Wave logiciel.
On utilise **zwave-js-ui** (interface web pour l'appairage + serveur API websocket sur le port 3000).
Le module `src/prise.py` se connecte à ce serveur.

---

## 1. Brancher la clé Z-Stick et trouver son port

Brancher le Z-Stick sur un port USB du **Pi**, puis :

```bash
ls -l /dev/serial/by-id/
```

Noter le chemin stable (ex. `usb-0658_0200-if00` — VID:PID `0658:0200` = contrôleur Silicon Labs 700).
La clé apparaît comme un périphérique **`/dev/ttyACM0`** (CDC-ACM), mais on utilise le chemin `by-id`
car `ttyACM0` peut changer de numéro après un replug.

## 2. Lancer zwave-js-ui (Docker)

Remplacer `INSERER_CHEMIN_BY_ID` par le chemin trouvé à l'étape 1 :

```bash
docker run -d --restart unless-stopped \
  -p 8091:8091 -p 3000:3000 \
  --device=/dev/serial/by-id/INSERER_CHEMIN_BY_ID:/dev/zwave \
  -v "$HOME/zwave-store":/usr/src/app/store \
  zwavejs/zwave-js-ui:latest
```

- `8091` = interface web, `3000` = API websocket (utilisée par `prise.py`).
- L'image est multi-arch (arm64) → tourne sur le Pi 5 64-bit.
- Si Docker n'est pas installé : `curl -fsSL https://get.docker.com | sh` puis `sudo usermod -aG docker $USER` (relog).

## 3. Configurer le contrôleur dans l'UI

Ouvrir `http://<ip-du-pi>:8091` → **Settings** :
- **Z-Wave → Serial Port** = `/dev/zwave` (le chemin mappé dans le conteneur).
- **Region** = `Europe`.
- **Home Assistant / WS Server** : activer le **WS Server** sur le port **3000** (souvent activé par défaut).
- Sauvegarder. Le contrôleur doit passer à l'état *ready*.

## 4. Appairer la prise (inclusion)

1. Brancher la ZW175 sur la prise murale qui **alimente l'alim USB-C du Pi** (c'est ça qu'on veut mesurer).
2. Dans l'UI : **Control Panel → Actions → Inclusion** (ajouter un nœud), choisir l'inclusion **sécurisée (S2)**.
3. Mettre la ZW175 en mode appairage : appuyer brièvement sur son **bouton** (voir notice ; en général 1 appui = action/inclusion).
4. L'inclusion S2 demande la **clé DSK de la prise** : scanner le **QR code imprimé sur la ZW175 elle-même**
   (sur le boîtier, à côté du bouton) avec l'appareil photo du téléphone/PC, ou saisir le code manuellement
   si l'UI le demande. Sans ce code, l'inclusion sécurisée échoue.
5. Le nœud apparaît dans la liste. **Noter son `node_id`** (ex. 2).

## 5. Vérifier les valeurs (étape de validation indispensable)

Dans **Control Panel**, sélectionner le nœud de la prise, onglet **Values** :
- repérer la valeur **`Electric_kWh_Consumed`** (énergie cumulée, kWh) et **`Electric_W_Consumed`** (puissance, W) ;
- vérifier leur **`propertyKey`** (attendus : kWh = `65537`, W = `66049`) et l'**endpoint** (attendu : `0`).

**Attention : si les `propertyKey` / endpoint diffèrent sur ton firmware**, les reporter dans `src/prise.py`
(constantes `CLE_KWH`, `CLE_W`, `ENDPOINT`, `NODE_ID`).

Onglet **Configuration** : vérifier la résolution du compteur kWh (pas de 0,01 vs 0,001 kWh) —
c'est ce qui décide si un lot court suffit à faire bouger le compteur.

## 6. Régler les paramètres de report (report dense)

Soit à la main dans l'onglet **Configuration**, soit en une commande :

```bash
python src/prise.py --config --node <node_id>
```

Valeurs appliquées (cf. `PARAMS_RECOMMANDES` dans `prise.py`) :

| Param | Valeur | Effet |
|------:|:------:|-------|
| 101 | 3 | report périodique = kWh + Watt (bitmask 1=kWh, 2=W) |
| 111 | 30 | intervalle du report périodique = 30 s (plancher conseillé) |
| 91 | 1 | report aussi dès que la puissance varie de ≥ 1 W |
| 92 | 1 | report aussi dès que l'énergie varie d'un cran |

> Note : la ZW175 n'a **qu'un seul** groupe de report (101) et **un seul** intervalle (111) —
> pas de 102/103/112/113 (ça, c'est le HEM Gen5). Ne pas essayer de les régler.

## 7. Tester la lecture (sans campagne)

```bash
pip install websocket-client          # dépendance de prise.py
python src/prise.py --duree 60 --node <node_id> --csv data/raw/test_prise.csv
```

Doit afficher `kWh debut -> fin`, l'énergie au mur (J) et la puissance moyenne (~6–8 W au repos).
Si `delta kWh = 0` : le lot est trop court pour la résolution → rallonger `--duree`.

## 8. Mesurer la baseline idle (pour l'énergie marginale)

Pi au repos (aucune inférence), sur 2 min :

```bash
python src/prise.py --duree 120 --node <node_id>
```

Reporter la **Puissance moyenne** affichée dans `BASELINE_W` de `src/campaign.py`.
Ainsi le résumé campagne calcule l'énergie **marginale** d'inférence (mur total − idle).

## 9. Lancer la campagne avec les 3 méthodes

Dans `src/campaign.py`, vérifier : `MESURER_PRISE = True`, `PRISE_NODE_ID = <node_id>`, `BASELINE_W = <idle>`.

```bash
python src/campaign.py
```

Sorties dans `data/raw/` :
- `resultats_<machine>_<date>.csv` — par requête : CodeCarbon + PMIC (inchangé) ;
- `resultats_<machine>_<date>_prise.csv` — résumé du lot au mur + recoupement des 3 méthodes (rendement PMIC/mur) ;
- `courbe_prise_<machine>_<date>.csv` — courbe de puissance au mur.

---

## Limites à garder en tête (pour le rapport)
- La prise mesure **tout le système au mur** (Pi + pertes de l'alim PD) → surestime le « Pi seul » ;
  c'est la **référence système total**, pas une mesure par composant (ça, c'est le PMIC).
- Précision instantanée ~±3 W, basse résolution temporelle → on s'appuie sur le **compteur kWh cumulé sur un lot**,
  pas sur la puissance instantanée.
- Le temps de **chargement des modèles** est inclus dans la mesure au mur (il est dans la boucle) →
  le « rendement PMIC/mur » est **indicatif**, à interpréter au niveau du lot, pas requête par requête.
