from llama_cpp import Llama
from codecarbon import EmissionsTracker
import pandas as pd
import json
import time
from datetime import datetime

# 1. Charger notre echantillon fige de 45 prompts (cree par build_prompts.py)
with open("prompts/prompts.json", encoding="utf-8") as f:
    fiches = json.load(f)

# 2. Charger le modele
modele = Llama(model_path="models/Llama-3.2-1B-Instruct-Q4_K_M.gguf", verbose=False)

# 2bis. reveille le CPU avant de mesurer
modele("Bonjour", max_tokens=8)

# 3. La grille d'experience : valeurs de max_tokens a tester x repetitions
MAX_TOKENS_VALEURS = [16, 64, 256]
N_REPETITIONS = 3

# 4. Liste vide qui va recevoir tous les resultats
resultats = []

# 5. Pour CHAQUE valeur de max_tokens, CHAQUE fiche, N repetitions
for max_tokens in MAX_TOKENS_VALEURS:
    for fiche in fiches:
        prompt = fiche["prompt"]
        for run in range(N_REPETITIONS):
            tracker = EmissionsTracker(save_to_file=False, log_level="error")
            tracker.start()
            debut = time.perf_counter()

            sortie = modele(prompt, max_tokens=max_tokens)

            duree = time.perf_counter() - debut
            tracker.stop()
            energie = tracker.final_emissions_data.energy_consumed

            nb_tokens = sortie["usage"]["completion_tokens"]
            joules = energie * 3_600_000

            resultats.append({
                "prompt": prompt,
                "classe": fiche["classe"],            # court / moyen / long
                "n_caracteres": fiche["n_caracteres"],
                "max_tokens": max_tokens,
                "run": run + 1,
                "tokens": nb_tokens,
                "duree_s": round(duree, 2),
                "energie_kWh": energie,
                "joules": round(joules, 1),
            })

            print(f"[max_tokens={max_tokens}] [run {run + 1}/{N_REPETITIONS}] "
                  f"({fiche['classe']}) {prompt[:40]}...  ->  "
                  f"{nb_tokens} tokens, {duree:.2f} s, {joules:.1f} J")

# 6. Ecrire dans un CSV HORODATE : on n'ecrase plus jamais d'anciens resultats
horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%M")
chemin = f"data/raw/resultats_{horodatage}.csv"
pd.DataFrame(resultats).to_csv(chemin, index=False)
print(f"\n{len(resultats)} mesures enregistrees dans {chemin}")
