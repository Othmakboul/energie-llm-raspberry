import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os

os.makedirs("figures/nthreads", exist_ok=True)

df = pd.read_csv("data/raw/nthreads_Pi5_2026-07-03_12h13.csv")
df["tok_s"] = df["tokens"] / df["duree_s"]
df["j_par_tok"] = df["joules_pmic"] / df["tokens"]
df["label"] = df["modele"] + " " + df["quantification"]

THREADS = [1, 2, 4]
PALETTE = {"1": "#2196F3", "2": "#4CAF50", "4": "#F44336"}

agg = (
    df.groupby(["modele", "quantification", "n_threads", "label"])
    .agg(
        joules_pmic=("joules_pmic", "mean"),
        j_par_tok=("j_par_tok", "mean"),
        tok_s=("tok_s", "mean"),
        w_moyen=("w_moyen_pmic", "mean"),
    )
    .reset_index()
)

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
ax.set_title("Énergie totale par inférence selon n_threads — Pi5")
ax.legend(title="n_threads")
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nthreads/fig1_energie_totale.png", dpi=150)
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
ax.set_title("Efficacité énergétique (J/tok) selon n_threads — Pi5")
ax.legend(title="n_threads")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nthreads/fig2_j_par_tok.png", dpi=150)
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
ax.set_title("Débit de génération selon n_threads — Pi5")
ax.legend(title="n_threads")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nthreads/fig3_debit_tok_s.png", dpi=150)
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
ax.set_title("Puissance PMIC moyenne selon n_threads — Pi5")
ax.legend(title="n_threads")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nthreads/fig4_puissance_w.png", dpi=150)
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
ax.set_title("Heatmap efficacité J/tok — n_threads × modèle")
fig.tight_layout()
fig.savefig("figures/nthreads/fig5_heatmap_j_tok.png", dpi=150)
plt.close()
print("Fig 5 sauvée")

print("\nToutes figures dans figures/nthreads/")
