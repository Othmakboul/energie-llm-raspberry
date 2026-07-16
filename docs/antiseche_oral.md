# 🎯 Anti-sèche oral — MA PARTIE : le harness de mesure PMIC

> Le reste (résultats, modèles) = contexte rapide. **Le cœur de mon exposé = §3 le harness.**
> Règle d'or : chaque "ça marche" = un chiffre.

---

## 1. Contexte en 20 s (juste pour situer ma partie)
On mesure l'énergie d'une requête LLM sur Pi 5. Problème : **RAPL** (le compteur d'énergie
des PC Intel/AMD) **n'existe pas sur ARM** → aucun outil logiciel ne donne la vraie puissance
sur le Pi. → **la mesure réelle doit venir du matériel.** C'est exactement ce que fait mon harness.

Triangulation 3 méthodes : CodeCarbon (estimation) · **PMIC onboard (ma brique)** · prise au mur.

---

# 3. 🟢 LE HARNESS PMIC — ma partie (le cœur)

## 3.0 L'idée en une phrase
> Le Pi 5 a une puce d'alimentation, le **PMIC** (Renesas DA9091), qui connaît la **tension et le
> courant de chaque rail interne** (CPU, RAM…). Mon harness l'interroge **pendant l'inférence**,
> et transforme cette suite de **puissances instantanées** en une **énergie en joules**.

**Le point à marteler** : le PMIC ne donne **pas** une énergie. Il donne une **puissance à l'instant t**.
Tout le travail du harness, c'est de **reconstruire l'énergie** à partir de ça.
(`énergie = puissance × temps`, mais la puissance varie → il faut intégrer dans le temps.)

## 3.1 Étape 1 — lire le PMIC une fois (`lire_rails()`)
- La commande `vcgencmd pmic_read_adc` sort une ligne par grandeur, ex :
  `VDD_CORE_A current(15)=0.39A` (courant) et `VDD_CORE_V volt(15)=0.75V` (tension).
- Une **regex** récupère, pour chaque rail, son **courant (A)** et sa **tension (V)**.
- Puissance d'un rail : **P = V × I** (seulement si on a les deux).
- On somme tous les rails → une clé **`TOTAL`** = puissance onboard instantanée.
> Résultat de l'étape : un instantané `{VDD_CORE: 0,29 W, DDR: …, …, TOTAL: 1,5 W}`.

## 3.2 Étape 2 — échantillonner EN PARALLÈLE de l'inférence (classe `MesurePMIC`)
- C'est un **context manager** : on l'utilise avec `with MesurePMIC() as pmic:`.
- À l'entrée du `with`, il lance un **thread de fond** (`daemon`) qui appelle `lire_rails()`
  **5 fois par seconde** et stocke chaque mesure **horodatée** (`time.perf_counter()`).
- Pendant ce temps, le programme principal fait tourner l'inférence **sans être ralenti**.
- À la sortie du `with`, le thread s'arrête et on calcule.
> **Pourquoi un thread ?** Pour mesurer **PENDANT** l'inférence, pas après — et sans bloquer le modèle.
> **Pourquoi un context manager ?** Le `with` garantit que la mesure démarre/s'arrête proprement
> même si l'inférence plante (`__exit__` n'avale pas les exceptions).

## 3.3 Étape 3 — calculer l'énergie : intégration TRAPÈZE (`_calculer()`)
- On a une liste de points (temps, puissance). L'énergie = **aire sous la courbe puissance(temps)**.
- Méthode des trapèzes, entre 2 échantillons consécutifs :
  > **E = Σ (P₁ + P₂)/2 × Δt**
- Sorties calculées :
  - `energie_joules` → énergie **totale onboard** de la requête,
  - `energie_par_rail` → **détail par composant** (dont **VDD_CORE = le CPU seul**),
  - `puissance_moyenne_w` → énergie / durée.
> **Pourquoi trapèze et pas "P moyenne × durée" ?** Le trapèze suit la courbe même si les
> échantillons ne sont pas parfaitement réguliers (jitter du thread) → intégrale plus juste.
> **C'est `energie_par_rail[VDD_CORE]` qui donne le résultat "CPU ≈ 68 % de l'onboard".**

## 3.4 Mode MOCK — développer sans le Pi
- Si `vcgencmd` est absent (sur PC), le module génère de **fausses valeurs plausibles**
  (idle ~1,5 W + bruit). Les chiffres ne veulent rien dire : **c'est juste pour tester la
  plomberie du code** (le `with`, le thread, l'intégration) avant le passage sur le Pi.
- C'est ce qui m'a permis d'écrire et valider tout le harness **avant** d'avoir le Pi opérationnel.

## 3.5 Comment c'est BRANCHÉ dans la campagne (`campaign.py`)
Les 2 méthodes encapsulées sur **exactement la même inférence** → comparables ligne par ligne :
```python
tracker.start()                          # méthode 1 : CodeCarbon (estimation)
with MesurePMIC() as pmic:               # méthode 2 : PMIC (mesure réelle)
    sortie = modele(prompt, max_tokens=..., temperature=0)   # temp=0 → déterministe/reproductible
tracker.stop()
# 1 ligne CSV : joules | joules_pmic | joules_pmic_cpu (VDD_CORE) | w_moyen_pmic
```
> Comme les deux mesurent la MÊME requête EN MÊME TEMPS, l'écart CodeCarbon/PMIC est
> directement comparable → **×1,51 à 16 tok → ×1,04 à 256 tok**.

## 3.6 LES LIMITES (à dire moi-même — ça fait sérieux)
1. **Idle inclus (~1,5 W)** : `E mesurée = inférence + Pi-allumé-pour-rien`. Plus la requête est
   longue, plus l'idle gonfle le total → **biaise la compa entre modèles**.
   Correction : **E_nette = E_mesurée − (P_idle × durée)**. On rapporte le **net**.
   (P_idle mesuré par `python src/pmic.py --duree 60`.)
2. **Le PMIC ne voit pas le rail 5 V** (`EXT5V` a une tension mais pas de courant lu)
   → il **sous-estime le total système** → d'où la **prise au mur** comme 3e méthode.
3. **Échantillonnage à 5 Hz** = ~20-25 points sur une inférence de plusieurs s → assez précis.
   Réglable (`hz=`) : ↑ Hz = plus fin mais l'overhead des `vcgencmd` finit par perturber la mesure ;
   ↓ Hz = trop grossier sur une requête courte (~1 s).

## 3.7 Questions probables du tuteur (et ma réponse)
- *« Pourquoi pas lire directement un compteur d'énergie ? »* → Le PMIC n'a **pas** de registre
  d'énergie, seulement V et I instantanés → c'est à moi d'intégrer.
- *« L'overhead de la mesure ? »* → chaque lecture = un `vcgencmd` ; à 5 Hz c'est négligeable
  devant une inférence de plusieurs secondes ; c'est justement pourquoi je ne monte pas le Hz.
- *« Précision ? »* → onboard fiable et réactive (VDD_CORE suit la charge via DVFS : 0,75→0,89 V) ;
  la limite connue = le 5 V manquant, couvert par la prise.

---

## 2. (si on me pose la question) résultats de la 1re campagne Pi
675 mesures · **~0,43 J/tok stable** · CodeCarbon surestime ×1,51→×1,04 · ~6 W · ~13,9 tok/s.

## 5. (contexte) côté Othmane
Llama-3.2-1B-Q4 · **E ≈ 10 J + ~1,0 J/tok (r=0,99)** · longueur prompt = effet nul → c'est le
**nb de tokens** qui pilote. Ma mesure PMIC retrouve la même structure linéaire (cohérence PC/Pi).

## ✅ Décisions du point (16/06)
MAC enregistrée (SSH OK) · soutenance **15-16/07** · **méthodo validée** ·
périmètre = **max de modèles bien mesurés → composition optimale** (taille × quantif × params).
