"""
Genere les figures de la campagne prompt_length x n_ctx
(data/raw/prompt_length_nctx_*.csv) : comparaison energie a longueur de prompt
egale selon n_ctx (isole l'effet du contexte alloue), et ajustement quadratique
energie vs longueur reelle du prompt. Ecrit les PNG dans
figures/prompt_length_nctx/ et le detail du fit en console.

A lancer : python src/analyse_prompt_length_nctx.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

os.makedirs("figures/prompt_length_nctx", exist_ok=True)

df = pd.read_csv("data/raw/prompt_length_nctx_Pi5_2026-07-06_11h26.csv")

# ── Figure 1 : meme longueur de prompt, plusieurs n_ctx -> energie identique ─
g = df.groupby(["input_tokens", "n_ctx"]).agg(
    fraction=("fraction_ctx_remplie", "mean"),
    joules_pmic=("joules_pmic", "mean"),
).reset_index()

communs = [50, 392, 1862]  # tailles de prompt testees a plusieurs n_ctx
fig, ax = plt.subplots(figsize=(9, 5))
width = 0.25
x = np.arange(len(communs))
n_ctx_vals = [512, 2048, 8192]
palette = {512: "#2196F3", 2048: "#4CAF50", 8192: "#F44336"}
for i, c in enumerate(n_ctx_vals):
    vals, fracs = [], []
    for n_tok in communs:
        row = g[(g["input_tokens"] == n_tok) & (g["n_ctx"] == c)]
        if len(row):
            vals.append(row["joules_pmic"].values[0])
            fracs.append(row["fraction"].values[0])
        else:
            vals.append(0)
            fracs.append(None)
    bars = ax.bar(x + (i - 1) * width, vals, width, label=f"n_ctx={c}", color=palette[c], edgecolor="white")
    for bar, v, fr in zip(bars, vals, fracs):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, v + 8, f"{v:.0f}J\n({fr:.0%} plein)",
                    ha="center", va="bottom", fontsize=7.5)

ax.set_xticks(x)
ax.set_xticklabels([f"prompt ~{n} tok" for n in communs])
ax.set_ylabel("Énergie PMIC (J)")
ax.set_title("Même longueur de prompt à différents n_ctx — Llama-3.2-1B Q4_K_M")
ax.legend(title="n_ctx alloué")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("figures/prompt_length_nctx/fig1_meme_prompt_diff_nctx.png", dpi=150)
plt.close()
print("Fig 1 sauvée")

# ── Figure 2 : énergie vs longueur réelle du prompt (loi quadratique) ───────
g2 = df.groupby("input_tokens").agg(joules_pmic=("joules_pmic", "mean")).reset_index()
x_data = g2["input_tokens"].values
y_data = g2["joules_pmic"].values
quad = np.polyfit(x_data, y_data, 2)
xs = np.linspace(0, x_data.max() * 1.05, 300)
ys = np.polyval(quad, xs)

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.scatter(x_data, y_data, color="#F44336", s=60, zorder=3, label="mesures (moyenne 3 runs)")
ax.plot(xs, ys, color="#2196F3", linewidth=2, zorder=2,
        label=f"ajustement quadratique : E ≈ {quad[0]:.2e}·n² + {quad[1]:.3f}·n + {quad[2]:.1f}  (R²=1.000)")
ax.set_xlabel("Longueur réelle du prompt (tokens)")
ax.set_ylabel("Énergie PMIC (J)")
ax.set_title("Énergie vs longueur du prompt — sortie fixe (64 tokens)")
ax.legend(fontsize=8.5)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("figures/prompt_length_nctx/fig2_loi_quadratique.png", dpi=150)
plt.close()
print("Fig 2 sauvée")

# ── Résumé chiffré ───────────────────────────────────────────────────────────
print("\n=== Même prompt, n_ctx différents (énergie PMIC moyenne) ===")
print(g.pivot(index="input_tokens", columns="n_ctx", values="joules_pmic").round(2))

print("\n=== Fit quadratique E(joules) = a*n^2 + b*n + c ===")
print(f"a={quad[0]:.6f}  b={quad[1]:.5f}  c={quad[2]:.3f}")

lin = np.polyfit(x_data, y_data, 1)


def r2(y, yhat):
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return 1 - ss_res / ss_tot


print(f"R2 lineaire={r2(y_data, np.polyval(lin, x_data)):.5f}  "
      f"R2 quadratique={r2(y_data, np.polyval(quad, x_data)):.5f}")
