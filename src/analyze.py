"""Analyse rapide d'un CSV de campagne.

Usage :
    python src/analyze.py                         # prend le CSV le plus recent de data/raw/
    python src/analyze.py data/raw/mon_fichier.csv

Affiche, par max_tokens et par classe de prompt :
- mediane / moyenne / ecart-type de l'energie (CodeCarbon et PMIC si presents)
- compare l'estimation logicielle (CodeCarbon) a la mesure materielle (PMIC)
"""

import sys
import glob
import pandas as pd

# 1. Choisir le fichier : argument fourni, sinon le CSV le plus recent de data/raw/
if len(sys.argv) > 1:
    chemin = sys.argv[1]
else:
    fichiers = sorted(glob.glob("data/raw/*.csv"))
    if not fichiers:
        print("Aucun CSV dans data/raw/")
        sys.exit()
    chemin = fichiers[-1]

print(f"Fichier analyse : {chemin}\n")
df = pd.read_csv(chemin)
print(f"{len(df)} mesures\n")

# 2. Energie (CodeCarbon) par max_tokens
if "max_tokens" in df.columns:
    print("=== Energie CodeCarbon (joules) par max_tokens ===")
    print(df.groupby("max_tokens")["joules"].agg(["median", "mean", "std"]).round(1))
    print()

    # 3. Si la mesure PMIC est presente : la comparer a CodeCarbon
    if "joules_pmic" in df.columns:
        print("=== Energie PMIC (joules) par max_tokens ===")
        print(df.groupby("max_tokens")["joules_pmic"].agg(["median", "mean", "std"]).round(1))
        print()

        comp = df.groupby("max_tokens").agg(
            cc=("joules", "median"),
            pmic=("joules_pmic", "median"),
        )
        comp["ecart_%"] = ((comp["cc"] - comp["pmic"]) / comp["pmic"] * 100).round(1)
        print("=== CodeCarbon vs PMIC (surestimation de l'estimation logicielle) ===")
        print(comp.round(1))
        print()

# 4. Effet de la classe de prompt (taille) a tokens fixes
if "classe" in df.columns and "max_tokens" in df.columns:
    print("=== Energie PMIC mediane par classe et max_tokens ===")
    col = "joules_pmic" if "joules_pmic" in df.columns else "joules"
    print(df.pivot_table(index="classe", columns="max_tokens", values=col, aggfunc="median").round(1))
    print()

# 5. Energie par token (efficacite)
col = "joules_pmic" if "joules_pmic" in df.columns else "joules"
d = df[df["tokens"] > 0].copy()
d["j_par_token"] = d[col] / d["tokens"]
print(f"=== Joules par token ({col}) selon max_tokens ===")
print(d.groupby("max_tokens")["j_par_token"].median().round(3))
