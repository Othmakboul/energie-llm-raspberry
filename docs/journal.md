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

