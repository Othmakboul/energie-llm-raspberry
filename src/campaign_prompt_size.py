"""Test de l'effet de la TAILLE DU PROMPT (entree) sur l'energie.

Idee : on fixe la SORTIE (max_tokens constant) et on fait varier la longueur
de l'ENTREE sur une large plage (128 -> 4096 tokens). But : voir si, au-dela
d'un certain seuil, le cout de lecture du prompt (prefill) devient mesurable.

ATTENTION : par defaut llama.cpp limite le contexte a 512 tokens. On augmente
donc n_ctx pour que les grands prompts ne soient PAS tronques.
"""

from llama_cpp import Llama
from codecarbon import EmissionsTracker
from pmic import MesurePMIC      # methode 2 : mesure onboard REELLE du Pi 5 (mock hors Pi) [Amine]
import pandas as pd
import time
from datetime import datetime

# ============================================================
#  REGLAGES
# ============================================================
MACHINE = "Pi5"                                          # "PC" ou "Pi5"
MODELE_PATH = "models/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
MODELE_NOM = "Llama-3.2-1B"
QUANTIFICATION = "Q4_K_M"
TEMPERATURE = 0.0
N_REPETITIONS = 3
MAX_TOKENS_SORTIE = 64                                    # SORTIE fixe (pour isoler l'effet entree)
TAILLES_ENTREE = [128, 256, 512, 1024, 2048, 4096]       # longueurs d'entree a tester (en tokens)
N_CTX = 8192                                              # fenetre de contexte (doit couvrir entree + sortie)
# ============================================================

# Texte de base (anglais, comme le modele et Alpaca). On le repetera/tronquera
# pour fabriquer des prompts de la longueur exacte voulue.
TEXTE_BASE = (
    "Edge computing brings computation closer to where data is produced. "
    "Small language models can now run on devices like the Raspberry Pi. "
    "Energy efficiency is a central concern for such constrained platforms. "
    "Quantization reduces the memory footprint of a model with little loss. "
    "Measuring the energy of a single request is surprisingly difficult. "
    "The number of generated tokens is the main driver of consumption. "
    "Reading the prompt is usually cheaper than writing the answer. "
    "However, very long inputs may change this balance significantly. "
)

# 1. Charger le modele avec un GRAND contexte (sinon les longs prompts sont coupes)
print(f"Chargement du modele avec n_ctx={N_CTX} ...")
modele = Llama(model_path=MODELE_PATH, n_ctx=N_CTX, verbose=False)

# 2. Pre-tokeniser le texte de base, puis en faire une grande reserve de tokens
base_tokens = modele.tokenize(TEXTE_BASE.encode("utf-8"))
reserve = base_tokens * (max(TAILLES_ENTREE) // len(base_tokens) + 2)  # assez de tokens pour la + grande taille

# 3. Inference de chauffe (resultat ignore)
modele("Bonjour", max_tokens=8, temperature=TEMPERATURE)

# 4. Boucle : pour chaque taille d'entree, fabriquer un prompt et mesurer
resultats = []
for taille in TAILLES_ENTREE:
    # construire un prompt d'environ `taille` tokens (on coupe la reserve)
    toks = reserve[:taille]
    prompt = modele.detokenize(toks).decode("utf-8", errors="ignore")

    for run in range(N_REPETITIONS):
        # Vider le cache du modele -> chaque mesure refait la lecture complete (cold)
        # sinon llama.cpp reutilise le prompt deja traite et la lecture n'est plus mesuree
        modele.reset()

        tracker = EmissionsTracker(save_to_file=False, log_level="error")
        tracker.start()
        debut = time.perf_counter()

        # Le PMIC echantillonne la puissance onboard en // pendant l'inference (methode 2)
        with MesurePMIC() as pmic:
            sortie = modele(prompt, max_tokens=MAX_TOKENS_SORTIE, temperature=TEMPERATURE)

        duree = time.perf_counter() - debut
        tracker.stop()
        energie = tracker.final_emissions_data.energy_consumed

        # vraies longueurs comptees par le modele
        input_tokens = sortie["usage"]["prompt_tokens"]
        output_tokens = sortie["usage"]["completion_tokens"]
        joules = energie * 3_600_000

        resultats.append({
            "machine": MACHINE,
            "modele": MODELE_NOM,
            "quantification": QUANTIFICATION,
            "taille_cible": taille,
            "input_tokens": input_tokens,      # longueur d'entree REELLE
            "output_tokens": output_tokens,    # sortie (fixe ~64)
            "run": run + 1,
            "duree_s": round(duree, 2),
            "energie_kWh": energie,
            "joules": round(joules, 1),                          # methode 1 : CodeCarbon (estimation)
            "joules_pmic": round(pmic.energie_joules, 1),        # methode 2 : PMIC (mesure reelle onboard)
            "joules_pmic_cpu": round(pmic.energie_par_rail.get("VDD_CORE", 0), 1),  # rail CPU seul
            "w_moyen_pmic": round(pmic.puissance_moyenne_w, 2),  # puissance moyenne onboard
        })

        print(f"[entree~{taille}] [run {run + 1}/{N_REPETITIONS}] "
              f"-> {input_tokens} tok in / {output_tokens} tok out, "
              f"{duree:.2f} s, {joules:.1f} J (CodeCarbon) / {pmic.energie_joules:.1f} J (PMIC)")

# 5. Sauvegarde CSV horodate
horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%M")
chemin = f"data/raw/prompt_size_{MACHINE}_{horodatage}.csv"
pd.DataFrame(resultats).to_csv(chemin, index=False)
print(f"\n{len(resultats)} mesures enregistrees dans {chemin}")
