from llama_cpp import Llama
from codecarbon import EmissionsTracker
import pandas as pd
import json
import os
import time
from datetime import datetime

#  REGLAGES DE LA CAMPAGNE  (tout se modifie ICI)
MACHINE = "PC"                          # "PC" maintenant, "Pi5" plus tard
TEMPERATURE = 0.0                       # 0 = reponses deterministes (reproductibles)
N_REPETITIONS = 3                       # nb de mesures par configuration
MAX_TOKENS_VALEURS = [16, 64, 256]      # grille de longueurs de reponse a tester

# Liste des modeles a tester : on en ajoute/enleve autant qu'on veut.
# (Il faut que le fichier .gguf existe dans models/ ; sinon il est ignore.)
MODELES = [
    {"nom": "Llama-3.2-1B", "quantification": "Q2_K",   "path": "models/Llama-3.2-1B-Instruct-Q2_K.gguf"},
    {"nom": "Llama-3.2-1B", "quantification": "Q4_K_M", "path": "models/Llama-3.2-1B-Instruct-Q4_K_M.gguf"},
    {"nom": "Llama-3.2-1B", "quantification": "Q8_0",   "path": "models/Llama-3.2-1B-Instruct-Q8_0.gguf"},
]

# 1. Charger notre echantillon fige de prompts (cree par build_prompts.py)
with open("prompts/prompts.json", encoding="utf-8") as f:
    fiches = json.load(f)

# 2. Liste vide qui va recevoir TOUS les resultats (tous modeles confondus)
resultats = []

# 3. Boucle EXTERNE : pour CHAQUE modele de la liste
for config in MODELES:

    # 3a. Si le fichier .gguf n'existe pas, on saute ce modele (sans planter)
    if not os.path.exists(config["path"]):
        print(f"!! Fichier introuvable, modele ignore : {config['path']}")
        continue

    print(f"\n===== Modele {config['nom']} {config['quantification']} =====")

    # 3b. Charger CE modele (une fois) + inference de chauffe
    modele = Llama(model_path=config["path"], verbose=False)
    modele("Bonjour", max_tokens=8, temperature=TEMPERATURE)

    # 3c. Boucles internes : max_tokens -> prompt -> repetitions
    for max_tokens in MAX_TOKENS_VALEURS:
        for fiche in fiches:
            prompt = fiche["prompt"]
            for run in range(N_REPETITIONS):
                tracker = EmissionsTracker(save_to_file=False, log_level="error")
                tracker.start()
                debut = time.perf_counter()

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
                    "prompt": prompt,
                    "classe": fiche["classe"],
                    "n_caracteres": fiche["n_caracteres"],
                    "max_tokens": max_tokens,
                    "run": run + 1,
                    "tokens": nb_tokens,
                    "duree_s": round(duree, 2),
                    "energie_kWh": energie,
                    "joules": round(joules, 1),
                })

                print(f"[{config['quantification']}] [max_tokens={max_tokens}] "
                      f"[run {run + 1}/{N_REPETITIONS}] ({fiche['classe']}) "
                      f"{prompt[:30]}...  ->  {nb_tokens} tok, {duree:.2f} s, {joules:.1f} J")

# 4. Ecrire TOUS les resultats dans un seul CSV horodate
horodatage = datetime.now().strftime("%Y-%m-%d_%Hh%M")
chemin = f"data/raw/resultats_{MACHINE}_{horodatage}.csv"
pd.DataFrame(resultats).to_csv(chemin, index=False)
print(f"\n{len(resultats)} mesures enregistrees dans {chemin}")
