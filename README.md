# Analyse énergétique d'un LLM embarqué sur Raspberry Pi

Mesure et analyse de la consommation énergétique de requêtes (prompts) sur un
modèle de langage léger déployé sur Raspberry Pi 5, en fonction des paramètres
d'inférence (taille du prompt, tokens générés, quantification, n_threads, n_ctx).

> Stage de Master, LISTIC (USMB / Polytech Annecy) — 6 semaines.

## Problématique

Comment caractériser et comparer le coût énergétique d'une requête sur un LLM
embarqué, et quels paramètres d'inférence influencent le plus cette consommation
dans un environnement contraint ?

## Approche

Le Raspberry Pi ne dispose pas de compteur énergétique matériel (pas de RAPL).
La consommation est donc mesurée/estimée par 3 méthodes en parallèle :
- **CodeCarbon** — estimation logicielle (TDP).
- **PMIC onboard** — mesure réelle par composant (`vcgencmd pmic_read_adc`).
- **Prise connectée** — mesure réelle au mur (référence système total).

Détail complet du protocole : `docs/architecture_mesure.md`.
Justification des outils retenus/écartés : `docs/etat_art_outils_mesure.md`.
Résultats interprétés et comparaison à la littérature : `docs/etat_de_lart.md`.

## Structure du dépôt

```
docs/        Protocole, état de l'art, roadmap, tuto Raspberry Pi
src/         Scripts : inférence, mesure, campagnes, analyse, dashboard
prompts/     Échantillon de prompts figé (prompts.json)
models/      Modèles .gguf (non versionnés, à télécharger)
data/        Mesures CSV (versionnées) + données brutes (non versionnées)
figures/     Graphiques générés par les scripts d'analyse (non versionnés, régénérables)
```

## Démarrage rapide

### 1. Environnement

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate   |   Linux/Pi : source .venv/bin/activate
pip install -r requirements.txt
```

Sur Raspberry Pi, l'installation complète (OS, dépendances, `llama-cpp-python`,
modèles, prise connectée) est détaillée dans `docs/tutoriel_raspberry.md`.

### 2. Modèles

Télécharger les modèles `.gguf` (Llama-3.2-1B, Qwen2.5-1.5B, Gemma-3-1B, en
plusieurs quantifications) dans `models/`. Sources et détails : `docs/tutoriel_raspberry.md`.

### 3. Prise connectée (méthode 3)

Appairage et configuration de la prise Z-Wave : `docs/prise_zwave_setup.md`.

### 4. Échantillon de prompts (une seule fois)

```bash
python src/build_prompts.py
```
Construit `prompts/prompts.json` à partir du dataset Alpaca (tirage figé,
reproductible — voir `docs/recherche-datasets-stats.md` pour la méthode).

### 5. Campagnes de mesure

Chaque script couvre une question expérimentale, écrit son CSV dans `data/raw/` :

| Script | Question | Sortie |
|---|---|---|
| `src/campaign.py` | Campagne principale : modèle x quantification x max_tokens (+ n_threads) | `resultats_<machine>_<date>.csv` |
| `src/campaign_nctx.py` | Effet de n_ctx (contexte alloué) | `nctx_<machine>_<date>.csv` |
| `src/campaign_nthreads.py` | Effet de n_threads (nb de cœurs) | `nthreads_<machine>_<date>.csv` |
| `src/campaign_prompt_size.py` | Effet de la taille du prompt (entrée) | `prompt_size_<machine>_<date>.csv` |
| `src/campaign_prompt_length_nctx.py` | Taille du prompt croisée avec n_ctx | `prompt_length_nctx_<machine>_<date>.csv` |

Réglages (modèles testés, n_threads, n_ctx, répétitions...) en tête de chaque
script — à vérifier avant de lancer. `src/inference.py` et `src/measure.py`
sont des briques d'apprentissage isolées (1 requête / 1 mesure), pas des
campagnes.

### 6. Analyse

| Script | Sur quelles données | Sortie |
|---|---|---|
| `src/analyze_pi5.py` | Campagne principale | Résumé chiffré en console |
| `src/visualize_pi5.py` | Campagne principale | PNG dans `data/` |
| `src/analyse_nctx.py` | Campagne n_ctx | PNG dans `figures/nctx/` |
| `src/analyse_nthreads_v2.py` | Campagne n_threads (données corrigées) | PNG dans `figures/nthreads_v2/` |
| `src/analyse_prompt_length_nctx.py` | Campagne prompt x n_ctx | PNG dans `figures/prompt_length_nctx/` |

### 7. Dashboard interactif

```bash
streamlit run src/dashboard.py
```
Interface Streamlit, 6 modes de navigation (impact n_threads, n_ctx, taille de
prompt, vue globale modèle/quantification, comparaison des 3 méthodes de
mesure, sensibilisation). Lit directement les CSV de `data/raw/`.

## Documentation

- `docs/roadmap.md` — avancement semaine par semaine.
- `docs/architecture_mesure.md` — protocole de mesure (les 3 méthodes, schéma, dataset).
- `docs/etat_art_outils_mesure.md` — outils de mesure d'énergie évalués, décision retenue.
- `docs/etat_de_lart.md` — synthèse bibliographique et résultats interprétés.
- `docs/recherche-datasets-stats.md` — choix du dataset de prompts et des statistiques.
- `docs/prise_zwave_setup.md` — installation et configuration de la prise connectée.
- `docs/tutoriel_raspberry.md` — installation complète du Raspberry Pi.

## Équipe

- Othmane — modèles légers.
- Amine — outils de mesure (software + hardware).

Labo LISTIC (USMB / Polytech Annecy), tuteur Stéphane Plassart.
