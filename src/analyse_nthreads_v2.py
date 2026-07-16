"""
Genere les figures de la campagne n_threads sur les donnees corrigees du 09/07
(data/raw/resultats_Pi5_2026-07-09_13h58.csv) : energie, efficacite J/tok,
debit, puissance, heatmap, variabilite (coefficient de variation) et
comparaison PMIC vs prise connectee (rendement). Ecrit les PNG dans
figures/nthreads_v2/ et un resume CSV, plus les meilleurs n_threads par modele
en console.

A lancer : python src/analyse_nthreads_v2.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os

os.makedirs("figures/nthreads_v2", exist_ok=True)

df = pd.read_csv("data/raw/resultats_Pi5_2026-07-09_13h58.csv")
df["tok_s"] = df["tokens"] / df["duree_s"]
df["j_par_tok"] = df["joules_pmic"] / df["tokens"]
df["label"] = df["modele"] + " " + df["quantification"]

THREADS = [1, 2, 4]
PALETTE = {"1": "#2196F3", "2": "#4CAF50", "4": "#F44336"}

agg = (
    df.groupby(["modele", "quantification", "n_threads", "label"])
    .agg(
        joules_pmic=("joules_pmic", "mean"),
        joules_pmic_std=("joules_pmic", "std"),
        j_par_tok=("j_par_tok", "mean"),
        j_par_tok_std=("j_par_tok", "std"),
        tok_s=("tok_s", "mean"),
        w_moyen=("w_moyen_pmic", "mean"),
        n=("joules_pmic", "size"),
    )
    .reset_index()
)
agg["cv_j_par_tok"] = agg["j_par_tok_std"] / agg["j_par_tok"]

labels_order = sorted(agg["label"].unique())
x = np.arange(len(labels_order))
width = 0.25

# ── Figure 1 : Énergie totale (J PMIC) ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5))
for i, t in enumerate(THREADS):
    vals = [agg[(agg["label"] == l) & (agg["n_threads"] == t)]["joules_pmic"].values[0]
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"{t} thread{'s' if t > 1 else ''}",
                  color=PALETTE[str(t)], edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                f"{v:.1f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Énergie PMIC (J)")
ax.set_title("Énergie totale par inférence selon n_threads — Pi5 (données corrigées 09/07)")
ax.legend(title="n_threads")
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nthreads_v2/fig1_energie_totale.png", dpi=150)
plt.close()
print("Fig 1 sauvée")

# ── Figure 2 : Efficacité (J/token) ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5))
for i, t in enumerate(THREADS):
    vals = [agg[(agg["label"] == l) & (agg["n_threads"] == t)]["j_par_tok"].values[0]
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"{t} thread{'s' if t > 1 else ''}",
                  color=PALETTE[str(t)], edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                f"{v:.3f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("J / token")
ax.set_title("Efficacité énergétique (J/tok) selon n_threads — Pi5 (données corrigées 09/07)")
ax.legend(title="n_threads")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nthreads_v2/fig2_j_par_tok.png", dpi=150)
plt.close()
print("Fig 2 sauvée")

# ── Figure 3 : Débit (tokens/s) ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5))
for i, t in enumerate(THREADS):
    vals = [agg[(agg["label"] == l) & (agg["n_threads"] == t)]["tok_s"].values[0]
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"{t} thread{'s' if t > 1 else ''}",
                  color=PALETTE[str(t)], edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{v:.1f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Tokens / seconde")
ax.set_title("Débit de génération selon n_threads — Pi5 (données corrigées 09/07)")
ax.legend(title="n_threads")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nthreads_v2/fig3_debit_tok_s.png", dpi=150)
plt.close()
print("Fig 3 sauvée")

# ── Figure 4 : Puissance moyenne (W) ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5))
for i, t in enumerate(THREADS):
    vals = [agg[(agg["label"] == l) & (agg["n_threads"] == t)]["w_moyen"].values[0]
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"{t} thread{'s' if t > 1 else ''}",
                  color=PALETTE[str(t)], edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{v:.2f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Puissance moyenne (W)")
ax.set_title("Puissance PMIC moyenne selon n_threads — Pi5 (données corrigées 09/07)")
ax.legend(title="n_threads")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nthreads_v2/fig4_puissance_w.png", dpi=150)
plt.close()
print("Fig 4 sauvée")

# ── Figure 5 : Heatmap J/tok (modele×threads) ───────────────────────────────
pivot = agg.pivot_table(index="label", columns="n_threads", values="j_par_tok")
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r")
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels([f"{t} thread{'s' if t > 1 else ''}" for t in pivot.columns])
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, fontsize=9)
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        ax.text(j, i, f"{pivot.values[i, j]:.3f}", ha="center", va="center",
                fontsize=9, color="black")
plt.colorbar(im, ax=ax, label="J / token")
ax.set_title("Heatmap efficacité J/tok — n_threads × modèle (données corrigées 09/07)")
fig.tight_layout()
fig.savefig("figures/nthreads_v2/fig5_heatmap_j_tok.png", dpi=150)
plt.close()
print("Fig 5 sauvée")

# ── Figure 6 : Variabilité (coefficient de variation J/tok) ────────────────
fig, ax = plt.subplots(figsize=(13, 5))
for i, t in enumerate(THREADS):
    vals = [agg[(agg["label"] == l) & (agg["n_threads"] == t)]["cv_j_par_tok"].values[0] * 100
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"{t} thread{'s' if t > 1 else ''}",
                  color=PALETTE[str(t)], edgecolor="white", linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Coefficient de variation J/tok (%)")
ax.set_title("Stabilité des mesures selon n_threads — Pi5")
ax.legend(title="n_threads")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nthreads_v2/fig6_variabilite.png", dpi=150)
plt.close()
print("Fig 6 sauvée")

# ── Figure 7 : Rendement PMIC / mur (prise Z-Wave) ──────────────────────────
prise = pd.read_csv("data/raw/resultats_Pi5_2026-07-09_13h58_prise.csv")
prise = prise.sort_values("modele")

fig, ax1 = plt.subplots(figsize=(9, 5))
xp = np.arange(len(prise))
w = 0.35
b1 = ax1.bar(xp - w / 2, prise["somme_J_pmic"], w, label="Énergie PMIC (J)", color="#2196F3")
b2 = ax1.bar(xp + w / 2, prise["energie_mur_marginale_J"], w, label="Énergie mur marginale (J)", color="#FF9800")
ax1.set_xticks(xp)
ax1.set_xticklabels(prise["modele"], fontsize=9)
ax1.set_ylabel("Énergie totale campagne (J)")
ax1.set_title("PMIC vs mesure au mur (prise Z-Wave) — campagne n_threads 09/07")
ax1.legend(loc="upper left")
ax1.grid(axis="y", alpha=0.3)

ax2 = ax1.twinx()
ax2.plot(xp, prise["rendement_pmic_sur_mur_pct"], "o-", color="black", label="Rendement PMIC/mur (%)")
for xi, v in zip(xp, prise["rendement_pmic_sur_mur_pct"]):
    ax2.annotate(f"{v:.1f}%", (xi, v), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)
ax2.set_ylabel("Rendement PMIC / mur (%)")
ax2.set_ylim(0, 100)
ax2.legend(loc="upper right")

fig.tight_layout()
fig.savefig("figures/nthreads_v2/fig7_rendement_pmic_mur.png", dpi=150)
plt.close()
print("Fig 7 sauvée")

print("\n=== Rendement PMIC / mur par modèle (campagne n_threads, prise 13h58) ===")
for _, row in prise.iterrows():
    print(f"{row['modele']:<15} PMIC={row['somme_J_pmic']:.0f} J  "
          f"mur_marginal={row['energie_mur_marginale_J']:.0f} J  "
          f"rendement={row['rendement_pmic_sur_mur_pct']:.1f}%  "
          f"W_moyen_mur={row['puissance_moyenne_mur_W']:.2f}")
print("Note: fichier resultats_Pi5_2026-07-09_12h48_prise.csv exclu (kwh_debut==kwh_fin, mesure invalide).")

# ── Tableau résumé + meilleur n_threads par modèle ──────────────────────────
summary = agg.sort_values(["label", "n_threads"])
summary.to_csv("figures/nthreads_v2/resume_nthreads.csv", index=False)
print("Résumé sauvé -> figures/nthreads_v2/resume_nthreads.csv")

print("\n=== Meilleur n_threads par modèle (min J/tok) ===")
best = agg.loc[agg.groupby("label")["j_par_tok"].idxmin()]
for _, row in best.iterrows():
    print(f"{row['label']:<22} -> n_threads={int(row['n_threads'])}  "
          f"{row['j_par_tok']:.3f} J/tok  ({row['tok_s']:.1f} tok/s)")

print("\n=== Gain/perte energie 1 -> 4 threads (%) ===")
for l in labels_order:
    v1 = agg[(agg["label"] == l) & (agg["n_threads"] == 1)]["j_par_tok"].values[0]
    v4 = agg[(agg["label"] == l) & (agg["n_threads"] == 4)]["j_par_tok"].values[0]
    delta = (v4 - v1) / v1 * 100
    print(f"{l:<22} {v1:.3f} -> {v4:.3f} J/tok  ({delta:+.1f}%)")

print("\nToutes figures dans figures/nthreads_v2/")
