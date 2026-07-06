"""Test croise TAILLE DU PROMPT x n_ctx.

Question : n_ctx a-t-il un effet energetique quand le prompt est long
(donc remplit une part significative du contexte alloue) ?

Jusqu'ici (campaign_nctx.py) les prompts etaient courts (<100 tokens) face a
n_ctx=512/2048/8192 : le contexte n'etait quasiment jamais rempli, d'ou un
effet de n_ctx negligeable (+1-2%). Ici on fait varier la longueur REELLE du
prompt (mesuree en tokens) ET n_ctx, pour separer deux effets :
  1. le cout de prefill (proportionnel au nb de tokens du prompt, independant
     de n_ctx tant que le prompt tient dedans),
  2. le cout d'allocation/remplissage du KV-cache (qui devrait grandir quand
     le prompt approche la taille de n_ctx).

Un seul modele est teste (suffisant pour isoler l'effet ; etendre MODELES
si le temps le permet).
"""

from llama_cpp import Llama
from codecarbon import EmissionsTracker
from pmic import MesurePMIC
import pandas as pd
import time
from datetime import datetime

# ============================================================
#  REGLAGES
# ============================================================
MACHINE = "Pi5"
MODELE_PATH = "models/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
MODELE_NOM = "Llama-3.2-1B"
QUANTIFICATION = "Q4_K_M"
TEMPERATURE = 0.0
N_REPETITIONS = 3
N_THREADS = 4
MAX_TOKENS_SORTIE = 64          # sortie fixe, pour isoler l'effet entree x n_ctx

# Grille (n_ctx, longueur de prompt visee en tokens). On ne garde que les
# combinaisons ou le prompt tient dans le contexte avec une marge pour la
# sortie (n_tokens_prompt + MAX_TOKENS_SORTIE < n_ctx).
GRILLE = [
    (512,  50),
    (512,  100),
    (512,  400),     # ~78% du contexte : quasi plein
    (2048, 50),
    (2048, 100),
    (2048, 400),     # meme prompt qu'au-dessus, mais contexte large -> comparaison directe
    (2048, 800),
    (2048, 1900),    # ~93% du contexte : quasi plein
    (8192, 50),
    (8192, 400),     # meme prompt, contexte tres large -> isoler prefill pur
    (8192, 1900),    # meme prompt qu'au n_ctx=2048 quasi-plein, ici tres degage
    (8192, 4000),
    (8192, 7800),    # ~95% du contexte : quasi plein
]
# ============================================================

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

# 1. Tokeniser le texte de base une fois (n_ctx=8192 = le plus grand, juste
#    pour disposer du tokenizer ; ne sert pas encore a l'inference).
print("Chargement du tokenizer (instance temporaire, n_ctx=8192)...")
tok_modele = Llama(model_path=MODELE_PATH, n_ctx=8192, n_threads=N_THREADS, verbose=False)
base_tokens = tok_modele.tokenize(TEXTE_BASE.encode("utf-8"))
plus_grande_taille = max(n for _, n in GRILLE)
reserve = base_tokens * (plus_grande_taille // len(base_tokens) + 2)

# 2. Fabriquer une bonne fois pour toutes le texte de chaque longueur de prompt visee
longueurs_uniques = sorted(set(n for _, n in GRILLE))
prompts_par_longueur = {}
for n_tok in longueurs_uniques:
    toks = reserve[:n_tok]
    prompts_par_longueur[n_tok] = tok_modele.detokenize(toks).decode("utf-8", errors="ignore")
del tok_modele

# 3. Boucle principale : un rechargement du modele par valeur de n_ctx
resultats = []
for n_ctx in sorted(set(c for c, _ in GRILLE)):
    longueurs = [n for c, n in GRILLE if c == n_ctx]
    print(f"\n===== {MODELE_NOM} {QUANTIFICATION} n_ctx={n_ctx} =====")

    modele = Llama(model_path=MODELE_PATH, n_ctx=n_ctx, n_threads=N_THREADS, verbose=False)
    modele("Bonjour", max_tokens=8, temperature=TEMPERATURE)   # inference de chauffe

    for n_tok in longueurs:
        prompt = prompts_par_longueur[n_tok]
        fraction = n_tok / n_ctx

        for run in range(N_REPETITIONS):
            modele.reset()   # vide le cache -> chaque run relit le prompt en entier (cold)

            tracker = EmissionsTracker(save_to_file=False, log_level="error")
            tracker.start()
            debut = time.perf_counter()
            with MesurePMIC() as pmic:
                sortie = modele(prompt, max_tokens=MAX_TOKENS_SORTIE, temperature=TEMPERATURE)
            duree = time.perf_counter() - debut
            tracker.stop()
            energie = tracker.final_emissions_data.energy_consumed

            input_tokens = sortie["usage"]["prompt_tokens"]
            output_tokens = sortie["usage"]["completion_tokens"]
            joules = energie * 3_600_000

            resultats.append({
                "machine": MACHINE,
                "modele": MODELE_NOM,
                "quantification": QUANTIFICATION,
                "n_threads": N_THREADS,
                "n_ctx": n_ctx,
                "n_tokens_prompt_cible": n_tok,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "fraction_ctx_remplie": round(fraction, 3),
                "run": run + 1,
                "duree_s": round(duree, 2),
                "energie_kWh": energie,
                "joules": round(joules, 1),
                "joules_pmic": round(pmic.energie_joules, 1),
                "joules_pmic_cpu": round(pmic.energie_par_rail.get("VDD_CORE", 0), 1),
                "w_moyen_pmic": round(pmic.puissance_moyenne_w, 2),
            })

            print(f"[n_ctx={n_ctx}] [prompt~{n_tok}tok reel={input_tokens}] "
                  f"[fill={fraction:.0%}] [run {run + 1}/{N_REPETITIONS}] "
                  f"-> {output_tokens} tok gen, {duree:.2f}s, {pmic.energie_joules:.1f}J (PMIC)")

    del modele

horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%M")
chemin = f"data/raw/prompt_length_nctx_{MACHINE}_{horodatage}.csv"
pd.DataFrame(resultats).to_csv(chemin, index=False)
print(f"\n{len(resultats)} mesures enregistrees dans {chemin}")
