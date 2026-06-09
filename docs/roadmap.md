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
| S2-S3 | Passage sur le Raspberry Pi | Pi installe, projet clone, modele, prise branchee | a venir |
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
- 3.1 Installer Raspberry Pi OS (carte SD), demarrer, se connecter.
- 3.2 git clone du depot GitHub.
- 3.3 venv + dependances (ATTENTION : llama-cpp-python sur ARM = etape delicate).
- 3.4 Re-telecharger le(s) modele(s) .gguf dans models/.
- 3.5 1er test + brancher la prise + mesurer la conso AU REPOS (ligne de base).

### S4 — Grande campagne de mesures
- 4.1 Telecharger plusieurs modeles (Q2/Q4/Q8, tailles 1B/3B/7B).
- 4.2 Etendre campaign.py : boucle sur toutes les combinaisons.
- 4.3 Lancer la campagne (tourne plusieurs heures).
- 4.4 Verifier la qualite des donnees (pas d'aberrations).

---

## Methodologie de mesure de l'energie (IMPORTANT)

Le Pi n'a pas de compteur materiel (pas de RAPL) -> deux methodes en PARALLELE :

### Methode logicielle (dans le code) — CodeCarbon
- Integre a campaign.py, estime l'energie a chaque requete, ecrit dans le CSV.
- Automatique, par requete. MAIS : c'est une estimation (approximative sur le Pi).

### Methode physique (hors code) — prise connectee
- Mesure la vraie electricite au mur. Reelle, mais :
  - mesure AU MUR -> inclut les pertes du chargeur USB-C (chiffre un peu plus eleve).
  - LENTE (rafraichit toutes les quelques secondes) -> ne peut PAS mesurer une
    requete courte seule. Solution : repeter la meme requete des centaines de fois
    pendant plusieurs minutes, puis : energie/requete = energie totale / nb requetes.
  - soustraire la conso AU REPOS pour isoler le surcout de l'inference.

### Les deux en MEME TEMPS = comparaison equitable
- On lance campaign.py UNE fois : CodeCarbon estime ET la prise mesure, en parallele.
- But : valider l'estimation logicielle avec la mesure physique (calculer l'ecart).

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