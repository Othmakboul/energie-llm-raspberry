# Architecture & protocole de mesure — LLM énergie sur Raspberry Pi 5

> Vue d'ensemble des mesures qu'on va faire : les 3 méthodes, ce qu'on collecte,
> les variables à faire varier, le protocole, et l'état de validation.
> Stage LISTIC — partie "outils de mesure" (Amine). **Version 2026-06-09 (v2).**

## Le principe en une phrase
Le **harness Python** (chef d'orchestre) lance une requête sur le **moteur d'inférence**,
lit **en parallèle** la **puissance** (3 méthodes), puis écrit **une ligne par requête**
(énergie + paramètres + tokens) dans un **dataset**, qui alimente la **visualisation** et le **rapport**.

---

## 1. Les 3 méthodes de mesure (triangulation)

Le Pi **n'a pas de RAPL** (compteur matériel x86). On combine donc **3 sources** qui se valident l'une l'autre :

| # | Méthode | Qui | Ce qu'elle mesure | Fréquence | Force / Faiblesse |
|---|---|---|---|---|---|
| 1 | **CodeCarbon** (logiciel) | Othmane (codé) | Énergie **estimée** par le logiciel | par requête | Simple, automatique. **MAIS** sur ARM = estimation par TDP, **pas une vraie mesure** → sert de **repère / comparaison** |
| 2 | **PMIC onboard** `vcgencmd pmic_read_adc` | **Amine** | Puissance **réelle onboard, par composant** (CPU, RAM…) | ~quelques Hz | **Vraie mesure, fine, par rail.** Ne voit **pas le rail 5V d'entrée** → sous-estime le total |
| 3 | **Prise connectée** (physique) | commun | Puissance **réelle au mur** (système total) | lente (~0,1–1 Hz) | **Vérité terrain système.** Inclut les pertes de l'alim PD (surestime "Pi seul") ; trop lente pour une requête courte |

**Pourquoi 3 et pas 1 :** chacune voit une chose différente. PMIC = *« où part l'énergie dans le Pi »*.
Prise = *« combien le système tire en tout »*. CodeCarbon = *« ce que l'estimation logicielle prédit »*.
Les confronter (calculer les écarts) est **un résultat en soi** pour le rapport.

> **État de validation (mesuré le 2026-06-09 sur le Pi 5) :** le PMIC fonctionne.
> Au repos : ≈ **1,55 W** onboard (dont `VDD_CORE`/CPU = 0,39 W). Sous charge CPU (4 cœurs) :
> ≈ **4,51 W** (dont `VDD_CORE` = 3,27 W). On a confirmé en vrai que `EXT5V` donne une
> tension mais **pas de courant** → d'où le besoin de la prise pour le total système.

---

## 2. Schéma global

```
                          ┌──────────────────────────────────────────────┐
                          │              RASPBERRY PI 5 (16 GB)            │
                          │                                                │
   ┌───────────────┐      │   ┌────────────────────────────────────────┐ │
   │ COUCHE 3        │     │   │  COUCHE 2 — HARNESS PYTHON (orchestrateur)│ │
   │ MOTEUR          │     │   │                                          │ │
   │ D'INFÉRENCE     │◄────┼───┤  pour chaque prompt :                    │ │
   │                 │     │   │   1. t0 = horodatage                     │ │
   │ llama.cpp /     │─────┼──►│   2. lance l'inférence (modèle quantifié)│ │
   │ llama-cpp-python│     │   │   3. échantillonne le PMIC en //         │ │
   │ Llama-3.2-1B    │     │   │   4. t1 = horodatage, récupère tokens    │ │
   │  Instruct Q4_K_M│     │   │   5. énergie = ∫ P dt  (Joules)          │ │
   │  → côté Othmane │     │   │   6. écrit 1 ligne dans le dataset       │ │
   └───────────────┘      │   └───────┬───────────────┬──────────────────┘ │
                          │           │ lit           │ lit                 │
                          │           ▼               ▼                     │
                          │   ┌──────────────┐  ┌──────────────────────┐    │
                          │   │ MÉTRIQUES SYS │  │ PMIC (méthode 2)      │   │
                          │   │ • psutil      │  │ • vcgencmd            │   │
                          │   │   CPU% RAM    │  │   pmic_read_adc       │   │
                          │   │ • vcgencmd    │  │   (V×A par rail → W)   │   │
                          │   │   temp/freq/  │  │ + CodeCarbon (méth. 1) │   │
                          │   │   throttling  │  └──────────────────────┘    │
                          │   └──────────────┘                              │
                          └───────────────────┬─────────────────────────────┘
                                              │ alimentation 5V / USB-C
   ┌───────────── COUCHE 1 — MESURE PHYSIQUE (méthode 3) ──────────────────────┐
   │   [Prise murale 230V] ── prise connectée ── alim PD USB-C ──► Pi           │
   │     mesure au mur, conso TOTALE réelle (référence système)                 │
   │     ⚠️ inclut les pertes de l'alim PD ; lente → répéter la requête ×N      │
   └───────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
   ┌──────────────────────────── SORTIES / LIVRABLES ─────────────────────────┐
   │   DATASET (1 ligne = 1 requête)  →  CSV / Parquet                          │
   │     → [VISU Streamlit]   [RAPPORT : comparaison des 3 méthodes]            │
   │     → [PUBLICATION PFE : dataset Hugging Face + repo propre]               │
   └────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Ce qu'on collecte — une ligne par requête (schéma du dataset)

| Colonne | Sens | Source |
|---|---|---|
| `modele` | nom du modèle (ex. Llama-3.2-1B) | inférence |
| `quantif` | niveau (Q2/Q4/Q8) | inférence |
| `prompt_id`, `categorie` | quel prompt, sa taille | prompts.json |
| `prompt_len` | taille du prompt (tokens) | inférence |
| `max_tokens` | budget de génération | paramètre |
| `n_tokens_out` | tokens réellement générés | inférence |
| `temperature`, `n_threads` | paramètres d'inférence | paramètre |
| `duree_s` | durée de la requête | chrono |
| `p_moy_pmic_w` | puissance moyenne PMIC | **PMIC (Amine)** |
| `energie_pmic_j` | énergie = ∫ P·dt | **PMIC (Amine)** |
| `j_par_token` | énergie / nb tokens | calculé |
| `energie_codecarbon_j` | énergie estimée | CodeCarbon |
| `temp_c`, `freq_mhz`, `throttled` | thermique / fréquence | vcgencmd/psutil |
| `cpu_percent` | charge CPU | psutil |
| `run` | n° de répétition | protocole |

> La conso **prise connectée** se mesure séparément (sur un lot de requêtes répétées), puis se
> ramène à l'énergie/requête — voir protocole §5.

---

## 4. Les variables à faire varier (le plan d'expériences)

1. **Taille du prompt** (court / moyen / long).
2. **Nombre de tokens générés** (`max_tokens` : 16 / 64 / 256).
3. **Niveau de quantification** (Q2 / Q4 / Q8 du même modèle).
4. **Paramètres d'inférence** (température, `n_threads`).
5. (+) **Taille du modèle** (1B / 3B / 7B), selon le temps restant.

---

## 5. Protocole expérimental (pour des mesures fiables)

- **Inférence de chauffe (warm-up)** : on jette la 1re requête (CPU froid → mesure faussée).
- **Répétitions** : chaque mesure est répétée **N fois** (ex. N=3) puis **moyennée** (réduit le bruit).
- **Ligne de base au repos** : mesurer le Pi **idle** et **soustraire** pour isoler le surcoût d'inférence.
- **Throttling thermique** : surveiller `temp_c`/`throttled` (avec cooler actif) — une mesure pendant throttling est à écarter.
- **PMIC (méthode 2)** : échantillonner `pmic_read_adc` pendant l'inférence (~5 Hz), puis énergie = ∫ P·dt.
- **Prise (méthode 3)** : trop lente ET imprécise en instantané (**±3 W** sur la ZW175, face à un Pi à 2–8 W)
  pour une requête seule → **benchmarks longs** : répéter la même requête ×N sur plusieurs minutes, lire le
  **compteur d'énergie cumulé (kWh)** de la prise (fiable, contrairement au W instantané),
  puis `énergie/requête = (énergie totale − repos) / nb requêtes`.

---

## 6. Les 3 couches en clair

### Couche 1 — Mesure physique : **prise connectée** (méthode 3)
Mesure au mur, conso système totale. Référence "vérité terrain".
**Matériel (fourni par le labo, identifié le 11/06)** : prise **Aeotec Smart Switch 7 (ZW175-C16)**
+ clé contrôleur USB **Aeotec Z-Stick 7 (ZWA010-C)**. Protocole **Z-Wave** → lecture par script
via la pile **Z-Wave JS** (zwave-js-ui ou zwave-js-server + client Python), clé branchée en USB.
⚠️ Précision instantanée ~**±3 W** (le Pi tire 2–8 W) → on s'appuie sur le **kWh cumulé**
+ benchmarks longs (cf. §5), pas sur le W instantané.

### Couche 2 — Harness Python (piloter + corréler) — *le cœur du livrable d'Amine*
Lance l'inférence, horodate, lit le **PMIC** + métriques système **en parallèle**, calcule
**énergie = ∫ P·dt** et **J/token**, écrit **une ligne par requête**, détecte le throttling.

### Couche 3 — Moteur d'inférence (côté Othmane)
**llama-cpp-python** + modèle **`Llama-3.2-1B-Instruct-Q4_K_M.gguf`** (testé sur PC : 2 tok ≈ 18,6 J, 64 tok ≈ 102,1 J → énergie = coût fixe + coût/token). Fournit tokens/s, temps prompt vs génération.

---

## 7. Démarrable maintenant vs bloqué
- ✅ **Fait (2026-06-09)** : PMIC validé sur le Pi (idle vs charge), Pi 5 configuré.
- ⛔ **Bloqué** : accès **Ethernet du labo** (la prise refuse une IP → MAC à faire enregistrer par Stéphane) → SSH headless en attente. WiFi possible en dépannage.
- ✅ **Obtenu (2026-06-11)** : prise connectée **Aeotec ZW175-C16** + clé **Z-Stick 7 ZWA010-C** → reste à monter la pile Z-Wave JS et valider une 1re lecture scriptée.
- 🤝 **Côté Othmane** : porter `Llama-3.2-1B` sur le Pi (⚠️ `llama-cpp-python` sur ARM = étape délicate).
- ▶️ **Prochain code** : harness PMIC en Python (Bloc 1→5), branché ensuite autour de `modele(prompt, ...)` dans `campaign.py`.
