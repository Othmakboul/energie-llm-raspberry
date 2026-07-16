# Tutoriel Raspberry Pi — installation complète du projet

Procédure pour installer le projet sur un Raspberry Pi 5 (16 Go) depuis zéro :
flash de l'OS, dépendances, modèles, premier test, prise connectée. À suivre
dans l'ordre. Pour la mesure PMIC et le protocole complet, voir
`architecture_mesure.md` ; pour la prise connectée en détail, voir
`prise_zwave_setup.md`.

---

## 1. Flasher le bon OS (étape critique)

Le Raspberry Pi 5 doit tourner en **64 bits**. Un OS 32 bits (armhf) casse la
compilation de `llama-cpp-python` et plafonne la RAM utilisable à ~3 Go, même
si les 16 Go sont installés.

Piège connu : un Raspberry Pi OS 32 bits peut utiliser un noyau 64 bits, donc
`uname -m` répond `aarch64` même en 32 bits et fait croire que tout va bien.
Le seul test fiable :

```bash
dpkg --print-architecture     # doit repondre arm64 (32 bits = armhf)
getconf LONG_BIT              # doit repondre 64
```

### Flash

Avec **Raspberry Pi Imager** sur un PC :
1. Choisir l'image **Raspberry Pi OS (64-bit)** — bien vérifier le "(64-bit)".
2. Dans les options avancées (roue crantée) avant d'écrire : nom d'utilisateur,
   WiFi configuré et SSH activé (pour un premier démarrage en headless).
3. Écrire la carte SD (efface tout le contenu existant), l'insérer dans le Pi,
   démarrer.
4. Une fois connecté : vérifier `dpkg --print-architecture` -> `arm64`.

---

## 2. Installer les paquets système

```bash
sudo apt update && sudo apt install -y libopenblas0 build-essential cmake git
```

- `libopenblas0` : bibliothèque de calcul matriciel dont numpy (utilisé par
  pandas et CodeCarbon) a besoin sur ARM. Sans elle : `ImportError:
  libopenblas.so.0: cannot open shared object file`. (Si le paquet est
  introuvable : `libopenblas-dev`.)
- `build-essential cmake` : compilateur C/C++ + cmake, nécessaires pour
  compiler `llama-cpp-python` (pas de wheel précompilé pour ARM sur PyPI).
- `git` : pour cloner le dépôt.

---

## 3. Cloner le dépôt

```bash
cd ~
git clone <URL-du-depot-GitHub> energie-llm-raspberry
cd energie-llm-raspberry
```

---

## 4. Environnement Python (venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install websocket-client   # dependance de src/prise.py, pas dans requirements.txt
```

Le venv isole les paquets du projet du Python système (Raspberry Pi OS
Bookworm refuse les installations globales avec `externally-managed-environment`).
Il faut réactiver le venv à chaque nouveau terminal : `source .venv/bin/activate`
(le prompt affiche alors `(.venv)`).

`llama-cpp-python` compile depuis les sources sur le Pi : compter 15 à 30
minutes, c'est normal. En cas d'échec, capturer le log complet et chercher les
vraies erreurs (le message générique "CMake build failed" seul ne dit rien) :

```bash
pip install llama-cpp-python --verbose 2>&1 | tee /tmp/build.log
grep -iE "error|fatal|no such file|undefined" /tmp/build.log | head -20
```

---

## 5. Télécharger les modèles

Trois familles, plusieurs niveaux de quantification chacune, à poser dans
`models/` (dossier non versionné) :

| Modèle | Quantifications testées |
|---|---|
| Llama-3.2-1B-Instruct | Q3_K_L, Q4_K_M, Q8_0 |
| Qwen2.5-1.5B-Instruct | Q3_K_L, Q4_K_M, Q8_0 |
| Gemma-3-1B-it | Q3_K_M, Q4_K_M, Q8_0 |

Exemple pour un fichier :

```bash
wget -P models/ "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
```

Chercher les autres fichiers `.gguf` (même schéma de nommage) dans les dépôts
Hugging Face `bartowski/<modele>-GGUF`. Les noms de fichiers exacts attendus
par les scripts de campagne sont dans les listes `MODELES` en tête de
`src/campaign.py` et des autres `src/campaign_*.py`.

---

## 6. Premier test

```bash
python src/inference.py      # le modele charge et repond ?
```

Puis un test de la chaîne de mesure logicielle seule (pas de LLM, juste pour
valider CodeCarbon + psutil sur le Pi) :

```bash
python src/measure.py
```

CodeCarbon ne connaît pas le CPU du Pi (pas de RAPL sur ARM) : il se rabat sur
un TDP par défaut, donc le chiffre d'énergie affiché est probablement éloigné
de la réalité. Ce n'est pas un problème en soi : c'est justement pourquoi le
projet mesure aussi via le PMIC et la prise connectée (voir
`architecture_mesure.md`).

---

## 7. Prise connectée (méthode 3)

Installation, appairage (inclusion S2 via le QR code imprimé sur la prise) et
configuration détaillées dans `prise_zwave_setup.md`. Nécessaire avant de
lancer une campagne avec `MESURER_PRISE = True`.

---

## 8. Lancer une campagne

```bash
python src/build_prompts.py   # une seule fois : construit prompts/prompts.json
python src/campaign.py        # campagne principale (regler les constantes en tete de fichier avant)
```

Toujours lancer les scripts depuis la racine du dépôt : les chemins
(`models/...`, `prompts/...`, `data/...`) sont relatifs.

Une campagne complète peut tourner plusieurs heures sur le Pi (nettement plus
lent qu'un PC). Pour un premier passage de validation, réduire temporairement
la grille testée (moins de modèles, moins de valeurs de `max_tokens`) avant de
lancer la campagne complète.

---

## Pièges connus (résumé)

| Symptôme | Cause | Solution |
|---|---|---|
| `ImportError: libopenblas.so.0` | Lib système OpenBLAS absente | `sudo apt install libopenblas0` |
| `CMake build failed` sur llama-cpp-python | OS 32 bits (armhf) flashé par erreur | Reflash en Raspberry Pi OS 64-bit, vérifier avec `dpkg --print-architecture` |
| `pip install` échoue avec `externally-managed-environment` | Installation hors venv | Toujours travailler dans le venv (`source .venv/bin/activate`) |
| Énergie CodeCarbon manifestement fausse sur le Pi | RAPL absent sur ARM, CodeCarbon retombe sur un TDP générique | Attendu — se fier au PMIC et à la prise (méthodes 2 et 3), pas à CodeCarbon seul |
