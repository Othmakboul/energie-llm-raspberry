"""
Brique d'apprentissage : CodeCarbon + psutil sur un calcul factice (pas de LLM).
Sert de premier test de la chaine de mesure logicielle avant de mesurer une
vraie inference (voir inference.py, puis campaign.py pour la version complete).

A lancer : python src/measure.py
"""

import psutil
from codecarbon import EmissionsTracker

# On demarre le "compteur d'energie" autour du calcul
tracker = EmissionsTracker(save_to_file=False, log_level="error")
tracker.start()

# --- Faux calcul lourd, juste pour avoir quelque chose a mesurer ---
total = 0
for i in range(50_000_000):
    total = total + i
# ------------------------------------------------------------------

# On arrete le compteur : il renvoie le CO2 (kg) et calcule l'energie
emissions = tracker.stop()
energie = tracker.final_emissions_data.energy_consumed   # en kWh

# Etat du CPU au passage
cpu = psutil.cpu_percent(interval=1)
freq = psutil.cpu_freq().current

print(f"CPU : {cpu} %  |  Frequence : {freq} MHz")
print(f"Energie consommee : {energie:.8f} kWh")
print(f"CO2 estime : {emissions:.8f} kg")