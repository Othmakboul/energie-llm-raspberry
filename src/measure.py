"""Mesure des métriques système et estimation énergétique.

Sur Raspberry Pi il n'y a pas de compteur matériel (RAPL). On combine donc :
  - les métriques système via psutil (charge CPU, fréquence),
  - une estimation de l'énergie via CodeCarbon.

Le context manager `mesurer` encadre un bloc de code et renvoie les métriques.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field

import psutil


@dataclass
class Metriques:
    duree_s: float = 0.0
    cpu_percent_moyen: float = 0.0
    freq_cpu_mhz: float = 0.0
    energie_kwh: float | None = None
    extra: dict = field(default_factory=dict)


@contextmanager
def mesurer(suivi_energie: bool = True):
    """Encadre un bloc de code et collecte les métriques pendant son exécution.

    Usage :
        with mesurer() as m:
            ... # code à mesurer
        print(m.duree_s, m.energie_kwh)
    """
    metriques = Metriques()

    tracker = None
    if suivi_energie:
        try:
            from codecarbon import EmissionsTracker

            tracker = EmissionsTracker(save_to_file=False, log_level="error")
            tracker.start()
        except Exception as exc:  # CodeCarbon indisponible / non supporté
            metriques.extra["codecarbon_erreur"] = str(exc)

    psutil.cpu_percent(interval=None)  # amorce la mesure
    debut = time.perf_counter()
    try:
        yield metriques
    finally:
        metriques.duree_s = time.perf_counter() - debut
        metriques.cpu_percent_moyen = psutil.cpu_percent(interval=None)
        freq = psutil.cpu_freq()
        metriques.freq_cpu_mhz = freq.current if freq else 0.0

        if tracker is not None:
            emissions = tracker.stop()  # kgCO2eq
            # CodeCarbon expose aussi l'énergie consommée en kWh
            try:
                metriques.energie_kwh = tracker.final_emissions_data.energy_consumed
            except Exception:
                metriques.extra["emissions_kgco2"] = emissions


if __name__ == "__main__":
    with mesurer() as m:
        sum(i * i for i in range(2_000_000))  # charge factice
    print(f"duree={m.duree_s:.3f}s cpu={m.cpu_percent_moyen}% energie={m.energie_kwh} kWh")
