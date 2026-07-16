# Roadmap du stage — energie-llm-raspberry

Analyse energetique des requetes d'un LLM embarque sur Raspberry Pi 5 (16 Go).
Objectif : mesurer le cout energetique d'une requete et identifier les parametres
d'inference les plus influents.

> Mise a jour : 2026-07-16 (soutenance le 15 ou 16/07/2026).

---

## Vue d'ensemble (6 semaines)

| Semaine | Phase | Livrable | Statut |
|---|---|---|---|
| S1 | Mise en place + bases | Machinerie sur PC (inference/measure/campaign + CSV) | FAIT |
| S2 | Mesure fiable + etat de l'art | Warm-up, repetitions/moyennes, notes articles | FAIT |
| S2-S3 | Passage sur le Raspberry Pi | Pi installe, projet clone, modele, prise branchee | FAIT (OS 64-bit, llama-cpp-python, 3 modeles, prise Z-Wave operationnelle) |
| S3-S4 | Grande campagne de mesures | Campagnes principales + n_threads + n_ctx + taille de prompt | FAIT (3645 mesures campagne principale + campagnes dediees n_threads/n_ctx/longueur de prompt) |
| S4-S5 | Analyse + visualisation | Interface Streamlit + graphiques | FAIT (`src/dashboard.py`, 6 modes) |
| S5-S6 | Redaction | Rapport final (analyse + recommandations) | en cours (soutenance 15-16/07/2026) |

### Les parametres testes
1. Taille du prompt (court / long, y compris effet croise avec n_ctx)
2. Nombre de tokens generes (max_tokens : 16 / 64 / 256)
3. Niveau de quantification (Q2/Q3/Q4/Q8 selon modele)
4. Parametres d'inference : n_threads (1/2/4), n_ctx
5. Modele/architecture : Llama-3.2-1B, Qwen2.5-1.5B, Gemma-3-1B

### Les 4 livrables attendus
- [x] Scripts de mesure
- [x] Base de donnees experimentale (CSV dans `data/raw/`, campagnes principales + n_threads + n_ctx + prompt_length)
- [x] Interface de visualisation (`src/dashboard.py`, Streamlit)
- [ ] Rapport avec analyse + recommandations (en cours de redaction)

---

## Detail des etapes S1 -> S4

### S1 — Mise en place + bases (FAIT)
- Repo, venv, dependances, .gitignore.
- Bases comprises (token, inference, quantification, energie).
- inference.py : 1 question -> reponse + tokens + duree.
- measure.py : CPU + energie (CodeCarbon).
- campaign.py : boucle sur plusieurs prompts -> CSV (data/raw/resultats.csv).

### S2 — Rendre la mesure fiable + etat de l'art (FAIT)
- Inference de chauffe (warm-up) : 1ere requete jetee (CPU froid -> mesure faussee).
- Repetitions de chaque mesure + moyenne/mediane (reduire le bruit) — voir `recherche-datasets-stats.md`.
- Etat de l'art : references [2] LLMPi, [3] energie SLM, [13] benchmark SBC et suite — voir `etat_de_lart.md`.
- Protocole experimental ecrit — voir `architecture_mesure.md`.

### S3 — Passage sur le Raspberry Pi (FAIT)
- Raspberry Pi OS 64-bit installe et verifie (`dpkg --print-architecture`).
- Repo clone sur le Pi, venv + dependances installees (llama-cpp-python compile sur ARM).
- 3 modeles `.gguf` telecharges dans `models/` (Llama-3.2-1B, Qwen2.5-1.5B, Gemma-3-1B).
- Prise connectee Z-Wave (Aeotec ZW175-C16) appairee et lue par script — voir `prise_zwave_setup.md`.
- Baseline au repos mesuree (PMIC + prise).

### S4 — Grande campagne de mesures (FAIT)
- Campagne principale : 3 modeles x plusieurs quantifications x max_tokens, 3645 mesures.
- Campagne n_threads (1/2/4 coeurs) : optimum energetique moyen a 2 threads.
- Campagne n_ctx : pas d'effet mesurable sur l'energie a longueur de prompt fixee.
- Campagne taille de prompt (seule + croisee avec n_ctx) : loi quadratique E(input_tokens).
- Donnees verifiees, resultats interpretes — voir `etat_de_lart.md` §5.

---

## Methodologie de mesure de l'energie

Triangulation a 3 methodes (CodeCarbon logiciel, PMIC onboard, prise connectee au mur) —
detail complet du protocole, du schema et du statut de chaque methode dans
`architecture_mesure.md`. Justification des outils ecartes/retenus dans `etat_art_outils_mesure.md`.

---

## Pieges connus
- Windows : llama-cpp-python ne compile pas (Long Path) -> wheel pre-compile.
- 1ere inference toujours plus lente (warm-up) -> a jeter.
- Une seule mesure a du bruit -> repeter + moyenner/medianer.
- OS 32 bits sur le Pi (decouvert le 12/06) : Raspberry Pi OS 32 bits (armhf) casse la compilation
  de llama-cpp-python et plafonne la RAM a ~3 Go. Piege : `uname -m` repond `aarch64` (noyau)
  meme en 32 bits -> le bon test est `dpkg --print-architecture` (arm64 = 64 bits, armhf = 32 bits).
  Reflash en Raspberry Pi OS 64-bit fait le 15/06, avant toute campagne.
