# État de l'art

## 1. Contexte : LLMs embarqués sur edge

Le déploiement de modèles de langage sur plateformes embarquées (Raspberry Pi, Orange Pi, Jetson)
soulève deux verrous : (1) la mémoire limitée impose des modèles ≤ 2B paramètres quantifiés,
(2) l'absence de compteurs RAPL sur ARM oblige à des méthodes de mesure alternatives [6, 13].

---

## 2. Synthèse des références clés

### [2] LLMPi — Optimizing LLMs for High-Throughput on Raspberry Pi (Ardakani et al., CVPR 2025)
- **Support** : Raspberry Pi (edge CPU contraint)
- **Technique** : k-quantization PTQ sur bits 2/4/6/8 + QAT (BitNet)
- **Résultat clé** : quantification = levier principal throughput/énergie sur Pi
- **Lien avec notre travail** : valide le choix llama.cpp + GGUF comme stack d'inférence ; notre campagne étend l'analyse à 3 architectures distinctes avec mesure PMIC onboard Pi5

### [3] Characterizing and Understanding Energy Footprint of Small Language Models on Edges (Islam et al., 2025)
- **Support** : edge GPU (Jetson) + CPU
- **Modèles** : famille 1B–7B, dont Llama-3.2-1B
- **Résultat clé** : empreinte énergie des SLM proportionnelle au nombre de tokens générés (loi linéaire)
- **Lien avec notre travail** : notre mesure PMIC confirme cette loi (r > 0.997 sur 3 modèles) sur Pi5 CPU-only — contribution : validation sur ARM sans GPU

### [13] An Evaluation of LLMs Inference on Popular Single-Board Computers (Tung & Nguyen, 2025)
- **Support** : Raspberry Pi 4, Raspberry Pi 5, Orange Pi 5 Pro
- **Résultat clé** : SBCs supportent fiablement modèles ≤ 1.5B ; Llamafile 4× plus rapide, 30–40% moins de puissance qu'Ollama
- **Lien avec notre travail** : confirme la fenêtre 1–1.5B retenue ; notre étude approfondit la granularité par quant (Q3/Q4/Q8) et par rail PMIC, absente de [13]

### [ACM ToIoT 2025] Sustainable LLM Inference for Edge AI (arxiv 2504.03360)
- **Support** : Raspberry Pi 4, mesure Joulescope JS110 (hardware externe)
- **Modèles testés** : Gemma 2 (2B), Llama 3.2 (1B), Qwen 2.5 (0.5B, 1.5B) — même familles que notre étude
- **Résultat clé** : Llama-3.2-1B fp16 = 17.60 J/tok → Q3_K_S = 3.75 J/tok (×4.7)
- **Lien avec notre travail** : notre Q3_K_M Llama = 0.455 J/tok sur Pi5 vs 3.75 J/tok Pi4 — amélioration Pi5 confirmée ; différence méthode mesure (PMIC I²C intégré vs Joulescope externe) constitue une contribution méthodologique

### Outils de mesure énergétique

| Outil | Type | Disponible Pi | Note |
|-------|------|---------------|------|
| CodeCarbon [11] | Estimation logicielle | ✓ | Surestime +12 à +35% sur ARM (RAPL absent) |
| PMIC I²C Pi5 | Mesure hardware onboard | ✓ | Notre méthode principale — rail VDD_CORE isolé |
| Scaphandre [8] | Monitoring RAPL | ✗ | RAPL absent ARM → inutilisable Pi |
| PowerAPI [12] | Framework RAPL | ✗ | Même limitation |
| Alumet [9] | Framework modulaire | Partiel | Pas testé Pi5 |
| Joulescope JS110 | Hardware externe | ✓ (coûteux) | Utilisé dans [ACM ToIoT] — alternative à prise Z-Wave |

---

## 3. Justification du choix des modèles

### Critères de sélection

| Critère | Source | Valeur retenue |
|---------|--------|----------------|
| Params ≤ 2B (contrainte RAM Pi5) | [13] — SBCs fiables jusqu'à 1.5B | 1B–1.5B |
| Format GGUF + llama.cpp | [2] — k-quant PTQ optimal sur Pi | Q3/Q4/Q8 |
| Architectures diversifiées | [3] — empreinte varie par archi | 3 familles distinctes |
| Représentativité littérature | [ACM ToIoT] — Llama/Gemma/Qwen déjà benchmarkés | Même familles |

### Justification par modèle

**Llama-3.2-1B (Meta AI)**
Référence de facto edge en 2025 : cité dans [2], [3], [13] et [ACM ToIoT] comme baseline
standard pour évaluation sur Pi. Architecture LlamaForCausalLM la plus documentée edge →
reproductibilité maximale. Nos résultats (Q4_K_M = 0.473 J/tok) permettent comparaison directe
avec [ACM ToIoT] (Joulescope Pi4) → contribution méthodologique PMIC vs hardware externe.

**Gemma-3-1B (Google DeepMind)**
Google positionne Gemma-3-1B pour *"extreme resource constraints"* — seul 1B multimodal de
la famille. [ACM ToIoT] inclut Gemma 2 (2B) ; Gemma-3-1B est la génération suivante, attendue
plus efficace. Nos résultats confirment : **Gemma-3-1B Q3_K_M = 0.359 J/tok = meilleur résultat
absolu** — valide le positionnement Google et constitue notre recommandation principale.

**Qwen2.5-1.5B (Alibaba DAMO)**
Rapport technique Qwen2.5 (arxiv 2412.15115) : Qwen2.5-1.5B domine en benchmark vs Gemma2-2.6B
sur tâches math/code avec 1.5B params seulement. [ACM ToIoT] mesure Qwen2.5-1.5B = 7.57 J/tok
(plus efficace que Llama 8.40 J/tok sur Pi4 Joulescope). Nos mesures PMIC Pi5 donnent
hiérarchie inverse (Qwen = 0.559 J/tok > Llama = 0.473 J/tok) → **contribution originale** :
la méthode de mesure et la génération matérielle (Pi4→Pi5) modifient les classements.

### Diversité architecturale

| Modèle | Architecture | Tokenizer | Institution |
|--------|-------------|-----------|-------------|
| Llama-3.2-1B | LlamaForCausalLM | Tiktoken BPE | Meta AI |
| Gemma-3-1B | Gemma3ForCausalLM | SentencePiece | Google DeepMind |
| Qwen2.5-1.5B | Qwen2ForCausalLM | Tiktoken BPE | Alibaba DAMO |

3 architectures, 3 tokenizers différents, 3 institutions → comparaison non biaisée.
Pattern Q3 > Q4 observé sur Gemma (inverse de Llama/Qwen) confirme que l'interaction
architecture × quantification est réelle et non un artefact.

---

## 4. Gap comblé par notre étude

| Étude existante | Plateforme | Méthode mesure | Granularité |
|-----------------|-----------|----------------|-------------|
| LLMPi [2] | Pi4 | Non précisée | Throughput, pas J/tok |
| Islam [3] | Jetson GPU | Puissance système | Par modèle global |
| Tung [13] | Pi4/Pi5/OrangePi | Estimation logicielle | Throughput/latence |
| ACM ToIoT 2025 | Pi4 | Joulescope externe | J/tok mais Pi4, fp16 |
| **Notre étude** | **Pi5** | **PMIC I²C onboard** | **J/tok par quant × modèle × classe prompt** |

Contribution principale : première mesure PMIC I²C intégré Pi5 (rail VDD_CORE isolé)
avec granularité à l'échelle de la requête, sur 3 architectures × 3 niveaux de quantification
× 3 longueurs de réponse × 5 classes de prompts → 3 645 mesures.

---

## Références

- [2] Ardakani et al. *LLMPi: Optimizing LLMs for High-Throughput on Raspberry Pi*. CVPR 2025. https://arxiv.org/abs/2504.02118
- [3] Islam et al. *Characterizing and Understanding Energy Footprint and Efficiency of Small Language Model on Edges*. 2025. https://arxiv.org/abs/2511.11624
- [6] Noureddine et al. *A review of energy measurement approaches*. OS Review, 2013.
- [8] Petit. *Scaphandre*. https://github.com/hubblo-org/scaphandre
- [9] Raffin et al. *Alumet: a modular framework to standardize energy measurement*. 2025.
- [11] Schmidt et al. *CodeCarbon*. 2021.
- [12] SPIRALS. *PowerAPI*.
- [13] Tung & Nguyen. *An Evaluation of LLMs Inference on Popular Single-board Computers*. 2025. https://arxiv.org/html/2511.07425v1
- [15] Wang et al. *Model compression and efficient inference for LLMs: A survey*. CoRR 2024.
- [ACM ToIoT] *Sustainable LLM Inference for Edge AI*. ACM ToIoT 2025. https://arxiv.org/abs/2504.03360
