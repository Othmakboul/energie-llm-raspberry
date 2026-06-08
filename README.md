# Analyse énergétique d'un LLM embarqué sur Raspberry Pi

Mesure et analyse de la consommation énergétique de requêtes (prompts) sur un
modèle de langage léger déployé sur Raspberry Pi, en fonction des paramètres
d'inférence.

> Stage de Master — durée 6 semaines.

## Problématique

Comment caractériser et comparer le coût énergétique d'une requête sur un LLM
embarqué, et quels paramètres d'inférence influencent le plus cette consommation
dans un environnement contraint ?

## Approche

Le Raspberry Pi ne dispose pas de compteur énergétique matériel (pas de RAPL).
La consommation est donc **estimée** à partir :
- de métriques système Linux (charge CPU, fréquence, température, temps),
- d'outils logiciels d'estimation (CodeCarbon, Scaphandre, ...).

Paramètres étudiés : taille du prompt, nombre de tokens générés, niveau de
quantification, paramètres d'inférence.

## Structure du dépôt

```
docs/        État de l'art et journal de bord
src/         Scripts : inférence, mesure, campagnes d'expériences
prompts/     Jeu de prompts standardisé
models/      Modèles .gguf (non versionnés)
data/        Mesures brutes et traitées (non versionnées)
analysis/    Analyse et interface de visualisation
```

## Démarrage rapide

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate   |   Linux/Pi : source .venv/bin/activate
pip install -r requirements.txt
```

## Équipe

- Othmane
- Amine

## Références

Voir `docs/etat_de_lart.md`.
