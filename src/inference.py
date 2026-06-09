from llama_cpp import Llama
from codecarbon import EmissionsTracker
import time

# 1. Charger le modele (hors mesure)
mon_modele = Llama(model_path="models/Llama-3.2-1B-Instruct-Q4_K_M.gguf", verbose=False)

# 2. Demarrer le compteur d'energie + le chrono
tracker = EmissionsTracker(save_to_file=False, log_level="error")
tracker.start()
debut = time.perf_counter()

# 3. Generer la reponse
resultat = mon_modele("Quelle est la capitale de la France ?", max_tokens=64)

# 4. Arreter le chrono + le compteur
duree = time.perf_counter() - debut
emissions = tracker.stop()
energie = tracker.final_emissions_data.energy_consumed   # en kWh

# 5. Recuperer les infos de la reponse
texte = resultat["choices"][0]["text"]
nb_tokens = resultat["usage"]["completion_tokens"]

# 6. Tout afficher
print(texte)
print(f"{nb_tokens} tokens en {duree:.2f} s")
print(f"Energie : {energie:.8f} kWh  ({energie * 3_600_000:.1f} J)")