# Recherche : datasets de prompts & statistiques (moyenne vs médiane)

> Réponse aux deux demandes des tuteurs (11/06/2026) :
> (a) quel dataset de prompts utiliser ; (b) moyenne ou médiane, combien de répétitions.
> Sources : 6 articles arXiv (sources primaires) lus par recherche automatisée.
> ⚠️ Infos extraites des articles mais à RE-VÉRIFIER lors de notre lecture
> (la passe de vérification croisée a été interrompue par une limite de session).

---

## (a) Quels datasets de prompts utilisent les études d'énergie LLM ?

### Ce qu'on observe dans la littérature : 3 approches

| Approche | Qui le fait | Exemple |
|---|---|---|
| **Datasets d'instructions** (questions/consignes réalistes) | MELODI (arXiv 2407.16893), TokenPowerBench (arXiv 2512.03024) | **Alpaca** (~52 000 prompts) + Code-Feedback ou LongBench |
| **Benchmarks de tâches académiques** | Étude énergie LLM quantifiés sur Pi 4 (arXiv 2504.03360) ; NAACL 2025 (arXiv 2502.05610) | CommonsenseQA, BIG-Bench Hard, TruthfulQA, GSM8K, HumanEval / GLUE, SQuAD, CNN-DM |
| **Prompts contrôlés / faits main** | Notre réf. [13] (arXiv 2511.07425) ; grande étude GPU (arXiv 2511.05597) | 3 prompts écrits à la main de longueurs différentes / grille contrôlée de tailles d'entrée-sortie |

### Comment ils échantillonnent
- arXiv 2504.03360 : **200 prompts par benchmark**, tirage aléatoire uniforme (+ HumanEval complet : 164).
- arXiv 2502.05610 (NAACL 2025) : **1024 prompts par dataset**, tirés une fois puis **réutilisés à l'identique** dans toutes les configs.
- TokenPowerBench (arXiv 2512.03024) : stratifie les résultats **par classes de longueur** (0–2K, 2K–5K, 5K–10K tokens).
- arXiv 2511.05597 : grille contrôlée entrée×sortie, plafonnée à 1000 tokens (les datasets publics dépassent rarement 1000 tokens).
- Notre réf. [13] (arXiv 2511.07425) : seulement **3 prompts faits main, 4 répétitions, moyenne simple** — preuve que même des études publiées ont une méthodo légère ; on peut faire mieux.

### Résultat scientifique clé (répété dans plusieurs articles)
- **C'est la LONGUEUR DE SORTIE (tokens générés) qui domine l'énergie, pas le prompt** :
  - MELODI : corrélation réponse↔énergie **r = 0.846** ; complexité du prompt : corrélations faibles (~0.1).
  - NAACL 2025 : énergie ≈ linéaire en tokens d'entrée (r=0.697) ET de sortie (**r=0.952**, pente plus forte).
  - arXiv 2511.05597 : sortie 100 → 900 tokens = énergie **×11**.
- Conséquence pour nous : **contrôler/fixer max_tokens** est crucial ; la taille du prompt est un facteur secondaire (mais à mesurer quand même — c'est dans notre sujet).

### Recommandation pour notre protocole
1. **Dataset principal : Alpaca** (le plus utilisé dans les études d'énergie : MELODI, TokenPowerBench ; citable).
2. **Échantillon stratifié par longueur** : ex. 3 classes (court / moyen / long) × 10-20 prompts, **tirés une fois et figés** (réutilisés à l'identique dans toutes les configurations, comme NAACL 2025).
3. Mentionner que [3] (notre biblio) utilise MMLU/HellaSwag — utile si on veut comparer, mais ce sont des QCM moins représentatifs d'un usage réel.

---

## (b) Moyenne ou médiane ? Répétitions, warm-up, outliers

### Références canoniques (à citer)
- **Georges, Buytaert & Eeckhout (2007)**, *Statistically Rigorous Java Performance Evaluation*, OOPSLA 2007. https://doi.org/10.1145/1297027.1297033
  → LE classique : répétitions multiples, exclusion du warm-up, moyennes avec **intervalles de confiance**, dénonce les conclusions tirées d'une seule mesure.
- **Hoefler & Belli (2015)**, *Scientific Benchmarking of Parallel Computing Systems*, SC'15. https://doi.org/10.1145/2807591.2807644
  → 12 règles du benchmark rigoureux ; recommande **médiane et percentiles** pour les distributions asymétriques (le bruit ne fait qu'AJOUTER du temps/énergie → distribution tirée vers le haut).

### Ce que font les études d'énergie LLM (constat : c'est inégal !)
| Étude | Statistiques utilisées |
|---|---|
| MELODI (2407.16893) | **médiane + IQR** (boîtes à moustaches, whiskers 1.5×IQR) |
| Pi 4 quantifiés (2504.03360) | moyenne ± écart-type (ex. Llama-3.2-1B : 8.40 ± 5.36 J/token — écart-type énorme !), pas de warm-up déclaré |
| Notre réf. [13] (2511.07425) | moyenne simple sur 4 runs, pas de médiane ni IC ni warm-up |
| Grande étude GPU (2511.05597) | pas de répétitions/warm-up/IC déclarés |

→ Beaucoup d'études publiées sont EN-DESSOUS des standards de Georges/Hoefler.
  En suivant ces standards, notre protocole sera plus rigoureux que plusieurs papiers publiés.

### Recommandation pour notre protocole (la réponse aux tuteurs)
1. **Les deux, car ils répondent à des questions différentes** :
   - **Médiane (+ IQR)** pour COMPARER les configurations → robuste aux outliers
     (justification : bruit asymétrique, cf. Hoefler & Belli 2015 ; pratique MELODI).
   - **Moyenne (± écart-type)** pour estimer les COÛTS CUMULÉS
     (1000 requêtes coûtent 1000 × moyenne, pas 1000 × médiane).
2. **Répétitions : 10 par configuration** (minimum 5) — Georges et al. recommandent
   assez de runs pour des intervalles de confiance ; notre propre bruit observé
   (88→364 J, ×4) le justifie.
3. **Warm-up : exclu** (déjà fait dans campaign.py) — conforme à Georges et al. 2007.
4. **Outliers : ne pas les supprimer en douce** ; les montrer (boxplot) et utiliser
   la médiane qui les neutralise. Si exclusion : règle explicite (ex. > 1.5×IQR) et
   documentée.
5. **Toujours rapporter la dispersion** (écart-type ou IQR), jamais un chiffre seul.
6. **Baseline au repos** : mesurer et soustraire la conso du Pi au repos
   (cf. 2504.03360 : baseline 2.85 W soustraite — à mesurer sur NOTRE Pi 5).

---

## Données de calibration utiles (extraites, à confirmer à la lecture)

- Pi 5 : modèles ≤1.5B → 5-15 tok/s ; ~10 W en pic (2511.07425).
- Llama-3.2-1B sur Pi : ~8.4 J/token en moyenne (2504.03360) — notre futur point de comparaison.
- Quantification : FP16 = 17.60 J/token vs q3_K_S = 3.75 J/token (−79 %) sur Llama-3.2-1B (2504.03360)
  → notre axe « quantification » devrait montrer des écarts forts.
- Les plus gros modèles consomment ~100× plus que les petits (MELODI).

## Les 6 sources lues (toutes arXiv, à mettre dans l'état de l'art)

1. arXiv **2504.03360** — énergie de 28 LLM quantifiés sur Raspberry Pi 4, mesure matérielle Joulescope JS110 (2 MHz). https://arxiv.org/abs/2504.03360
2. arXiv **2511.07425** — notre réf. [13] : 25 LLM sur Pi 4/Pi 5/Orange Pi, q4_k_m. https://arxiv.org/abs/2511.07425
3. arXiv **2407.16893** — MELODI / "The Price of Prompting" : profilage énergie par prompt, Alpaca + Code-Feedback. https://arxiv.org/abs/2407.16893
4. arXiv **2502.05610** — NAACL 2025 : énergie d'inférence sur 11 datasets NLP standards, 1024 prompts figés. https://arxiv.org/html/2502.05610v2
5. arXiv **2512.03024** — TokenPowerBench : benchmark puissance/énergie, Alpaca + LongBench, stratification par longueur. https://arxiv.org/html/2512.03024v1
6. arXiv **2511.05597** — 32 500+ mesures par prompt sur GPU datacenter (pas edge) ; sortie 100→900 tokens = ×11. https://arxiv.org/abs/2511.05597

> ⚠️ Rappel : vérifier titres/auteurs exacts sur les pages arXiv au moment de citer.
