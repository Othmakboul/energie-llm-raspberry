# Explication pas à pas — les tout premiers pas du stage (sur PC, avant le Pi)

> Ce document retrace les toutes premières étapes du stage (J1-J3, encore sur PC,
> avant le portage sur Raspberry Pi), avec des explications simples pour quelqu'un
> qui découvre le sujet. Utile pour prendre en main les notions de base et le code
> initial. Pour le protocole final et l'état d'avancement complet, voir
> `architecture_mesure.md` et `roadmap.md`.

---

## Étape 0 — La préparation (J1-J2)

### Ce qui a été fait
1. Créé le dépôt GitHub `energie-llm-raspberry` (code partagé entre Othmane et Amine).
2. Créé un venv (environnement virtuel Python) dans `.venv\`.
3. Installé les bibliothèques : `llama-cpp-python`, `codecarbon`, `psutil`, `pandas`, `streamlit`.
4. Vérifié le `.gitignore` : il exclut de git le venv, les modèles `.gguf` (trop lourds)
   et les données `data/` (propres à chaque machine).

### Pourquoi
- Le venv = une boîte à outils Python propre au projet, isolée du reste du PC.
- Le `.gitignore` = la liste de ce que git ne doit pas envoyer sur GitHub.

### Piège rencontré (Windows)
- `llama-cpp-python` ne compile pas sur Windows (erreur « Long Path »).
  Solution : installer le wheel pré-compilé :
  `pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu`

(Sur Raspberry Pi, le problème est différent : voir `docs/prise_zwave_setup.md` et le tuto
Pi pour l'installation par compilation, plus longue mais sans piège équivalent.)

---

## Étape 1 — Les notions de base (à connaître par cœur)

| Notion | Explication simple |
|---|---|
| LLM | Programme qui a appris à prédire le mot suivant. Il ne « comprend » pas, il calcule des probabilités. |
| Prompt | Le texte qu'on lui donne (la question). |
| Token | Morceau de mot (~3/4 de mot). Le modèle lit et écrit token par token. |
| Inférence | Le moment où le modèle répond. C'est ce qu'on mesure. |
| Paramètres (1B, 3B...) | La taille du « cerveau ». B = milliard. Plus gros = plus malin mais plus lent et gourmand. |
| Quantification (Q2/Q4/Q8) | Arrondir les nombres du modèle pour le compresser (comme un JPEG). Q4_K_M = le standard. |
| GGUF | Le format de fichier d'un modèle quantifié (comme .mp3 pour la musique). |
| llama.cpp | Le « lecteur » qui fait tourner les .gguf sur CPU. `llama-cpp-python` = sa télécommande Python. |
| RAM vs CPU | RAM = plan de travail (16 Go sur le Pi -> pas un souci). CPU = l'ouvrier qui calcule -> c'est lui la limite. |
| Watt / Joule | Watt = puissance instantanée (robinet ouvert). Joule = énergie totale (eau écoulée) = puissance x durée. 1 kWh = 3 600 000 J. |
| RAPL | Compteur d'énergie intégré aux processeurs Intel/AMD. Le Pi n'en a pas -> tout le défi du stage. |

---

## Étape 2 — Télécharger un modèle (J3 matin)

### Ce qui a été fait
Téléchargé `Llama-3.2-1B-Instruct-Q4_K_M.gguf` (770 Mo) depuis Hugging Face
(dépôt `bartowski/Llama-3.2-1B-Instruct-GGUF`) -> posé dans `models/`.

### Pourquoi ce modèle
- 1B = petit -> rapide à tester, et c'est un bon compromis énergie/qualité
  selon la littérature (voir `etat_de_lart.md`).
- Instruct = dressé pour répondre à des questions (pas juste compléter du texte).
- Q4_K_M = la quantification standard utilisée dans les articles de référence -> comparable.

### Comment choisir un modèle (critères)
1. Format `.gguf` (sinon ça ne tourne pas sur llama.cpp).
2. Version Instruct.
3. Taille adaptée à la machine (1B pour commencer).
4. Quantification Q4_K_M par défaut.
5. Famille récente (Llama 3.2, Qwen2.5, Gemma) bien optimisée ARM.

(Suite du stage : les 3 familles Llama-3.2-1B, Qwen2.5-1.5B et Gemma-3-1B ont finalement
été mesurées, en plusieurs niveaux de quantification — voir `etat_de_lart.md` §3.)

---

## Étape 3 — inference.py : faire parler le modèle (J3)

### Le code, ligne par ligne
```python
from llama_cpp import Llama      # importer la classe qui lit les .gguf
import time                       # le chronomètre Python

# 1. Charger le modèle (hors chrono : on mesure la requête, pas le chargement)
mon_modele = Llama(model_path="models/Llama-3.2-1B-Instruct-Q4_K_M.gguf", verbose=False)

# 2. Chrono : départ juste avant la génération
debut = time.perf_counter()

# 3. Poser la question
resultat = mon_modele("Quelle est la capitale de la France ?", max_tokens=64, stop=["\n"])

# 4. Chrono : stop juste après
duree = time.perf_counter() - debut

# 5. Extraire les infos du résultat (un dictionnaire = boîte à étiquettes)
texte = resultat["choices"][0]["text"]
nb_tokens = resultat["usage"]["completion_tokens"]

print(texte)
print(f"{nb_tokens} tokens en {duree:.2f} secondes")
```

### Les paramètres importants
- `max_tokens=64` : nombre maximum de tokens à générer.
- `stop=["\n"]` : s'arrêter au premier retour à la ligne (sinon le modèle
  continue jusqu'à épuiser max_tokens, car il ne sait pas s'arrêter seul).

### Les bugs corrigés (et ce qu'ils enseignent)
1. `NameError: name 'Llama' is not defined` -> import oublié.
   Leçon : toute bibliothèque doit être importée avant usage.
2. `NameError: name 'nb_tokens' is not defined` -> variable jamais créée avant usage.
   Leçon : une variable doit être créée avant d'être utilisée.
3. Chrono mal placé (il englobait le chargement du modèle) -> on mesurait
   5.61 s au lieu de 4.99 s. Leçon : bien définir ce qu'on mesure. Le coût d'une
   requête = la génération seule, pas le chargement (qui n'arrive qu'une fois).

### Résultat observé
- Avec stop : « Paris. » -> 2 tokens en 0.25 s.
- Sans stop : 64 tokens en ~3.8-5 s.
- 20x moins de tokens = ~20x moins de temps. Première relation clé du stage.

---

## Étape 4 — measure.py : lire l'état de la machine (J3)

### Le code
```python
import psutil                                 # le tableau de bord du PC
from codecarbon import EmissionsTracker       # le compteur d'énergie logiciel

tracker = EmissionsTracker(save_to_file=False, log_level="error")
tracker.start()                               # début de la mesure

# ... un calcul à mesurer (boucle lourde ou inférence) ...

emissions = tracker.stop()                    # fin -> renvoie le CO2 (kg)
energie = tracker.final_emissions_data.energy_consumed   # énergie en kWh

cpu = psutil.cpu_percent(interval=1)          # % CPU (moyenne sur 1 seconde)
freq = psutil.cpu_freq().current              # fréquence CPU en MHz
```

### À savoir
- psutil lit l'état : % d'utilisation du CPU, fréquence. Indices de l'effort.
- CodeCarbon estime l'énergie (temps CPU x puissance supposée). Ce n'est pas
  une mesure matérielle -> bon pour comparer, pas pour un chiffre absolu exact.
- Conversion utile : Joules = kWh x 3 600 000.

### Résultat observé
Boucle de 50 millions d'additions -> ~0.0000289 kWh soit environ 104 J.

---

## Étape 5 — Fusionner : mesurer une vraie inférence (J3)

### L'idée
Le chrono et le compteur d'énergie entourent exactement la même chose : la génération.

```python
tracker.start()
debut = time.perf_counter()
sortie = modele(prompt, max_tokens=64)     # <- la seule chose mesurée
duree = time.perf_counter() - debut
tracker.stop()
```

### Résultat observé (premier résultat scientifique du stage)
| Réponse | Tokens | Durée | Énergie |
|---|---|---|---|
| courte (stop) | 2 | 0.27 s | 18.6 J |
| longue (sans stop) | 64 | 3.75 s | 102.1 J |

### Observation fine
32x plus de tokens mais seulement ~5.5x plus d'énergie ->
énergie ≈ coût fixe + (coût par token x nb tokens).
Toute requête a un coût de départ incompressible.

---

## Étape 6 — campaign.py : automatiser et enregistrer (J3)

### Les concepts nouveaux
- Boucle `for` : répéter le même traitement pour chaque question d'une liste.
- Boucles imbriquées : pour chaque question (externe) x N répétitions (interne).
- `liste.append(fiche)` : accumuler les résultats (chaque fiche = 1 dictionnaire).
- pandas : `pd.DataFrame(resultats).to_csv(...)` -> transforme la liste en CSV.

### La structure finale du script
```
charger le modèle (1 seule fois)
inférence de chauffe (résultat jeté)          <- warm-up
pour chaque prompt :
    pour run de 1 à N_REPETITIONS :
        mesurer (énergie + chrono + tokens)
        ranger la fiche dans la liste
écrire la liste dans data/raw/resultats.csv
```

### Pourquoi le warm-up
1re mesure observée : 303.8 J vs ~98 J pour les suivantes (x3).
Le CPU « froid » fausse la 1re mesure -> on lance une requête bidon avant
de mesurer, et on jette son résultat (comme un sportif qui s'échauffe).

### Pourquoi les répétitions
Mesures observées pour la même requête : 88.6 J, 137.4 J, 364.7 J (x4).
C'est du bruit : le PC fait d'autres choses en arrière-plan.
Une mesure unique ment. On répète N fois et on prend la moyenne (ou la médiane
selon le cas — voir `recherche-datasets-stats.md`).

### Autre observation
Le nombre de tokens varie d'un run à l'autre (14 vs 64) : le modèle a du
hasard (paramètre température). Piste explorée ensuite : fixer les paramètres
d'inférence pour des runs comparables — voir le protocole final dans `architecture_mesure.md`.

---

## Étape 7 — Partage GitHub (J3)

```bash
git add -A            # 1. préparer tous les changements
git commit -m "..."   # 2. créer le point de sauvegarde
git push origin main  # 3. envoyer sur GitHub
```
On récupère les changements de l'autre avec : `git pull origin main`.

Le modèle `.gguf` et les CSV ne sont pas dans git (`.gitignore`) ->
chacun télécharge son modèle localement et régénère ses propres données.

---

## Étape 8 — La méthodologie de mesure pour le Pi (décidée à ce stade, pas encore codée)

Le Pi 5 n'a pas de RAPL -> décision de croiser 3 méthodes en même temps (CodeCarbon,
prise connectée, PMIC). Détail complet et statut final de chaque méthode :
voir `architecture_mesure.md` §1 et `etat_art_outils_mesure.md`.

---

## Ce que ce document ne couvre pas

Ce document s'arrête à J3, avant le passage sur Raspberry Pi. La suite du stage
(installation Pi, PMIC, prise Z-Wave, grandes campagnes, dashboard, analyse) est
documentée dans :
- `roadmap.md` — avancement semaine par semaine.
- `architecture_mesure.md` — protocole de mesure final.
- `etat_de_lart.md` — résultats et comparaison à la littérature.
- Tuto Raspberry Pi (`docs/`) — installation complète du Pi et de la prise connectée.

### Fichiers clés du projet
| Fichier | Rôle |
|---|---|
| `src/campaign.py` et variantes (`campaign_nctx.py`, `campaign_nthreads.py`, ...) | scripts de campagne, un par plan d'expérience |
| `src/inference.py` | brique d'apprentissage : 1 requête mesurée |
| `src/measure.py` | brique d'apprentissage : psutil + CodeCarbon |
| `src/pmic.py` | mesure PMIC onboard |
| `src/prise.py` | mesure prise connectée Z-Wave |
| `src/dashboard.py` | interface de visualisation Streamlit |
| `data/raw/*.csv` | les mesures (régénérées par les campagnes) |
| `docs/roadmap.md` | le plan des 6 semaines + avancement |
