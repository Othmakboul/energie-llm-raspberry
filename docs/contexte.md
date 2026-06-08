# Contexte du projet — récapitulatif

> Document de passation à coller en début d'une nouvelle discussion pour donner
> tout le contexte du stage et de l'avancement.

## Le stage

- **Sujet** : Analyse énergétique des requêtes d'un modèle de langage (LLM)
  embarqué sur Raspberry Pi.
- **Durée** : 6 semaines.
- **Équipe** : 2 stagiaires — Othmane et Amine.
- **Matériel** : un Raspberry Pi prêté (modèle à confirmer : Pi 4 ou Pi 5).
- **Niveau** : stage de Master. OS de travail : Windows (Othmane).

## Problématique

Comment caractériser et comparer le coût énergétique d'une requête (prompt) sur
un LLM embarqué, et quels paramètres d'inférence influencent le plus cette
consommation dans un environnement contraint ?

## Concepts clés

- **LLM** : modèle de langage (type ChatGPT/Llama/Mistral).
- **Edge computing / embarqué** : faire tourner l'IA localement sur un petit
  appareil (vs cloud). Avantages : hors-ligne, données privées, faible coût.
  Contrainte : peu de ressources (CPU faible, peu de RAM, pas de GPU).
- **Raspberry Pi** : mini-ordinateur = la plateforme de test (volontairement
  contrainte).
- **Quantification** : compresser le modèle (nombres sur 8 ou 4 bits au lieu de
  32) → plus petit, plus rapide, moins gourmand, légèrement moins précis.
  Paramètre expérimental clé.
- **Prompt / requête** : la question posée au modèle. Originalité du sujet :
  analyser l'énergie À L'ÉCHELLE D'UNE REQUÊTE (peu étudié).

## Difficulté technique centrale

Le Raspberry Pi **n'a pas de compteur énergétique matériel** (pas de RAPL comme
sur les CPU Intel). L'énergie doit donc être **estimée indirectement** via :
- métriques système Linux (charge CPU, fréquence, température, temps),
- outils logiciels (CodeCarbon, Scaphandre, PowerAPI, Alumet, EcoFloc).

## Paramètres à faire varier dans les expériences

1. Taille du prompt.
2. Nombre de tokens générés.
3. Niveau de quantification.
4. Paramètres d'inférence (température, nb de threads, etc.).

## Livrables attendus

1. Environnement fonctionnel sur Raspberry Pi.
2. Scripts de mesure + base de données expérimentale.
3. Interface de visualisation (Python).
4. Rapport avec analyse et recommandations.

## Pile technique choisie

- **Inférence** : `llama.cpp` (modèles `.gguf` quantifiés). Bindings
  `llama-cpp-python` OU binaire `llama.cpp` précompilé (plan B si l'install
  Python coince sur Windows).
- **Mesure** : `CodeCarbon` (estimation énergie) + `psutil` (métriques système).
- **Données** : `pandas`, CSV.
- **Visualisation** : `Streamlit`.

## Articles de référence prioritaires

- **[2]** LLMPi — Optimizing LLMs for high-throughput on Raspberry Pi (2025).
- **[3]** Characterizing energy footprint of small language models on edges (2025).
- **[13]** An evaluation of LLMs inference on single-board computers (2025).
(Liste complète des 15 références dans la proposition de stage d'origine.)

## Répartition envisagée (2 axes parallèles)

- **Axe A — Inférence & modèles** : `llama.cpp`, modèles quantifiés, paramètres
  d'inférence, scripts d'expériences.
- **Axe B — Mesure & data** : outils de mesure, collecte des métriques,
  base de données, interface de visualisation.
- (Répartition exacte à fixer avec Amine.)

## Planning 6 semaines (synthèse)

- **S1** : état de l'art (lire [2][3][13]) + installer la pile sur PC.
- **S2** : Pi opérationnel (OS, SSH) + portage de la pile sur le Pi. **Point
  critique** — si le matériel coince, tout glisse.
- **S3** : pipeline automatisé (inférence + mesure → CSV).
- **S4** : campagne d'expériences (runs, souvent la nuit).
- **S5** : analyse + visualisation (Streamlit).
- **S6** : rédaction du rapport + livrables.

## État d'avancement actuel

- ✅ Dépôt git local initialisé (`energie-llm-raspberry`), premier commit fait.
- ✅ Structure de projet créée (voir `README.md`).
- ✅ Squelettes de scripts reliés entre eux : `src/inference.py`,
  `src/measure.py`, `src/campaign.py`, `analysis/app.py`.
- ✅ Jeu de prompts d'exemple : `prompts/prompts.json`.
- ⬜ Choix plateforme d'hébergement (GitHub recommandé, sauf instance GitLab
  imposée par le labo — à confirmer avec l'encadrant).
- ⬜ Push sur le remote.
- ⬜ Environnement Python créé + dépendances installées.
- ⬜ Modèle `.gguf` téléchargé pour les premiers tests.
- ⬜ Raspberry Pi pas encore reçu.

## Prochaines étapes immédiates

1. Confirmer GitHub vs GitLab (question à l'encadrant).
2. Créer le repo distant, ajouter Amine en collaborateur, push.
3. Créer le venv + `pip install -r requirements.txt`.
4. Télécharger un petit modèle quantifié (1B–3B, Q4) dans `models/`.
5. Tester `src/inference.py` puis une mini-campagne avec `src/campaign.py`.
