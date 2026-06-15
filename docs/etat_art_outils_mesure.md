# État de l'art — Outils de mesure d'énergie pour LLM sur Raspberry Pi 5

> Stage LISTIC — mesure de la conso énergétique de requêtes LLM sur Pi 5.
> Partie **outils de mesure** (Amine). Cible : mesurer l'énergie **par requête** d'un
> LLM léger quantifié, en fonction des paramètres d'inférence (taille prompt, tokens
> générés, quantification, threads…).
> Dernière revue : 2026-06-09.

---

## ⚠️ Le fait qui structure toute la décision

**RAPL (Running Average Power Limit) est une feature Intel/AMD x86 uniquement.**
Elle **n'existe pas sur ARM** → pas de `/sys/class/powercap/intel-rapl` sur le Pi 5.

**Conséquence directe** : tous les outils logiciels qui lisent RAPL (Scaphandre,
CodeCarbon, PowerAPI, pyJoules, CarbonTracker…) ne fournissent **aucune puissance CPU
réelle** sur Raspberry Pi. Sur Pi, ils tombent soit en erreur, soit en *estimation par
TDP* (une constante × le temps), ce qui n'est **pas une mesure**.

➡️ La **mesure réelle** sur Pi vient forcément du **matériel** (wattmètre / INA219) ou
du **PMIC embarqué** du Pi 5. Les outils SW servent surtout à l'état de l'art, au
pilotage de l'expérience, et à la comptabilité CO₂.

---

## A. Outils LOGICIELS basés sur RAPL — ❌ inutilisables pour la puissance CPU sur Pi

| Outil | Langage / nature | Avantages | Inconvénients | Verdict Pi 5 |
|---|---|---|---|---|
| **Scaphandre** | Rust, exporteur de métriques | Très bonne intégration Prometheus/Grafana, par-process, mature | **RAPL only**, ARM sur la roadmap mais **pas implémenté** ; v1.0 ajoute Windows pas ARM | ❌ Pas de mesure réelle |
| **CodeCarbon** | Python, lib | Hyper simple (`@track_emissions`), donne g CO₂, très répandu | Sur Pi : RAPL absent → **fallback "CPU constant mode" = TDP × temps**, donc estimation pas mesure | ⚠️ Utile pour CO₂/repère, pas pour la puissance fine |
| **PowerAPI** | Python, middleware | Power *modeling* fin, par-process, architecture sensor/formula | S'appuie sur RAPL (HWPC sensor) → même mur ARM | ❌ Pas de mesure réelle |
| **pyJoules** | Python, wrapper | Mesure des **bouts de code** très facilement (`with EnergyContext`) | x86 / NVIDIA only (RAPL + nvml) | ❌ |
| **CarbonTracker** | Python | Estime l'empreinte training/inférence ML | Lit RAPL + nvidia-smi → x86/GPU | ❌ |

---

## B. Outils LOGICIELS d'estimation / comptabilité (pas de mesure HW directe)

| Outil | Nature | Avantages | Inconvénients | Verdict |
|---|---|---|---|---|
| **EcoLogits** | Python, estimation | Estime énergie/CO₂ d'appels LLM **via API cloud** (OpenAI/Anthropic) | Ne mesure **aucun** hardware local | 🔸 Hors cible mesure, mais bon **comparatif "cloud vs edge"** pour le rapport |
| **Ecofloc** (2025) | CLI, par-process | Mesure conso **par processus** (CPU/RAM/GPU/réseau) | Dépend de ses backends → **à tester sur ARM**, support incertain | 🟡 À évaluer concrètement sur le Pi |
| **Alumet** (LIG + Eviden, 2025) | Rust, framework modulaire | Archi **sources → transforms → outputs** : on peut brancher une **source custom** (INA219 / PMIC). Next-gen, conçu pour être étendu | Plugin RAPL natif = x86 ; brancher une source custom = **dev à faire** | ⭐ **Piste SW la plus prometteuse** si on veut un pipeline propre |
| **Noureddine review (2013)** | Papier | Revue de référence des méthodes de mesure énergie SW | — | 📚 Background théorique pour le rapport |

---

## C. Outils MATÉRIELS & spécifiques Pi 5 — ✅ la vraie voie de mesure

| Outil | Principe | Avantages | Inconvénients | Verdict |
|---|---|---|---|---|
| **PMIC onboard Pi 5** `vcgencmd pmic_read_adc` | Lecture ADC du PMIC Renesas DA9091 : tensions + courants **par rail** (VDD_CORE, 3V3_SYS, DDR, HDMI…) | **Gratuit, déjà sur le Pi**, scriptable, donne la conso **par composant**, fréquence ~Hz | **Ne mesure PAS le rail 5V d'entrée** → **sous-estime la conso totale** ; écarts constatés vs wattmètre externe ; précision ADC limitée | ✅ **Outil n°1 pour la puissance onboard / par composant**. À calibrer contre une réf externe |
   | **Wattmètre USB-C inline** (UM25C, PD tester…) | Mesure V/I/P réels sur le câble d'alim entre l'alim et le Pi | **Conso système totale réelle**, simple, pas de câblage interne, certains logguent en Bluetooth/USB | Résolution temporelle souvent faible (1 Hz), logging parfois propriétaire ; mesure le tout-Pi (pas par composant) | ✅ **Référence "vérité terrain" système.** ⚠️ **À commander (manque actuel)** |
   | **Capteur INA219 / INA260 (I2C)** | Shunt sur la ligne d'alim, lecture V/I/P scriptable en Python | **Le plus rigoureux** pour de l'inline haute fréquence ; intégration Python directe ; pas cher | Demande **câblage** (shunt sur l'alim) + un peu d'électronique ; INA219 plage de courant à dimensionner | ✅ **Meilleur compromis rigueur/scriptabilité** pour des mesures fines synchronisées au code |
   | **Prise connectée / wattmètre mural** | Mesure au mur (230 V) | Zéro intrusion, ordre de grandeur immédiat | **Inclut les pertes de l'alim PD** → **surestime** la conso "Pi seul" ; basse résolution | 🔸 OK pour un ordre de grandeur, **pas** pour de la mesure fine |

   ---

## Décision retenue pour notre cas (actée 2026-06-09)

**Triangulation à 3 méthodes** (chacune voit une chose différente, on les confronte) :

1. **Mesure fine, par composant** → **PMIC onboard** (`vcgencmd pmic_read_adc`), scripté
   en Python, échantillonné pendant l'inférence. *Gratuit, dispo immédiatement.*
   ✅ **Validé en vrai sur le Pi le 2026-06-09** : idle ≈ 1,55 W (CPU 0,39 W), charge ≈ 4,51 W
   (CPU 3,27 W). Confirmé : `EXT5V` a une tension mais **pas de courant** → sous-estimation du total.
2. **Référence système totale** → **prise connectée** (au mur). Remplace le wattmètre USB-C
   inline (plus simple à obtenir, pas d'achat spécifique). ⚠️ surestime (pertes alim PD) et lente
   → protocole : répéter la requête ×N puis diviser. **L'INA219 reste un plan B** plus rigoureux si
   on veut de l'inline haute fréquence.
3. **Comparaison logicielle** → **CodeCarbon** (déjà codé par Othmane) : on le **garde** non pas
   comme mesure mais comme **estimation à confronter** au PMIC et à la prise (calculer l'écart =
   résultat pour le rapport). **EcoLogits** = comparaison edge vs cloud.
4. **Pipeline SW extensible (bonus PFE)** → creuser **Alumet** avec une source custom PMIC, pas
   prioritaire pour le stage.

**Contrainte sur la prise connectée :** doit être **lisible par script** (API locale type
Tasmota/Shelly, **pas** une prise cloud fermée) et **précise en basse puissance** (le Pi tire ~2–8 W).

**Ce qui débloque la suite :**
- ⛔ Obtenir la **prise connectée** (lisible par script) — à demander à Stéphane.
- ⛔ Débloquer l'**Ethernet du labo** (MAC à enregistrer) pour le SSH headless.
- ✅ Déjà fait sans rien acheter : `pmic_read_adc` scripté à la main, idle vs charge mesurés.
  Prochain pas : automatiser en Python (harness PMIC).

---

## Sources
- Scaphandre RAPL/ARM : github.com/hubblo-org/scaphandre/issues/35
- CodeCarbon sur Pi 5 (fallback constant) : github.com/mlco2/codecarbon/issues/790 ; mlco2.github.io/codecarbon/rapl.html
- Alumet : github.com/alumet-dev/alumet ; hal.science/hal-05246933
- Pi 5 PMIC : github.com/jfikar/RPi5-power ; forums.raspberrypi.com pmic_read_adc
- EcoLogits : github.com/genai-impact/ecologits
- Noureddine et al., 2013 — *A Review of Energy Measurement Approaches*
