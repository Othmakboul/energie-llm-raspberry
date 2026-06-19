"""Visualisation campagne Pi5 — 3 quantifications x 3 max_tokens.

Usage :
    python src/visualize_pi5.py                          # CSV le plus recent de data/raw/
    python src/visualize_pi5.py data/raw/mon_fichier.csv

Genere dans data/ :
    pi5_energie_par_quantif.png   — energie PMIC par quantif x max_tokens
    pi5_modele_lineaire.png       — E = fixe + alpha*tokens (regression)
    pi5_vitesse.png               — tok/s par quantif
    pi5_cc_vs_pmic.png            — CodeCarbon vs PMIC par quantif
    pi5_effet_prompt.png          — effet taille prompt par quantif
    pi5_j_par_token.png           — joules/token par quantif x max_tokens
"""

import sys
import glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COULEURS = {"Q3_K_L": "#e07b39", "Q4_K_M": "#2a7aba", "Q8_0": "#4caf50"}

# ── Charger CSV ────────────────────────────────────────────────────────────
if len(sys.argv) > 1:
    chemin = sys.argv[1]
else:
    fichiers = sorted(glob.glob("data/raw/resultats_Pi5*.csv"))
    fichiers = [f for f in fichiers if "_prise" not in f]
    if not fichiers:
        print("Aucun CSV Pi5 dans data/raw/")
        sys.exit()
    chemin = fichiers[-1]

df = pd.read_csv(chemin)
print(f"Fichier : {chemin}  ({len(df)} mesures)")

COL_E = "joules_pmic" if "joules_pmic" in df.columns else "joules"
quantifs = sorted(df.quantification.unique())
tokens_vals = sorted(df.max_tokens.unique())


# ── 1. Energie PMIC par quantif x max_tokens ──────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(tokens_vals))
width = 0.25
for i, q in enumerate(quantifs):
    vals = [df[(df.quantification == q) & (df.max_tokens == t)][COL_E].median()
            for t in tokens_vals]
    errs = [df[(df.quantification == q) & (df.max_tokens == t)][COL_E].std()
            for t in tokens_vals]
    ax.bar(x + i * width, vals, width, yerr=errs, capsize=4,
           label=q, color=COULEURS.get(q), alpha=0.85)

ax.set_xticks(x + width)
ax.set_xticklabels([f"{t} tokens" for t in tokens_vals])
ax.set_ylabel("Energie PMIC (J)")
ax.set_title("Energie par quantification et nombre de tokens générés (Pi5)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("data/pi5_energie_par_quantif.png", dpi=150)
plt.close()
print("  -> data/pi5_energie_par_quantif.png")


# ── 2. Modele lineaire E = fixe + alpha*tokens ─────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
for q in quantifs:
    sub = df[df.quantification == q]
    a, b = np.polyfit(sub["tokens"], sub[COL_E], 1)
    r = np.corrcoef(sub["tokens"], sub[COL_E])[0, 1]
    tok_range = np.linspace(sub["tokens"].min(), sub["tokens"].max(), 100)
    medians = sub.groupby("tokens")[COL_E].median()
    ax.scatter(medians.index, medians.values, color=COULEURS.get(q), zorder=5, s=60)
    ax.plot(tok_range, a * tok_range + b, color=COULEURS.get(q),
            label=f"{q}  E={b:.1f}+{a:.3f}·tok  r={r:.4f}")

ax.set_xlabel("Tokens générés")
ax.set_ylabel("Energie PMIC (J)")
ax.set_title("Modèle linéaire E = coût fixe + coût/token — par quantification (Pi5)")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("data/pi5_modele_lineaire.png", dpi=150)
plt.close()
print("  -> data/pi5_modele_lineaire.png")


# ── 3. Vitesse tok/s ───────────────────────────────────────────────────────
df["tok_s"] = df["tokens"] / df["duree_s"]
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(tokens_vals))
width = 0.25
for i, q in enumerate(quantifs):
    vals = [df[(df.quantification == q) & (df.max_tokens == t)]["tok_s"].median()
            for t in tokens_vals]
    ax.bar(x + i * width, vals, width, label=q, color=COULEURS.get(q), alpha=0.85)

ax.set_xticks(x + width)
ax.set_xticklabels([f"{t} tokens" for t in tokens_vals])
ax.set_ylabel("Tokens / seconde")
ax.set_title("Vitesse d'inférence par quantification (Pi5)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("data/pi5_vitesse.png", dpi=150)
plt.close()
print("  -> data/pi5_vitesse.png")


# ── 4. CodeCarbon vs PMIC ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(tokens_vals))
width = 0.18
for i, q in enumerate(quantifs):
    cc_vals = [df[(df.quantification == q) & (df.max_tokens == t)]["joules"].median()
               for t in tokens_vals]
    pmic_vals = [df[(df.quantification == q) & (df.max_tokens == t)][COL_E].median()
                 for t in tokens_vals]
    offset = (i - 1) * width * 2.2
    ax.bar(x + offset - width / 2, pmic_vals, width,
           label=f"{q} PMIC", color=COULEURS.get(q), alpha=0.9)
    ax.bar(x + offset + width / 2, cc_vals, width,
           label=f"{q} CodeCarbon", color=COULEURS.get(q), alpha=0.4,
           hatch="//", edgecolor=COULEURS.get(q))

ax.set_xticks(x)
ax.set_xticklabels([f"{t} tokens" for t in tokens_vals])
ax.set_ylabel("Energie (J)")
ax.set_title("CodeCarbon (estimation) vs PMIC (mesure réelle) — Pi5")
ax.legend(fontsize=8, ncol=2)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("data/pi5_cc_vs_pmic.png", dpi=150)
plt.close()
print("  -> data/pi5_cc_vs_pmic.png")


# ── 5. Effet taille prompt ─────────────────────────────────────────────────
sub64 = df[df.max_tokens == 64]
classes = ["court", "moyen", "long"]
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(classes))
width = 0.25
for i, q in enumerate(quantifs):
    vals = [sub64[sub64.quantification == q][sub64.classe == c][COL_E].median()
            if c in sub64[sub64.quantification == q]["classe"].values else 0
            for c in classes]
    ax.bar(x + i * width, vals, width, label=q, color=COULEURS.get(q), alpha=0.85)

ax.set_xticks(x + width)
ax.set_xticklabels(classes)
ax.set_ylabel("Energie PMIC (J)")
ax.set_title("Effet de la taille du prompt sur l'énergie (max_tokens=64, Pi5)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("data/pi5_effet_prompt.png", dpi=150)
plt.close()
print("  -> data/pi5_effet_prompt.png")


# ── 6. Joules par token ───────────────────────────────────────────────────
df["j_par_tok"] = df[COL_E] / df["tokens"]
fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(tokens_vals))
width = 0.25
for i, q in enumerate(quantifs):
    vals = [df[(df.quantification == q) & (df.max_tokens == t)]["j_par_tok"].median()
            for t in tokens_vals]
    ax.bar(x + i * width, vals, width, label=q, color=COULEURS.get(q), alpha=0.85)

ax.set_xticks(x + width)
ax.set_xticklabels([f"{t} tokens" for t in tokens_vals])
ax.set_ylabel("J / token (PMIC)")
ax.set_title("Efficacité énergétique : Joules par token générée (Pi5)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("data/pi5_j_par_token.png", dpi=150)
plt.close()
print("  -> data/pi5_j_par_token.png")

print("\nTous les graphiques generes dans data/")
