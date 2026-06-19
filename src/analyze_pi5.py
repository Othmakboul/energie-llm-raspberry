"""Analyse d'un CSV de campagne Pi5 (3 quantifications x 3 max_tokens).

Usage :
    python src/analyze_pi5.py                          # CSV le plus recent de data/raw/
    python src/analyze_pi5.py data/raw/mon_fichier.csv

Affiche :
  1. Energie PMIC + CodeCarbon par quantif x max_tokens
  2. Vitesse (tok/s) par quantif
  3. Modele lineaire E = fixe + alpha*tokens par quantif
  4. Surestimation CodeCarbon vs PMIC
  5. Effet taille prompt (classe) a max_tokens fixes
  6. Joules par token par quantif
"""

import sys
import glob
import numpy as np
import pandas as pd

# ── 1. Choisir le fichier ──────────────────────────────────────────────────
if len(sys.argv) > 1:
    chemin = sys.argv[1]
else:
    fichiers = sorted(glob.glob("data/raw/resultats_Pi5*.csv"))
    fichiers = [f for f in fichiers if "_prise" not in f]
    if not fichiers:
        print("Aucun CSV Pi5 dans data/raw/")
        sys.exit()
    chemin = fichiers[-1]

print(f"Fichier : {chemin}")
df = pd.read_csv(chemin)
print(f"{len(df)} mesures | quantifs : {sorted(df.quantification.unique())} | max_tokens : {sorted(df.max_tokens.unique())}\n")

COL_E = "joules_pmic" if "joules_pmic" in df.columns else "joules"

# ── 2. Energie PMIC par quantif x max_tokens ──────────────────────────────
print("=== Energie PMIC (mediane J) par quantif x max_tokens ===")
print(df.groupby(["quantification", "max_tokens"])[COL_E].median().unstack().round(1))
print()

print("=== Energie CodeCarbon (mediane J) par quantif x max_tokens ===")
print(df.groupby(["quantification", "max_tokens"])["joules"].median().unstack().round(1))
print()

# ── 3. Vitesse (tok/s) ────────────────────────────────────────────────────
print("=== Vitesse mediane (tok/s) par quantif x max_tokens ===")
df["tok_s"] = df["tokens"] / df["duree_s"]
print(df.groupby(["quantification", "max_tokens"])["tok_s"].median().unstack().round(2))
print()

# ── 4. Modele lineaire E = fixe + alpha * tokens ──────────────────────────
print("=== Modele lineaire PMIC : E = cout_fixe + alpha * tokens ===")
for q in sorted(df.quantification.unique()):
    sub = df[df.quantification == q]
    a, b = np.polyfit(sub["tokens"], sub[COL_E], 1)
    r = np.corrcoef(sub["tokens"], sub[COL_E])[0, 1]
    print(f"  {q:10s} : E = {b:.1f} J  +  {a:.3f} J/tok    (r = {r:.4f})")
print()

# ── 5. Surestimation CodeCarbon vs PMIC ───────────────────────────────────
print("=== Surestimation CodeCarbon vs PMIC par quantif ===")
ratio = df.groupby("quantification").apply(
    lambda x: (x["joules"].sum() / x[COL_E].sum() - 1) * 100
)
for q, v in ratio.items():
    print(f"  {q:10s} : CodeCarbon surestime PMIC de +{v:.1f}%")
print()

# ── 6. Effet taille prompt (classe) ───────────────────────────────────────
print("=== Energie PMIC mediane (J) par classe x quantif  [max_tokens=64] ===")
sub64 = df[df.max_tokens == 64]
print(sub64.pivot_table(index="quantification", columns="classe", values=COL_E, aggfunc="median").round(1))
print()

# ── 7. Joules par token ───────────────────────────────────────────────────
df["j_par_tok"] = df[COL_E] / df["tokens"]
print("=== Joules par token PMIC (mediane) par quantif x max_tokens ===")
print(df.groupby(["quantification", "max_tokens"])["j_par_tok"].median().unstack().round(3))
print()

# ── 8. Puissance moyenne au mur PMIC (W) ──────────────────────────────────
if "w_moyen_pmic" in df.columns:
    print("=== Puissance moyenne PMIC (W) par quantif ===")
    print(df.groupby("quantification")["w_moyen_pmic"].median().round(2))
    print()

# ── 9. Synthese : classement global par quantif (64 tokens, mediane PMIC) ─
print("=== SYNTHESE : classement efficacite energetique (64 tokens) ===")
synth = df[df.max_tokens == 64].groupby("quantification").agg(
    energie_J=(COL_E, "median"),
    vitesse_toks=("tok_s", "median"),
    j_par_token=("j_par_tok", "median"),
).sort_values("energie_J")
print(synth.round(2))
