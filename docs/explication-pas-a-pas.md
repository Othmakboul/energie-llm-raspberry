# Explication pas à pas — tout ce qu'on a fait jusqu'à maintenant

> Ce document retrace CHAQUE étape du début du stage jusqu'à aujourd'hui (J3),
> avec les explications simples. À relire avant le rapport ou pour réviser.

---

## Étape 0 — La préparation (J1-J2)

### Ce qu'on a fait
1. Créé le dépôt GitHub `energie-llm-raspberry` (code partagé avec Amine).
2. Déplacé le projet sur `D:\2025_Recherche\` (C: n'avait plus de place).
3. Créé un **venv** (environnement virtuel Python) dans `.venv\`.
4. Installé les bibliothèques : `llama-cpp-python`, `codecarbon`, `psutil`, `pandas`, `streamlit`.
5. Vérifié le `.gitignore` : il exclut de git le venv, les modèles `.gguf` (trop lourds)
   et les données `data/` (propres à chaque machine).

### Pourquoi
- Le **venv** = une boîte à outils Python propre au projet, isolée du reste du PC.
- Le **.gitignore** = la liste de ce que git ne doit PAS envoyer sur GitHub.

### Piège rencontré (Windows)
- `llama-cpp-python` ne compile pas sur Windows (erreur « Long Path »).
  Solution : installer le **wheel pré-compilé** :
  `pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu`

---

## Étape 1 — Les notions de base (à connaître par cœur)

| Notion | Explication simple |
|---|---|
| **LLM** | Programme qui a appris à prédire le mot suivant. Il ne « comprend » pas, il calcule des probabilités. |
| **Prompt** | Le texte qu'on lui donne (la question). |
| **Token** | Morceau de mot (~3/4 de mot). Le modèle lit et écrit token par token. |
| **Inférence** | Le moment où le modèle répond. C'est CE qu'on mesure. |
| **Paramètres (1B, 3B…)** | La taille du « cerveau ». B = milliard. Plus gros = plus malin mais plus lent et gourmand. |
| **Quantification (Q2/Q4/Q8)** | Arrondir les nombres du modèle pour le compresser (comme un JPEG). Q4_K_M = le standard. |
| **GGUF** | Le format de fichier d'un modèle quantifié (comme .mp3 pour la musique). |
| **llama.cpp** | Le « lecteur » qui fait tourner les .gguf sur CPU. `llama-cpp-python` = sa télécommande Python. |
| **RAM vs CPU** | RAM = plan de travail (16 Go sur notre Pi → pas un souci). CPU = l'ouvrier qui calcule → c'est LUI la limite. |
| **Watt / Joule** | Watt = puissance instantanée (robinet ouvert). Joule = énergie totale (eau écoulée) = puissance × durée. 1 kWh = 3 600 000 J. |
| **RAPL** | Compteur d'énergie intégré aux processeurs Intel/AMD. Le Pi n'en a PAS → tout le défi du stage. |

---

## Étape 2 — Télécharger un modèle (J3 matin)

### Ce qu'on a fait
Téléchargé `Llama-3.2-1B-Instruct-Q4_K_M.gguf` (770 Mo) depuis Hugging Face
(dépôt `bartowski/Llama-3.2-1B-Instruct-GGUF`) → posé dans `models/`.

### Pourquoi ce modèle
- **1B** = petit → rapide à tester, et c'est le « meilleur compromis énergie/qualité »
  selon l'article [3] de la biblio du sujet.
- **Instruct** = dressé pour répondre à des questions (pas juste compléter du texte).
- **Q4_K_M** = la quantification standard utilisée dans tous les articles → comparable.

### Comment choisir un modèle (critères)
1. Format `.gguf` (sinon ça ne tourne pas sur llama.cpp)
2. Version `Instruct`
3. Taille adaptée à la machine (1B pour commencer)
4. Quantification Q4_K_M par défaut
5. Famille récente (Llama 3.2, Qwen2.5, Gemma) bien optimisée ARM

---

## Étape 3 — inference.py : faire parler le modèle (J3)

### Le code, ligne par ligne
```python
from llama_cpp import Llama      # importer la classe qui lit les .gguf
import time                       # le chronomètre Python

# 1. Charger le modèle (HORS chrono : on mesure la requête, pas le chargement)
mon_modele = Llama(model_path="models/Llama-3.2-1B-Instruct-Q4_K_M.gguf", verbose=False)

# 2. Chrono : départ JUSTE avant la génération
debut = time.perf_counter()

# 3. Poser la question
resultat = mon_modele("Quelle est la capitale de la France ?", max_tokens=64, stop=["\n"])

# 4. Chrono : stop JUSTE après
duree = time.perf_counter() - debut

# 5. Extraire les infos du résultat (un dictionnaire = boîte à étiquettes)
texte = resultat["choices"][0]["text"]
nb_tokens = resultat["usage"]["completion_tokens"]

print(texte)
print(f"{nb_tokens} tokens en {duree:.2f} secondes")
```

### Les paramètres importants
- `max_tokens=64` : nombre MAXIMUM de tokens à générer.
- `stop=["\n"]` : s'arrêter au premier retour à la ligne (sinon le modèle
  « radote » jusqu'à épuiser max_tokens, car il ne sait pas s'arrêter seul).

### Les bugs qu'on a corrigés (et ce qu'ils enseignent)
1. **`NameError: name 'Llama' is not defined`** → on avait oublié l'import.
   Leçon : toute bibliothèque doit être importée avant usage.
2. **`NameError: name 'nb_tokens' is not defined`** → on utilisait une variable
   jamais créée. Leçon : une variable doit être créée avant d'être utilisée.
3. **Chrono mal placé** (il englobait le chargement du modèle) → on mesurait
   5.61 s au lieu de 4.99 s. Leçon : bien définir CE qu'on mesure. Le coût d'une
   requête = la génération seule, pas le chargement (qui n'arrive qu'une fois).

### Résultat observé
- Avec stop : « Paris. » → **2 tokens en 0.25 s**
- Sans stop : 64 tokens en ~3.8-5 s
- → **20× moins de tokens = ~20× moins de temps.** Première relation clé du stage !

---

## Étape 4 — measure.py : lire l'état de la machine (J3)

### Le code
```python
import psutil                                 # le "tableau de bord" du PC
from codecarbon import EmissionsTracker       # le "compteur d'énergie" logiciel

tracker = EmissionsTracker(save_to_file=False, log_level="error")
tracker.start()                               # ⚡ début de la mesure

# ... un calcul à mesurer (boucle lourde ou inférence) ...

emissions = tracker.stop()                    # ⚡ fin → renvoie le CO2 (kg)
energie = tracker.final_emissions_data.energy_consumed   # énergie en kWh

cpu = psutil.cpu_percent(interval=1)          # % CPU (moyenne sur 1 seconde)
freq = psutil.cpu_freq().current              # fréquence CPU en MHz
```

### À savoir
- **psutil** lit l'état : % d'utilisation du CPU, fréquence. Indices de l'effort.
- **CodeCarbon ESTIME** l'énergie (temps CPU × puissance supposée). Ce n'est PAS
  une mesure matérielle → bon pour COMPARER, pas pour un chiffre absolu exact.
- Conversion utile : **Joules = kWh × 3 600 000**.

### Résultat observé
Boucle de 50 millions d'additions → ~0.0000289 kWh ≈ **104 J**.

---

## Étape 5 — Fusionner : mesurer une vraie inférence (J3)

### L'idée
Le chrono ET le compteur d'énergie entourent EXACTEMENT la même chose : la génération.

```python
tracker.start()                  # ⚡
debut = time.perf_counter()      # ⏱️
sortie = modele(prompt, max_tokens=64)     # ← la seule chose mesurée
duree = time.perf_counter() - debut        # ⏱️
tracker.stop()                   # ⚡
```

### Résultat observé (le 1er résultat scientifique du stage !)
| Réponse | Tokens | Durée | Énergie |
|---|---|---|---|
| courte (stop) | 2 | 0.27 s | **18.6 J** |
| longue (sans stop) | 64 | 3.75 s | **102.1 J** |

### Observation fine
32× plus de tokens mais seulement ~5.5× plus d'énergie →
**énergie ≈ coût fixe + (coût par token × nb tokens)**.
Toute requête a un coût de départ incompressible.

---

## Étape 6 — campaign.py : automatiser et enregistrer (J3)

### Les concepts nouveaux
- **Boucle `for`** : répéter le même traitement pour chaque question d'une liste.
- **Boucles imbriquées** : pour chaque question (externe) × N répétitions (interne).
- **`liste.append(fiche)`** : accumuler les résultats (chaque fiche = 1 dictionnaire).
- **pandas** : `pd.DataFrame(resultats).to_csv(...)` → transforme la liste en CSV.

### La structure finale du script
```
charger le modèle (1 seule fois)
inférence de chauffe (résultat jeté)          ← warm-up
pour chaque prompt :
    pour run de 1 à N_REPETITIONS :
        mesurer (énergie + chrono + tokens)
        ranger la fiche dans la liste
écrire la liste dans data/raw/resultats.csv
```

### Pourquoi le warm-up ?
1ère mesure observée : **303.8 J** vs ~98 J pour les suivantes (×3 !).
Le CPU « froid » fausse la 1ère mesure → on lance une requête bidon AVANT
de mesurer, et on jette son résultat. (Comme un sportif qui s'échauffe.)

### Pourquoi les répétitions ?
Mesures observées pour LA MÊME requête : 88.6 J, 137.4 J, **364.7 J** (×4 !).
C'est du « bruit » : le PC fait d'autres choses en arrière-plan.
→ Une mesure unique MENT. On répète N fois et on prendra la MOYENNE.

### Autre observation
Le nombre de tokens varie d'un run à l'autre (14 vs 64) : le modèle a du
hasard (paramètre température). Piste : température=0 pour des runs identiques
→ à trancher dans le protocole expérimental.

---

## Étape 7 — Partage GitHub (J3)

```bash
git add -A            # 1. préparer tous les changements
git commit -m "..."   # 2. créer le point de sauvegarde
git push origin main  # 3. envoyer sur GitHub
```
Amine récupère avec : `git pull origin main`.

⚠️ Le modèle .gguf et le CSV ne sont PAS dans git (.gitignore) →
chacun télécharge son modèle localement.

---

## Étape 8 — La méthodologie de mesure pour le Pi (décidée, pas encore codée)

Le Pi 5 n'a pas de RAPL → on croisera **3 méthodes EN MÊME TEMPS** :

| # | Méthode | Type | Rôle |
|---|---|---|---|
| 1 | **CodeCarbon** | logicielle (estimation) | mesure en masse, par requête, automatique |
| 2 | **Prise connectée** | physique, au mur | vérité terrain. Lente → mesurer par PAQUETS de requêtes puis diviser. Inclut les pertes du chargeur (~10-15%) → à préciser dans le rapport. Soustraire la conso au repos. |
| 3 | **PMIC du Pi 5** | capteur matériel interne | `vcgencmd pmic_read_adc` → tension × courant = puissance de la carte. Plus précis que la prise, n'existe QUE sur le Pi. |

**Effet observateur** (question qu'on s'est posée) : CodeCarbon/PMIC tournent sur
le Pi → petit surcoût CPU vu par la prise. Négligeable car le LLM sature le CPU.
Bonus rapport : le quantifier (mesurer repos seul vs repos + CodeCarbon).

---

## Où on en est / la suite

```
✅ S1 : machinerie complète sur PC (prévu 1 semaine, fait en 2 jours)
✅ S2.1 : warm-up        ✅ S2.2 : répétitions
🔄 S2.4 : état de l'art  🔄 S2.5 : protocole expérimental
🔄 Pi : installation en cours (Amine)
⬜ Campagne réelle sur Pi (3 mesures en parallèle)
⬜ Analyse + interface Streamlit
⬜ Rapport final
```

### Les fichiers du projet
| Fichier | Rôle |
|---|---|
| `src/campaign.py` | **LE script principal** (celui qui évolue et partira sur le Pi) |
| `src/inference.py` | brique d'apprentissage : 1 requête mesurée |
| `src/measure.py` | brique d'apprentissage : psutil + CodeCarbon |
| `data/raw/resultats.csv` | les mesures (régénéré à chaque campagne) |
| `docs/roadmap.md` | le plan des 6 semaines + méthodologie |
| `docs/journal.md` | le suivi jour par jour |
| `docs/reprise-session.md` | le point d'étape pour reprendre avec Claude |
| `docs/presentation-point1.html` | la présentation du point d'avancement #1 |
