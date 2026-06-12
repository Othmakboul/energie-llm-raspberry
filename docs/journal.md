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

### Jour 4 — 11/06/2026
- Point d'avancement #1 avec les tuteurs : PASSE avec succes.
- Presente : chaine de mesure complete, 1ers resultats (19 J vs 100 J),
  pieges identifies (warm-up, bruit, hasard), methodo 3 mesures pour le Pi.
- Pi : installation en cours cote Amine.
- Retours tuteurs : (1) utiliser un DATASET de prompts dedie/standard plutot que
  des questions inventees ; (2) justifier scientifiquement le choix moyenne vs
  mediane en s'appuyant sur des articles de methodologie de benchmark.

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

