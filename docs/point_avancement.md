# Point d'avancement — stage énergie LLM sur Raspberry Pi 5

> **Document vivant** : mis à jour à chaque point/RDV tuteurs. Sert de support oral et
> de base au rapport. Le détail technique de la mesure est dans
> [`architecture_mesure.md`](architecture_mesure.md) ; l'état de l'art outils dans
> [`etat_art_outils_mesure.md`](etat_art_outils_mesure.md) ; le suivi jour par jour dans
> [`journal.md`](journal.md).

Stage : *Analyse énergétique de requêtes LLM sur Raspberry Pi 5* — LISTIC
Binôme : **Amine** (outils de mesure) · **Othmane** (modèles légers) — Tuteur : S. Plassart
Période : J1 = 08/06 → **soutenance 15 ou 16/07/2026**. **Dernière mise à jour : 16/06/2026.**

---

## 1. Sujet en une phrase

Mesurer **combien d'énergie consomme une requête** envoyée à un LLM léger quantifié qui
tourne sur un **Raspberry Pi 5 (16 Go)**, comprendre **quels paramètres** font varier
cette consommation (longueur du prompt, tokens générés, quantification, paramètres d'inférence),
et en déduire la **composition optimale** (taille de modèle × quantification × paramètres
d'inférence) qui **minimise le coût énergétique d'une requête**.

---

## 2. Le point clé scientifique (à expliquer à l'oral)

Sur PC (Intel/AMD) il existe un compteur d'énergie matériel, **RAPL**. **Il n'existe PAS sur
ARM** → aucun outil logiciel classique (Scaphandre, CodeCarbon, PowerAPI…) ne donne la vraie
puissance CPU sur le Pi. **Conséquence qui structure tout le projet : la mesure réelle passe
par le matériel.** D'où une **triangulation à 3 méthodes** (CodeCarbon estimé / PMIC onboard
réel / prise au mur), confrontées sur les mêmes requêtes — la comparaison des écarts est
elle-même un résultat. → détail complet dans `architecture_mesure.md` et `etat_art_outils_mesure.md`.

---

## 3. Où on en est (roadmap)

| Phase | Prévu | Statut |
|---|---|---|
| S1 — Machinerie de mesure sur PC (inference/measure/campaign → CSV) | S1 | ✅ **Fait** |
| S2 — Mesure fiable (warm-up, répétitions) + état de l'art | S2 | ✅ quasi fait |
| S2-S3 — Passage sur le Pi | S2-S3 | ✅ **Fait** : Pi reflashé 64-bit, `llama-cpp-python` compilé, modèle 1B Q4 chargé (~13,9 tok/s), PMIC en mode réel |
| S3-S4 — Grande campagne de mesures (le gros CSV) | S3-S4 | 🔄 **Démarrée** : 1re campagne triangulée sur le Pi le 15/06 (675 mesures) ; reste axes quantification + prise Z-Wave |
| S4-S5 — Analyse + interface Streamlit | S4-S5 | ⏳ À venir |
| S5-S6 — Rapport final | S5-S6 | ⏳ À venir |

➡️ **Dans les temps**, avec une avance : la 1re campagne triangulée tourne déjà **sur le Pi** (pas seulement sur PC).

---

## 4. Réalisations concrètes (mesurées)

**🆕 1re campagne triangulée RÉELLE sur le Pi 5 (15/06) — livrable de la semaine**
- **675 mesures** : 45 prompts Alpaca × max_tokens [16/64/256] × 5 répétitions, sur le Pi 5.
  CSV `resultats_Pi5_2026-06-15_14h45.csv`, colonnes PMIC (`joules_pmic`, `joules_pmic_cpu`,
  `w_moyen_pmic`) remplies en parallèle de CodeCarbon → **triangulation opérationnelle sur le Pi**.
- Résultats (médianes) :

  | Mesure | Valeur |
  |---|---|
  | Énergie par token (PMIC) | **~0,43 J/token, stable** → loi E ∝ tokens confirmée *sur le Pi* |
  | Écart CodeCarbon vs PMIC | **×1,51 à 16 tok → ×1,04 à 256 tok** (CodeCarbon surestime) |
  | Puissance d'inférence | **~6 W** |
  | Part CPU (VDD_CORE) / onboard | **≈ 68 %** |
  | Débit | **~13,9 tok/s** (1B Q4 sur Pi 5) |

  ⚠️ Les joules incluent l'idle (~1,5 W) → **soustraire la ligne de base** ; le PMIC ne voit pas
  le 5 V → la prise donnera un total mur attendu > CodeCarbon. L'**écart entre méthodes est lui-même
  un résultat** pour le rapport.

**Mesure (Amine)**
- État de l'art des outils → **insight clé : RAPL = x86 uniquement**, inutilisable sur ARM/Pi
  (justifie toute la stratégie matérielle). Synthèse dans `etat_art_outils_mesure.md`.
- Architecture de mesure à **3 méthodes en triangulation** (`architecture_mesure.md`).
- **1re mesure réelle sur le Pi 5** via `vcgencmd pmic_read_adc` (idle vs charge 4 cœurs) :

  | | Repos (idle) | En charge (4 cœurs) |
  |---|---|---|
  | **CPU (VDD_CORE)** | 0,39 W | **3,27 W** |
  | **Total onboard** | ~1,55 W | ~4,51 W |

  Tension CPU 0,750 → 0,890 V (= DVFS) : la mesure réagit bien à la charge. Constat confirmé :
  `EXT5V` a une tension mais **pas de courant** → le PMIC ne voit pas le 5 V → prise nécessaire
  pour le total système.
- **Harness PMIC Python** (`src/pmic.py`) écrit + branché dans `campaign.py` (colonnes
  `joules_pmic`, `joules_pmic_cpu`, `w_moyen_pmic`).
- **Setup Pi fiabilisé** : découverte que l'OS flashé était **32 bits** (cassait `llama-cpp-python`,
  RAM plafonnée) → **reflash 64-bit le 15/06**. Leçon : valider l'architecture de l'OS fait
  partie du setup reproductible (`dpkg --print-architecture`, pas `uname -m`).

**Modèles (Othmane)**
- Modèle retenu et testé : **Llama-3.2-1B-Instruct-Q4_K_M**. Loi *coût fixe + coût/token*
  (2 tok ≈ 18,6 J, 64 tok ≈ 102,1 J sur PC).
- Pipeline complet sur PC : `inference.py` / `measure.py` / `campaign.py` (multi-modèles,
  temperature=0) → CSV.
- Dataset **Alpaca** : 45 prompts figés (seed=42), stratifiés par longueur. Campagnes max_tokens
  [16/64/256] → **E ≈ 10 J + ~1,0 J/token (r=0,99)** ; effet taille du prompt nul (répliqué 3×).

---

## 5. Prochaines étapes (S3)

1. **Ligne de base idle** (`python src/pmic.py --duree 60`) à soustraire des joules mesurés.
2. **Axe quantification** : télécharger Q2_K + Q8_0, relancer la campagne → comparer J/token.
3. **Monter la pile Z-Wave** (Z-Stick 7 + ZW175) → 1re lecture scriptée du kWh cumulé (benchmark long) = 3e méthode.
4. Petit **graphe J vs tokens** (PMIC vs CodeCarbon) pour le rapport / l'oral.
5. Compléter les 4 paramètres (longueur prompt · max_tokens · quantification · params d'inférence).

---

## 6. Décisions actées au point du 16/06 ✅

1. ✅ **Réseau labo réglé** — la **MAC du Pi est enregistrée** → SSH headless de nouveau possible
   (plus besoin de l'écran branché en permanence → mesure plus propre).
2. ✅ **Date de soutenance fixée : 15 ou 16/07/2026** → rétroplanning à caler dessus (≈ 4 sem restantes).
3. ✅ **Méthodologie validée** — la **triangulation 3 méthodes** (CodeCarbon vs PMIC vs prise) est
   approuvée ; les écarts entre méthodes sont acceptés comme un résultat.
4. ✅ **Périmètre tranché — viser le MAXIMUM de modèles BIEN mesurés**, pour **trouver la composition
   optimale qui minimise le coût énergétique d'une requête** (taille modèle × quantification ×
   paramètres d'inférence). Le « bien mesurés » reste la contrainte : on n'élargit pas au prix de la rigueur.

### Reste à faire (non bloquant)
- **Prise connectée Z-Wave** (Aeotec ZW175 + Z-Stick 7) : valider une 1re lecture scriptée du kWh cumulé.
- **Limite du PMIC** (ne voit pas le 5 V) : couverte par la prise au mur ; INA219/wattmètre inline en option si besoin de finesse.

### 💡 PFE 2027
- Objectif de capitalisation (**dataset Hugging Face** + repo reproductible) — à confirmer pour publier en open-source.
