# État de l'art — Outils de mesure d'énergie pour LLM sur Raspberry Pi 5

> Stage LISTIC — mesure de la conso énergétique de requêtes LLM sur Pi 5.
> Partie outils de mesure (Amine). Cible : mesurer l'énergie par requête d'un
> LLM léger quantifié, en fonction des paramètres d'inférence (taille prompt, tokens
> générés, quantification, threads...).
> Revue initiale : 2026-06-09. Décision retenue mise en œuvre jusqu'en fin de stage
> (voir `architecture_mesure.md` pour le protocole final et `roadmap.md` pour l'avancement).

---

## Le fait qui structure toute la décision

**RAPL (Running Average Power Limit) est une feature Intel/AMD x86 uniquement.**
Elle n'existe pas sur ARM -> pas de `/sys/class/powercap/intel-rapl` sur le Pi 5.

**Conséquence directe** : tous les outils logiciels qui lisent RAPL (Scaphandre,
CodeCarbon, PowerAPI, pyJoules, CarbonTracker...) ne fournissent aucune puissance CPU
réelle sur Raspberry Pi. Sur Pi, ils tombent soit en erreur, soit en estimation par
TDP (une constante x le temps), ce qui n'est pas une mesure.

La mesure réelle sur Pi vient forcément du matériel (wattmètre / INA219) ou
du PMIC embarqué du Pi 5. Les outils logiciels servent surtout à l'état de l'art, au
pilotage de l'expérience, et à la comptabilité CO2.

---

## A. Outils logiciels basés sur RAPL — inutilisables pour la puissance CPU sur Pi

| Outil | Langage / nature | Avantages | Inconvénients | Verdict Pi 5 |
|---|---|---|---|---|
| **Scaphandre** | Rust, exporteur de métriques | Très bonne intégration Prometheus/Grafana, par-process, mature | RAPL only, ARM sur la roadmap mais pas implémenté ; v1.0 ajoute Windows pas ARM | Pas de mesure réelle |
| **CodeCarbon** | Python, lib | Hyper simple (`@track_emissions`), donne g CO2, très répandu | Sur Pi : RAPL absent -> fallback "CPU constant mode" = TDP x temps, donc estimation pas mesure | Utile pour CO2/repère, pas pour la puissance fine |
| **PowerAPI** | Python, middleware | Power modeling fin, par-process, architecture sensor/formula | S'appuie sur RAPL (HWPC sensor) -> même limite ARM | Pas de mesure réelle |
| **pyJoules** | Python, wrapper | Mesure des bouts de code très facilement (`with EnergyContext`) | x86 / NVIDIA only (RAPL + nvml) | Inutilisable sur Pi |
| **CarbonTracker** | Python | Estime l'empreinte training/inférence ML | Lit RAPL + nvidia-smi -> x86/GPU | Inutilisable sur Pi |

---

## B. Outils logiciels d'estimation / comptabilité (pas de mesure hardware directe)

| Outil | Nature | Avantages | Inconvénients | Verdict |
|---|---|---|---|---|
| **EcoLogits** | Python, estimation | Estime énergie/CO2 d'appels LLM via API cloud (OpenAI/Anthropic) | Ne mesure aucun hardware local | Hors cible mesure, mais bon comparatif "cloud vs edge" pour le rapport |
| **Ecofloc** (2025) | CLI, par-process | Mesure conso par processus (CPU/RAM/GPU/réseau) | Dépend de ses backends -> support ARM incertain | Non retenu, non testé faute de temps |
| **Alumet** (LIG + Eviden, 2025) | Rust, framework modulaire | Archi sources -> transforms -> outputs : on peut brancher une source custom (INA219 / PMIC). Conçu pour être étendu | Plugin RAPL natif = x86 ; brancher une source custom = dev à faire | Piste la plus prometteuse pour un futur pipeline SW propre (hors périmètre du stage) |
| **Noureddine et al. (2013)** | Papier | Revue de référence des méthodes de mesure énergie logicielle | — | Background théorique pour le rapport |

---

## C. Outils matériels & spécifiques Pi 5 — la vraie voie de mesure

| Outil | Principe | Avantages | Inconvénients | Verdict |
|---|---|---|---|---|
| **PMIC onboard Pi 5** `vcgencmd pmic_read_adc` | Lecture ADC du PMIC Renesas DA9091 : tensions + courants par rail (VDD_CORE, 3V3_SYS, DDR, HDMI...) | Gratuit, déjà sur le Pi, scriptable, donne la conso par composant, fréquence ~Hz | Ne mesure pas le rail 5V d'entrée -> sous-estime la conso totale ; précision ADC limitée | Outil n°1 pour la puissance onboard / par composant. Retenu et validé (voir `architecture_mesure.md` §1) |
| **Wattmètre USB-C inline** (UM25C, PD tester...) | Mesure V/I/P réels sur le câble d'alim entre l'alim et le Pi | Conso système totale réelle, simple, pas de câblage interne | Résolution temporelle souvent faible (1 Hz), logging parfois propriétaire | Non retenu : remplacé par la prise connectée (disponible sans achat) |
| **Capteur INA219 / INA260 (I2C)** | Shunt sur la ligne d'alim, lecture V/I/P scriptable en Python | Le plus rigoureux pour de l'inline haute fréquence ; intégration Python directe ; pas cher | Demande câblage (shunt sur l'alim) + un peu d'électronique | Plan B non nécessaire, non utilisé |
| **Prise connectée / wattmètre mural** | Mesure au mur (230 V) | Zéro intrusion, ordre de grandeur immédiat | Inclut les pertes de l'alim PD -> surestime la conso "Pi seul" ; basse résolution | Retenu comme référence système total (voir `architecture_mesure.md`) |

---

## Décision retenue (actée 2026-06-09, mise en œuvre jusqu'en fin de stage)

**Triangulation à 3 méthodes** (chacune voit une chose différente, on les confronte) :

1. **Mesure fine, par composant** -> PMIC onboard (`vcgencmd pmic_read_adc`), scripté
   en Python (`src/pmic.py`), échantillonné pendant l'inférence. Gratuit, disponible immédiatement.
   Validation initiale sur le Pi le 2026-06-09 : voir `architecture_mesure.md` §1.
2. **Référence système totale** -> prise connectée (au mur, `src/prise.py`). Remplace le wattmètre USB-C
   inline (plus simple à obtenir, pas d'achat spécifique). Surestime (pertes alim PD) et lente
   -> protocole : répéter la requête xN puis diviser (voir `docs/prise_zwave_setup.md`).
3. **Comparaison logicielle** -> CodeCarbon (codé par Othmane) : conservé non pas
   comme mesure mais comme estimation à confronter au PMIC et à la prise (l'écart mesuré est
   un résultat du rapport — voir mode "Comparaison 3 méthodes" du dashboard).
4. **Pipeline logiciel extensible** : Alumet avec une source custom PMIC identifié comme piste
   de suite (hors périmètre du stage, capitalisable pour le PFE 2027).

---

## Sources
- Scaphandre RAPL/ARM : github.com/hubblo-org/scaphandre/issues/35
- CodeCarbon sur Pi 5 (fallback constant) : github.com/mlco2/codecarbon/issues/790 ; mlco2.github.io/codecarbon/rapl.html
- Alumet : github.com/alumet-dev/alumet ; hal.science/hal-05246933
- Pi 5 PMIC : github.com/jfikar/RPi5-power ; forums.raspberrypi.com pmic_read_adc
- EcoLogits : github.com/genai-impact/ecologits
- Noureddine et al., 2013 — A Review of Energy Measurement Approaches
