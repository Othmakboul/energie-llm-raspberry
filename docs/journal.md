# Journal de bord

Notez ici au fil de l'eau : ce qui a été fait, les décisions, les problèmes
rencontrés et leurs solutions. Ce journal servira de base au rapport final.

---

## Semaine 1

### Jour 1
- Lecture du sujet, mise en place du dépôt.
- Répartition : Othmane → ... / Amine → ...
- TODO : lire [2][3][13], installer llama.cpp.

### Jour 2 — 08/06/2026
- Projet déplacé sur D: (manque de place sur C:).
- venv créé + dépendances installées.
- Dépôt GitHub en place, .gitignore OK.
- TODO : télécharger un modèle .gguf et tester l'inférence.

### Jour 3 — 09/06/2026
- Compris les bases (token, inférence, quantification, énergie).
- Modèle téléchargé : Llama-3.2-1B-Instruct-Q4_K_M.gguf dans models/.
- Réécrit inference.py de zéro : charge le modèle, pose une question,
  mesure durée + nb de tokens, arrêt propre avec stop=["\n"].
- Observation : moins de tokens = moins de temps (64 tok/5s → 2 tok/0.25s).
- Ecrit measure.py : psutil (CPU %, frequence) + CodeCarbon (energie estimee).
- Test OK sur un faux calcul : ~0.0000289 kWh (~104 J).
- Etape 3 : mesure (chrono + CodeCarbon) branchee autour de la vraie inference.
- 1er resultat : reponse courte 2 tok = 18.6 J ; reponse longue 64 tok = 102.1 J.
- Observation : energie non proportionnelle = cout fixe + cout par token.
- Etape 4 : campaign.py boucle sur plusieurs prompts -> CSV dans data/raw/resultats.csv.
- Observation : 1ere inference plus lente (effet "warm-up") -> a jeter dans les mesures.
- => Machinerie complete fonctionnelle sur PC (objectif Semaine 1 atteint).
- TODO : faire varier les parametres (taille prompt, max_tokens, quantif, modeles) ;
  ajouter une inference de chauffe + repetitions ; preparer le passage sur le Pi.

#### Jour 3 — 09/06/2026 (Amine — outils de mesure / PMIC)
- Etat de l'art outils de mesure redige : `docs/etat_art_outils_mesure.md`. Insight cle :
  **RAPL = x86 only** -> inutilisable sur ARM ; la vraie mesure vient du HW.
- Architecture/protocole de mesure redige : `docs/architecture_mesure.md` (les 3 methodes,
  schema CSV, variables, protocole).
- **Decision materiel** : on part sur une **prise connectee** (au mur) au lieu d'un wattmetre
  USB-C -> pas d'achat specifique. Lecture par script requise.
- **1re mesure reelle sur le Pi 5** via `vcgencmd pmic_read_adc` (idle vs charge 4 coeurs) :
  - VDD_CORE (CPU) : **0,39 W -> 3,27 W** (tension 0,750 -> 0,890 V = DVFS).
  - Total onboard : **~1,55 W -> ~4,51 W** (delta CPU ~+3 W).
  - Confirme : `EXT5V` a une tension mais **pas de courant** -> le PMIC ne voit pas le 5 V
    -> besoin de la prise pour le total systeme.
- **Methodo binome** : le PMIC = 3e methode de mesure (onboard reelle), ajoutee a la roadmap
  a cote de CodeCarbon + prise -> triangulation a confronter dans le rapport.
- TODO : construire le harness PMIC en Python, puis le brancher dans campaign.py.

### Jour 4 — 11/06/2026
- Point d'avancement #1 avec les tuteurs : PASSE avec succes.
- Presente : chaine de mesure complete, 1ers resultats (19 J vs 100 J),
  pieges identifies (warm-up, bruit, hasard), methodo 3 mesures pour le Pi.
- Pi : installation en cours cote Amine.
- Retours tuteurs : (1) utiliser un DATASET de prompts dedie/standard plutot que
  des questions inventees ; (2) justifier scientifiquement le choix moyenne vs
  mediane en s'appuyant sur des articles de methodologie de benchmark.

#### Jour 4 — 11/06/2026 (Amine — prise connectee)
- **Materiel prise connectee identifie (fourni par le labo)** : prise **Aeotec Smart Switch 7
  (ZW175-C16)** + cle USB controleur **Aeotec Z-Stick 7 (ZWA010-C)**. Protocole = **Z-Wave**
  -> lecture par script via la pile **Z-Wave JS** (zwave-js-ui ou zwave-js-server + client Python).
- ⚠️ **Limite identifiee : precision ~±3 W** sur la puissance instantanee — enorme face au Pi (2–8 W).
- **Decision** : on ne se fie pas au W instantane -> **benchmarks longs** : repeter la meme requete
  ×N sur plusieurs minutes, lire le **compteur d'energie cumule (kWh)** de la prise, soustraire le
  repos, diviser par N. L'erreur ±3 W se moyenne ; le kWh cumule est la valeur fiable.
- TODO : inclure la prise dans le harness (timestamps debut/fin + releve kWh).

### Jour 5 — 12/06/2026
- Recherche bibliographique (datasets + stats) -> docs/recherche-datasets-stats.md.
  Conclusions : dataset Alpaca (standard des etudes d'energie) ; mediane+IQR pour
  comparer, moyenne+ecart-type pour les couts ; refs Georges 2007, Hoefler 2015.
- build_prompts.py : echantillon de 45 prompts Alpaca, stratifie par longueur
  (percentiles extremes 10%), graine fixe (seed=42) -> prompts/prompts.json.
- campaign.py branche sur prompts.json (+ colonnes classe et n_caracteres au CSV).
- 1ere campagne complete : 135 mesures (45 prompts x 3 reps).
  Resultats : court 85.8 J / moyen 78.0 J / long 78.8 J (medianes) -> PAS d'effet
  visible de la taille du prompt. Coherent avec la litterature : les tokens de
  SORTIE dominent l'energie (sortie fixee a 64 tokens -> energie ~identique).
- Demonstration mediane vs moyenne sur nos donnees : outlier a 322 J tire la
  moyenne (91.2 J) mais pas la mediane (78.8 J).
- Campagne #2 (echantillon contraste x15, 23-433 caracteres) : effet taille du
  prompt toujours nul (~79 J partout) -> resultat replique 2 fois.
- Campagne #3 (axe max_tokens 16/64/256, 405 mesures, CSV horodate) :
  * energie mediane : 26 J / 72 J / 254 J -> quasi LINEAIRE en tokens generes
  * correlation tokens<->joules : r = 0.99 (litterature GPU : 0.95)
  * cout fixe visible : 1.65 J/token a 16 tok vs 1.02 J/token a 256 tok
    -> modele : E = cout fixe (~10 J) + ~1.0 J par token (sur PC)
  * effet classe a 256 tokens : court 254.8 = long 254.8 J -> 3e replication
- Graphique genere : data/energie_vs_tokens.png
- CONCLUSION JOUR 5 : le nombre de tokens GENERES est LE facteur dominant de
  l'energie ; la taille du prompt est negligeable (<= ~430 car.) ; modele lineaire.

#### Jour 5 — 12/06/2026 (Amine — mise en route du Pi pour l'inference)
- VS Code installe sur le Pi (`apt install code`), repo clone, venv + codecarbon/psutil/pandas.
- Piege n°1 : numpy plantait (`libopenblas.so.0` manquant) -> `apt install libopenblas0`.
- **Piege n°2 (important)** : la compilation de `llama-cpp-python` echouait. Diagnostic via le nom
  du compilateur (`arm-linux-gnueabihf-g++` = 32 bits) : **l'OS flashe etait Raspberry Pi OS 32 bits**.
  Attention, `uname -m` repond `aarch64` (noyau 64 bits) meme sur l'OS 32 bits -> le bon test
  est `dpkg --print-architecture` (armhf = 32, arm64 = 64). Confirme : armhf.
- Consequences du 32 bits : llama.cpp casse/lent (optimise aarch64), max ~3 Go RAM/processus
  (16 Go inutilisables), mesures indefendables -> **decision : reflash en Raspberry Pi OS 64-bit
  AVANT toute mesure** (aucune campagne Pi encore faite, c'est le bon moment).
- Lecon methodo pour le rapport : valider l'architecture de l'OS fait partie du setup reproductible.

## Semaine 2

### Jour 6 — 15/06/2026 (Amine — reflash 64-bit + remise en route)
- **Reflash effectue** : microSD reformatee + **Raspberry Pi OS 64-bit** (version standard, avec bureau)
  ecrit proprement via **Raspberry Pi Imager** (et non plus une copie d'archive). Pi 5 redemarre OK
  sur ecran+clavier+souris.
- Verifications post-reflash : OS 64-bit confirme, ~16 Go de RAM visibles, 4 coeurs. Systeme mis a jour
  (`apt full-upgrade`).
- Point methodo (a citer) : le projet utilise **`llama-cpp-python`** (binding Python, cf. requirements.txt),
  pas un binaire llama.cpp compile a la main -> sur le 64-bit, `pip install llama-cpp-python` doit passer
  (l'echec du 12/06 venait du 32 bits).
- **Reintegration du repo** : recupere la derniere version d'Othmane (campaign.py multi-modeles,
  dataset Alpaca, temperature=0) comme base, puis re-pose la partie mesure (Amine) par-dessus :
  `src/pmic.py` + injection du PMIC dans `campaign.py` (colonnes `joules_pmic`, `joules_pmic_cpu`,
  `w_moyen_pmic`) + docs mesure (architecture, etat de l'art, points d'avancement, questions tuteurs).
- TODO J7 : sur le Pi reflashe -> `git clone` + venv + `pip install -r requirements.txt`
  (verifier la compilation de llama-cpp-python en 64-bit), re-telecharger les .gguf, lancer une 1re
  campagne triangulee (PMIC reel), monter la pile Z-Wave pour la prise.

