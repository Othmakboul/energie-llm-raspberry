import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os

os.makedirs("figures/nctx", exist_ok=True)

df = pd.read_csv("data/raw/nctx_Pi5_2026-07-05_06h32.csv")
df["tok_s"] = df["tokens"] / df["duree_s"]
df["j_par_tok"] = df["joules_pmic"] / df["tokens"]
df["label"] = df["modele"] + " " + df["quantification"]

CTX = [512, 2048, 8192]
PALETTE = {"512": "#2196F3", "2048": "#4CAF50", "8192": "#F44336"}

agg = (
    df.groupby(["modele", "quantification", "n_ctx", "label"])
    .agg(
        joules_pmic=("joules_pmic", "mean"),
        j_par_tok=("j_par_tok", "mean"),
        tok_s=("tok_s", "mean"),
        w_moyen=("w_moyen_pmic", "mean"),
        duree_s=("duree_s", "mean"),
    )
    .reset_index()
)

labels_order = sorted(agg["label"].unique())
x = np.arange(len(labels_order))
width = 0.25

# ── Figure 1 : Énergie totale (J PMIC) ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5))
for i, c in enumerate(CTX):
    vals = [agg[(agg["label"] == l) & (agg["n_ctx"] == c)]["joules_pmic"].values[0]
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"n_ctx={c}",
                  color=PALETTE[str(c)], edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                f"{v:.1f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Énergie PMIC (J)")
ax.set_title("Énergie totale par inférence selon n_ctx — Pi5")
ax.legend(title="n_ctx")
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nctx/fig1_energie_totale.png", dpi=150)
plt.close()
print("Fig 1 sauvée")

# ── Figure 2 : Efficacité (J/token) ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5))
for i, c in enumerate(CTX):
    vals = [agg[(agg["label"] == l) & (agg["n_ctx"] == c)]["j_par_tok"].values[0]
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"n_ctx={c}",
                  color=PALETTE[str(c)], edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                f"{v:.3f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("J / token")
ax.set_title("Efficacité énergétique (J/tok) selon n_ctx — Pi5")
ax.legend(title="n_ctx")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nctx/fig2_j_par_tok.png", dpi=150)
plt.close()
print("Fig 2 sauvée")

# ── Figure 3 : Débit (tokens/s) ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5))
for i, c in enumerate(CTX):
    vals = [agg[(agg["label"] == l) & (agg["n_ctx"] == c)]["tok_s"].values[0]
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"n_ctx={c}",
                  color=PALETTE[str(c)], edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f"{v:.1f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Tokens / seconde")
ax.set_title("Débit de génération selon n_ctx — Pi5")
ax.legend(title="n_ctx")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nctx/fig3_debit_tok_s.png", dpi=150)
plt.close()
print("Fig 3 sauvée")

# ── Figure 4 : Puissance moyenne (W) ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5))
for i, c in enumerate(CTX):
    vals = [agg[(agg["label"] == l) & (agg["n_ctx"] == c)]["w_moyen"].values[0]
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"n_ctx={c}",
                  color=PALETTE[str(c)], edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{v:.2f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Puissance moyenne (W)")
ax.set_title("Puissance PMIC moyenne selon n_ctx — Pi5")
ax.legend(title="n_ctx")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nctx/fig4_puissance_w.png", dpi=150)
plt.close()
print("Fig 4 sauvée")

# ── Figure 5 : Heatmap J/tok (modele×n_ctx) ─────────────────────────────────
pivot = agg.pivot_table(index="label", columns="n_ctx", values="j_par_tok")
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r")
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels([f"n_ctx={c}" for c in pivot.columns])
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, fontsize=9)
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        ax.text(j, i, f"{pivot.values[i, j]:.3f}", ha="center", va="center",
                fontsize=9, color="black")
plt.colorbar(im, ax=ax, label="J / token")
ax.set_title("Heatmap efficacité J/tok — n_ctx × modèle")
fig.tight_layout()
fig.savefig("figures/nctx/fig5_heatmap_j_tok.png", dpi=150)
plt.close()
print("Fig 5 sauvée")

# ── Figure 6 : Durée moyenne (s) selon n_ctx (temps de chargement/alloc KV) ─
fig, ax = plt.subplots(figsize=(13, 5))
for i, c in enumerate(CTX):
    vals = [agg[(agg["label"] == l) & (agg["n_ctx"] == c)]["duree_s"].values[0]
            for l in labels_order]
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"n_ctx={c}",
                  color=PALETTE[str(c)], edgecolor="white", linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{v:.2f}", ha="center", va="bottom", fontsize=7)

ax.set_xticks(x)
ax.set_xticklabels(labels_order, rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Durée moyenne (s)")
ax.set_title("Durée d'inférence selon n_ctx — Pi5")
ax.legend(title="n_ctx")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/nctx/fig6_duree_s.png", dpi=150)
plt.close()
print("Fig 6 sauvée")

print("\nToutes figures dans figures/nctx/")

# ── Résumé chiffré (stdout) pour le rapport ─────────────────────────────────
print("\n=== Résumé global (moyennes tous modèles) ===")
glob = df.groupby("n_ctx").agg(
    joules_pmic=("joules_pmic", "mean"),
    j_par_tok=("j_par_tok", "mean"),
    tok_s=("tok_s", "mean"),
    w_moyen=("w_moyen_pmic", "mean"),
    duree_s=("duree_s", "mean"),
).round(3)
print(glob)

base = glob.loc[512]
top = glob.loc[8192]
print("\nVariation 512 -> 8192 :")
for col in glob.columns:
    delta = (top[col] - base[col]) / base[col] * 100
    print(f"  {col}: {delta:+.1f}%")
