# Roadmap du stage — energie-llm-raspberry

Analyse energetique des requetes d'un LLM embarque sur Raspberry Pi 5 (16 Go).
Objectif : mesurer le cout energetique d'une requete et identifier les parametres
d'inference les plus influents.

---

## Vue d'ensemble (6 semaines)

| Semaine | Phase | Livrable | Statut |
|---|---|---|---|
| S1 | Mise en place + bases | Machinerie sur PC (inference/measure/campaign + CSV) | FAIT |
| S2 | Mesure fiable + etat de l'art | Warm-up, repetitions/moyennes, notes articles | en cours |
| S2-S3 | Passage sur le Raspberry Pi | Pi installe, projet clone, modele, prise branchee | EN COURS (Pi 5 configure + PMIC valide 09/06 ; OS reflashe en 64-bit le 15/06 ; reste : install llama-cpp-python, modeles, prise Z-Wave) |
| S3-S4 | Grande campagne de mesures | Le gros CSV (4 parametres x modeles) | a venir |
| S4-S5 | Analyse + visualisation | Interface Streamlit + graphiques | a venir |
| S5-S6 | Redaction | Rapport final (analyse + recommandations) | a venir |

### Les 4 parametres a faire varier
1. Taille du prompt (court / long)
2. Nombre de tokens generes (max_tokens : 16 / 64 / 256)
3. Niveau de quantification (Q2 / Q4 / Q8 du meme modele)
4. Parametres d'inference (temperature, n_threads)
(+ le modele : 1B / 3B / 7B)

### Les 4 livrables attendus
- [x] Scripts de mesure
- [ ] Base de donnees experimentale (gros CSV)
- [ ] Interface de visualisation
- [ ] Rapport avec analyse + recommandations

---

## Detail des etapes S1 -> S4

### S1 — Mise en place + bases (FAIT)
- Repo, venv, dependances, .gitignore.
- Bases comprises (token, inference, quantification, energie).
- inference.py : 1 question -> reponse + tokens + duree.
- measure.py : CPU + energie (CodeCarbon).
- campaign.py : boucle sur plusieurs prompts -> CSV (data/raw/resultats.csv).

### S2 — Rendre la mesure fiable + etat de l'art
- 2.1 Inference de chauffe (warm-up) : 1ere requete jetee (CPU froid -> mesure faussee).
- 2.2 Repeter chaque mesure N fois + moyenne (reduire le bruit).
- 2.3 (Optionnel) ranger "charger + mesurer" dans une fonction reutilisable.
- 2.4 Etat de l'art : lire [2] LLMPi, [3] energie SLM, [13] benchmark SBC -> notes.
- 2.5 Ecrire le protocole experimental (valeurs a tester decidees a l'avance).

### S3 — Passage sur le Raspberry Pi (des reception)
- 3.1 Installer Raspberry Pi OS (carte SD), demarrer, se connecter. [x] reflashe 64-bit le 15/06
- 3.2 git clone du depot GitHub. [x] (a refaire sur l'OS reflashe)
- 3.3 venv + dependances (ATTENTION : llama-cpp-python sur ARM = etape delicate ; OK en 64-bit, KO en 32-bit).
- 3.4 Re-telecharger le(s) modele(s) .gguf dans models/.
- 3.5 1er test + brancher la prise + mesurer la conso AU REPOS (ligne de base).

### S4 — Grande campagne de mesures
- 4.1 Telecharger plusieurs modeles (Q2/Q4/Q8, tailles 1B/3B/7B).
- 4.2 Etendre campaign.py : boucle sur toutes les combinaisons.
- 4.3 Lancer la campagne (tourne plusieurs heures).
- 4.4 Verifier la qualite des donnees (pas d'aberrations).

---

## Methodologie de mesure de l'energie (IMPORTANT)

Le Pi n'a pas de compteur materiel (pas de RAPL, c'est une feature x86) -> TROIS methodes
en PARALLELE, qui se valident l'une l'autre (triangulation).
Detail complet cote mesure : voir docs/architecture_mesure.md + docs/etat_art_outils_mesure.md (partie Amine).

### Methode 1 — logicielle (dans le code) — CodeCarbon
- Integre a campaign.py, estime l'energie a chaque requete, ecrit dans le CSV.
- Automatique, par requete. MAIS : sur ARM c'est une ESTIMATION par TDP, pas une vraie mesure.
- On la garde comme REPERE a confronter aux deux mesures reelles ci-dessous.

### Methode 2 — onboard reelle (dans le code) — PMIC `vcgencmd pmic_read_adc`  [partie Amine]
- Lit la puissance REELLE par composant (CPU=VDD_CORE, RAM, etc.) directement sur le Pi 5.
- Echantillonnee pendant l'inference (~5 Hz) -> energie = somme(P x dt) en Joules, et J/token.
  Harness Python = src/pmic.py (context manager `with MesurePMIC():`), branche dans campaign.py.
- Gratuit, deja dispo. Limite : ne voit PAS le rail 5V d'entree -> sous-estime le total
  (d'ou la prise pour le total systeme).
- VALIDE le 09/06 sur le Pi : idle ~1,55 W (CPU 0,39 W), charge ~4,51 W (CPU 3,27 W).

### Methode 3 — physique (hors code) — prise connectee
- Mesure la vraie electricite au mur. Reelle, mais :
  - mesure AU MUR -> inclut les pertes du chargeur USB-C (chiffre un peu plus eleve).
  - LENTE (rafraichit toutes les quelques secondes) -> ne peut PAS mesurer une
    requete courte seule. Solution : repeter la meme requete des centaines de fois
    pendant plusieurs minutes, puis : energie/requete = energie totale / nb requetes.
  - soustraire la conso AU REPOS pour isoler le surcout de l'inference.
- Materiel (fourni labo, 11/06) : prise Aeotec ZW175-C16 + cle Z-Stick 7 (Z-Wave), lue
  par script via la pile Z-Wave JS. Precision instantanee ~±3 W -> on s'appuie sur le kWh cumule.

### Les trois en MEME TEMPS = comparaison equitable
- On lance campaign.py UNE fois : CodeCarbon estime, le PMIC mesure l'onboard, la prise
  mesure le mur -> les trois en parallele sur les memes requetes.
- But : confronter estimation (CodeCarbon) vs onboard reel (PMIC) vs total mur (prise),
  calculer les ecarts. Cette comparaison est un RESULTAT du rapport.

### Effet observateur (a citer dans le rapport)
- La prise ne gene PAS CodeCarbon (materiel externe).
- CodeCarbon tourne sur le Pi -> ajoute un petit surcout CPU vu par la prise,
  mais NEGLIGEABLE car le LLM sature le CPU.
- Bonus : le quantifier (repos seul vs repos + CodeCarbon) et le mentionner.

---

## Pieges connus
- Windows : llama-cpp-python ne compile pas (Long Path) -> wheel pre-compile.
- D:\ refuse la creation de dossiers a la racine -> sous-dossiers existants seulement.
- 1ere inference toujours plus lente (warm-up) -> a jeter.
- Une seule mesure a du bruit -> repeter + moyenner.
- **OS 32 bits sur le Pi (decouvert 12/06)** : Raspberry Pi OS 32 bits (armhf) casse la compilation
  de llama-cpp-python et plafonne la RAM a ~3 Go. PIEGE : `uname -m` repond `aarch64` (noyau)
  meme en 32 bits -> le bon test est `dpkg --print-architecture` (arm64 = 64, armhf = 32).
  -> reflash en Raspberry Pi OS 64-bit fait le 15/06 AVANT toute campagne.