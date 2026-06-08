"""Campagne d'expériences : croise prompts et paramètres, mesure, sauvegarde.

Boucle sur le jeu de prompts et sur une grille de paramètres d'inférence, mesure
chaque exécution et écrit une ligne par run dans un CSV (data/raw/).
"""

from __future__ import annotations

import csv
import json
from itertools import product
from pathlib import Path

from inference import lancer_inference
from measure import mesurer

RACINE = Path(__file__).resolve().parents[1]


def charger_prompts(chemin: Path) -> list[dict]:
    return json.loads(chemin.read_text(encoding="utf-8"))


def lancer_campagne(
    modele_path: str,
    prompts_path: Path = RACINE / "prompts" / "prompts.json",
    sortie_csv: Path = RACINE / "data" / "raw" / "mesures.csv",
    grille_max_tokens: tuple[int, ...] = (32, 128),
    grille_temperature: tuple[float, ...] = (0.7,),
) -> None:
    prompts = charger_prompts(prompts_path)
    sortie_csv.parent.mkdir(parents=True, exist_ok=True)

    champs = [
        "prompt_id", "categorie", "max_tokens", "temperature",
        "n_tokens_generes", "duree_s", "cpu_percent", "freq_mhz", "energie_kwh",
    ]
    nouveau = not sortie_csv.exists()

    with sortie_csv.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=champs)
        if nouveau:
            writer.writeheader()

        for prompt, max_tokens, temp in product(
            prompts, grille_max_tokens, grille_temperature
        ):
            with mesurer() as m:
                res = lancer_inference(
                    modele_path=modele_path,
                    prompt=prompt["texte"],
                    prompt_id=prompt["id"],
                    max_tokens=max_tokens,
                    temperature=temp,
                )

            writer.writerow({
                "prompt_id": res.prompt_id,
                "categorie": prompt.get("categorie", ""),
                "max_tokens": max_tokens,
                "temperature": temp,
                "n_tokens_generes": res.n_tokens_generes,
                "duree_s": round(res.duree_s, 4),
                "cpu_percent": m.cpu_percent_moyen,
                "freq_mhz": m.freq_cpu_mhz,
                "energie_kwh": m.energie_kwh,
            })
            print(f"OK {res.prompt_id} max_tokens={max_tokens} -> {res.duree_s:.2f}s")


if __name__ == "__main__":
    lancer_campagne(modele_path="models/modele.gguf")
