# Point d'avancement — stage énergie LLM sur Raspberry Pi 5

> **Document vivant** : mis à jour à chaque point/RDV tuteurs. Sert de support oral et
> de base au rapport. Le détail technique de la mesure est dans
> [`architecture_mesure.md`](architecture_mesure.md) ; l'état de l'art outils dans
> [`etat_art_outils_mesure.md`](etat_art_outils_mesure.md) ; le suivi jour par jour dans
> [`journal.md`](journal.md).

Stage : *Analyse énergétique de requêtes LLM sur Raspberry Pi 5* — LISTIC
Binôme : **Amine** (outils de mesure) · **Othmane** (modèles légers) — Tuteur : S. Plassart
Période : J1 = 08/06 → fin estimée 19/07. **Dernière mise à jour : 15/06/2026.**

---

## 1. Sujet en une phrase

Mesurer **combien d'énergie consomme une requête** envoyée à un LLM léger quantifié qui
tourne sur un **Raspberry Pi 5 (16 Go)**, et comprendre **quels paramètres** font varier
cette consommation (longueur du prompt, tokens générés, quantification, paramètres d'inférence).

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
| S2-S3 — Passage sur le Pi | S2-S3 | 🔄 **En cours** : Pi configuré + PMIC validé 09/06 ; **OS reflashé en 64-bit le 15/06** ; reste install `llama-cpp-python` + modèles + prise |
| S3-S4 — Grande campagne de mesures (le gros CSV) | S3-S4 | ⏳ À venir |
| S4-S5 — Analyse + interface Streamlit | S4-S5 | ⏳ À venir |
| S5-S6 — Rapport final | S5-S6 | ⏳ À venir |

➡️ **Dans les temps**, avec une avance sur la partie matérielle (PMIC déjà validé en vrai).

---

## 4. Réalisations concrètes (mesurées)

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

## 5. Prochaines étapes (S2-S3)

1. Sur le Pi reflashé : `git clone` + venv + `pip install -r requirements.txt` →
   **vérifier que `llama-cpp-python` compile en 64-bit**, re-télécharger les `.gguf`.
2. 1re **campagne triangulée sur le Pi** : `campaign.py` avec PMIC réel + ligne de base au repos.
3. **Monter la pile Z-Wave** (Z-Stick 7 + ZW175) → 1re lecture scriptée du kWh cumulé (benchmark long).
4. Faire varier les 4 paramètres (longueur prompt · max_tokens · quantification · params d'inférence).

---

## 6. Questions / décisions à trancher avec les tuteurs

### 🔴 Bloquants
1. **Réseau labo — Ethernet ne donne pas d'IP au Pi** (MAC probablement à enregistrer) →
   SSH headless impossible, on travaille écran branché. *Demande : enregistrer la MAC / accès dédié.*
2. **Prise connectée** : OK matériel fourni (Aeotec ZW175 + Z-Stick 7, Z-Wave) — reste à valider
   une 1re lecture scriptée (pile Z-Wave JS).

### 🟠 Organisation
3. **Date de soutenance** — toujours pas confirmée. *À fixer pour caler le rétroplanning.*
4. **Périmètre de la campagne** — combien de modèles viser ? Principe de descope :
   **1 modèle bien mesuré > 4 mal mesurés.**

### 🟢 Validation méthodo
5. **Triangulation 3 méthodes** (CodeCarbon vs PMIC vs prise) — valider l'approche et que les
   écarts attendus sont un résultat acceptable.
6. **Limite du PMIC** (ne voit pas le 5 V) — confirmer que PMIC + prise couvre le besoin, ou
   recommandent-ils un INA219/wattmètre USB-C inline en plus ?

### 💡 PFE 2027
7. Objectif de capitalisation (**dataset Hugging Face** + repo reproductible) — leur avis / accord
   pour publier en open-source.
