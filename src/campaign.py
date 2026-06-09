from llama_cpp import Llama
from codecarbon import EmissionsTracker
import pandas as pd
import time

# 1. Charger le modele UNE SEULE FOIS (avant la boucle)
modele = Llama(model_path="models/Llama-3.2-1B-Instruct-Q4_K_M.gguf", verbose=False)

# 1bis. Inference de chauffe (resultat ignore) : reveille le CPU avant de mesurer
modele("Bonjour", max_tokens=8)

# 2. La liste des questions a tester
prompts = [
    "Quelle est la capitale de la France ?",
    "Cite trois fruits.",
    "Explique en une phrase ce qu'est un ordinateur.",
]

# 3. Combien de fois on repete chaque mesure (pour moyenner et reduire le bruit)
N_REPETITIONS = 3

# 4. Liste vide qui va recevoir tous les resultats
resultats = []

# 5. Pour CHAQUE question, on repete la mesure N fois
for prompt in prompts:
    for run in range(N_REPETITIONS):          # range(3) -> 0, 1, 2
        tracker = EmissionsTracker(save_to_file=False, log_level="error")
        tracker.start()
        debut = time.perf_counter()

        sortie = modele(prompt, max_tokens=64)

        duree = time.perf_counter() - debut
        tracker.stop()
        energie = tracker.final_emissions_data.energy_consumed

        nb_tokens = sortie["usage"]["completion_tokens"]
        joules = energie * 3_600_000

        # On ajoute une "fiche" de resultat a la liste (avec le numero de run)
        resultats.append({
            "prompt": prompt,
            "run": run + 1,                   # run + 1 pour compter a partir de 1
            "tokens": nb_tokens,
            "duree_s": round(duree, 2),
            "energie_kWh": energie,
            "joules": round(joules, 1),
        })

        print(f"[run {run + 1}/{N_REPETITIONS}] {prompt}  ->  {nb_tokens} tokens, {duree:.2f} s, {joules:.1f} J")

# 6. Ecrire toute la liste dans un fichier CSV
pd.DataFrame(resultats).to_csv("data/raw/resultats.csv", index=False)
print("\nResultats enregistres dans data/raw/resultats.csv")