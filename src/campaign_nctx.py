"""
Campagne dediee a l'effet de n_ctx (taille de contexte allouee) sur l'energie :
memes modeles/quantifications que campaign.py, n_threads fixe a 4, n_ctx varie
(512 / 2048 / 8192). Ecrit une ligne par requete dans data/raw/nctx_*.csv.

A lancer : python src/campaign_nctx.py
"""

from llama_cpp import Llama
from codecarbon import EmissionsTracker
from pmic import MesurePMIC
from prise import MesurePrise
import pandas as pd
import json
import os
import time
import contextlib
from datetime import datetime

MACHINE = "Pi5"
TEMPERATURE = 0.0
N_REPETITIONS = 3
MAX_TOKENS_VALEURS = [16, 64, 256]
MESURER_PRISE = False
PRISE_NODE_ID = 2
BASELINE_W = 3.5

MODELES = []
for nom, quants, paths in [
    ("Llama-3.2-1B", ["Q3_K_L", "Q4_K_M", "Q8_0"], [
        "models/Llama-3.2-1B-Instruct-Q3_K_L.gguf",
        "models/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "models/Llama-3.2-1B-Instruct-Q8_0.gguf",
    ]),
    ("Gemma-3-1B", ["Q3_K_M", "Q4_K_M", "Q8_0"], [
        "models/gemma-3-1b-it-Q3_K_M.gguf",
        "models/gemma-3-1b-it-Q4_K_M.gguf",
        "models/gemma-3-1b-it-Q8_0.gguf",
    ]),
    ("Qwen2.5-1.5B", ["Q3_K_L", "Q4_K_M", "Q8_0"], [
        "models/Qwen2.5-1.5B-Instruct-Q3_K_L.gguf",
        "models/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf",
        "models/Qwen2.5-1.5B-Instruct-Q8_0.gguf",
    ]),
]:
    for q, p in zip(quants, paths):
        for ctx in [512, 2048, 8192]:
            MODELES.append({"nom": nom, "quantification": q, "path": p, "n_threads": 4, "n_ctx": ctx})

with open("prompts/prompts.json", encoding="utf-8") as f:
    fiches = json.load(f)

resultats = []
ctx_prise = MesurePrise(node_id=PRISE_NODE_ID, baseline_w=BASELINE_W) if MESURER_PRISE else contextlib.nullcontext()

with ctx_prise as prise:
    for config in MODELES:
        if not os.path.exists(config["path"]):
            print(f"!! Fichier introuvable, modele ignore : {config['path']}")
            continue

        print(f"\n===== {config['nom']} {config['quantification']} n_ctx={config['n_ctx']} =====")

        modele = Llama(
            model_path=config["path"],
            verbose=False,
            n_threads=config["n_threads"],
            n_ctx=config["n_ctx"],
        )
        modele("Bonjour", max_tokens=8, temperature=TEMPERATURE)

        for max_tokens in MAX_TOKENS_VALEURS:
            for fiche in fiches:
                prompt = fiche["prompt"]
                for run in range(N_REPETITIONS):
                    modele.reset()
                    tracker = EmissionsTracker(save_to_file=False, log_level="error")
                    tracker.start()
                    debut = time.perf_counter()
                    with MesurePMIC() as pmic:
                        sortie = modele(prompt, max_tokens=max_tokens, temperature=TEMPERATURE)
                    duree = time.perf_counter() - debut
                    tracker.stop()
                    energie = tracker.final_emissions_data.energy_consumed
                    nb_tokens = sortie["usage"]["completion_tokens"]
                    joules = energie * 3_600_000

                    resultats.append({
                        "machine": MACHINE,
                        "modele": config["nom"],
                        "quantification": config["quantification"],
                        "n_threads": config["n_threads"],
                        "n_ctx": config["n_ctx"],
                        "prompt": prompt,
                        "classe": fiche["classe"],
                        "n_caracteres": fiche["n_caracteres"],
                        "max_tokens": max_tokens,
                        "run": run + 1,
                        "tokens": nb_tokens,
                        "duree_s": round(duree, 2),
                        "energie_kWh": energie,
                        "joules": round(joules, 1),
                        "joules_pmic": round(pmic.energie_joules, 1),
                        "joules_pmic_cpu": round(pmic.energie_par_rail.get("VDD_CORE", 0), 1),
                        "w_moyen_pmic": round(pmic.puissance_moyenne_w, 2),
                    })

                    print(f"[{config['quantification']}] [n_ctx={config['n_ctx']}] [max_tokens={max_tokens}] "
                          f"[run {run+1}/{N_REPETITIONS}] {prompt[:30]}... -> "
                          f"{nb_tokens} tok, {duree:.2f}s, {pmic.energie_joules:.1f}J (PMIC)")

horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%M")
chemin = f"data/raw/nctx_{MACHINE}_{horodatage}.csv"
pd.DataFrame(resultats).to_csv(chemin, index=False)
print(f"\n{len(resultats)} mesures enregistrees dans {chemin}")
