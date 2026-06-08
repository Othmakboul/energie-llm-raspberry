# État de l'art

Résumés des articles lus en début de stage. Une section par référence.

## Articles prioritaires

### [2] LLMPi — Optimizing LLMs for high-throughput on Raspberry Pi (2025)
- À résumer.

### [3] Characterizing energy footprint of small language models on edges (2025)
- À résumer.

### [13] An evaluation of LLMs inference on popular single-board computers (2025)
- À résumer.

## Outils de mesure énergétique

| Outil | Type | Note |
|-------|------|------|
| CodeCarbon [11] | Estimation logicielle | Simple à intégrer en Python |
| Scaphandre [8] | Monitoring | Repose sur RAPL (limité sur Pi) |
| PowerAPI [12] | Framework | |
| Alumet [9] | Framework modulaire | |
| EcoFloc [14] | Multi-composants | |

## À retenir
- Le Raspberry Pi n'expose pas de compteur RAPL → mesure indirecte / estimation [2, 6, 13].
- Quantification = levier principal de réduction du coût (llama.cpp) [3, 15].
