"""
Visualisation complète — présentation tuteurs 25/06/2026
Données : Llama-3.2-1B (19/06) + Qwen2.5-1.5B (24/06) + prompts longs (17/06)
"""

import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0f0f1a",
    "axes.facecolor":   "#0f0f1a",
    "axes.edgecolor":   "#444",
    "axes.labelcolor":  "#ddd",
    "axes.titlecolor":  "white",
    "xtick.color":      "#aaa",
    "ytick.color":      "#aaa",
    "text.color":       "white",
    "grid.color":       "#2a2a3a",
    "grid.linestyle":   "--",
    "grid.alpha":       0.5,
    "legend.facecolor": "#1a1a2e",
    "legend.edgecolor": "#444",
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
})

COL_LLAMA = "#E94F37"   # rouge
COL_QWEN  = "#00B4D8"   # bleu clair
QUANTIFS  = ["Q3_K_L", "Q4_K_M", "Q8_0"]
Q_LABELS  = ["Q3_K_L", "Q4_K_M", "Q8_0"]

# ── Chargement ────────────────────────────────────────────────────────────────
df_llama = pd.read_csv("data/raw/resultats_Pi5_2026-06-19_05h16.csv")
df_qwen  = pd.read_csv("data/raw/resultats_Pi5_2026-06-24_16h01.csv")
df_long  = pd.read_csv("data/raw/prompt_size_Pi5_2026-06-17_11h22.csv")

df_all = pd.concat([df_llama, df_qwen], ignore_index=True)
df_all["tok_s"]     = df_all["tokens"]    / df_all["duree_s"]
df_all["j_par_tok"] = df_all["joules_pmic"] / df_all["tokens"]

# ── Figure : 3×2 = 6 graphiques ───────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("Analyse énergétique LLM sur Raspberry Pi 5  —  LISTIC  |  25/06/2026",
             fontsize=15, fontweight="bold", color="white", y=1.01)
fig.patch.set_facecolor("#0f0f1a")

x   = np.arange(len(QUANTIFS))
w   = 0.35

# ════════════════════════════════════════════════════════════════════════════
# G1 — Énergie médiane par quantif × modèle (max_tokens=64)
# ════════════════════════════════════════════════════════════════════════════
ax = axes[0, 0]
for df, label, col, offset in [
        (df_llama, "Llama-3.2-1B", COL_LLAMA, -w/2),
        (df_qwen,  "Qwen2.5-1.5B", COL_QWEN,  +w/2)]:
    vals = [df[(df.quantification==q) & (df.max_tokens==64)]["joules_pmic"].median()
            for q in QUANTIFS]
    bars = ax.bar(x + offset, vals, w, label=label, color=col, alpha=0.88, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 1, f"{v:.0f} J",
                ha="center", va="bottom", fontsize=9, color="white")

ax.set_xticks(x); ax.set_xticklabels(Q_LABELS)
ax.set_ylabel("Énergie PMIC médiane (J)")
ax.set_title("Énergie par requête\n[max_tokens = 64]")
ax.legend(); ax.grid(axis="y", zorder=0)
ax.set_ylim(0, ax.get_ylim()[1] * 1.15)

# ════════════════════════════════════════════════════════════════════════════
# G2 — J/token par quantif × modèle
# ════════════════════════════════════════════════════════════════════════════
ax = axes[0, 1]
for df, label, col, offset in [
        (df_llama, "Llama-3.2-1B", COL_LLAMA, -w/2),
        (df_qwen,  "Qwen2.5-1.5B", COL_QWEN,  +w/2)]:
    df2 = df.copy(); df2["j_par_tok"] = df2["joules_pmic"] / df2["tokens"]
    vals = [df2[df2.quantification==q]["j_par_tok"].median() for q in QUANTIFS]
    bars = ax.bar(x + offset, vals, w, label=label, color=col, alpha=0.88, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 0.005, f"{v:.2f}",
                ha="center", va="bottom", fontsize=9, color="white")

ax.set_xticks(x); ax.set_xticklabels(Q_LABELS)
ax.set_ylabel("J / token (PMIC)")
ax.set_title("Efficacité énergétique\n[Joules par token généré]")
ax.legend(); ax.grid(axis="y", zorder=0)
ax.set_ylim(0, ax.get_ylim()[1] * 1.15)

# ════════════════════════════════════════════════════════════════════════════
# G3 — Vitesse (tok/s) par quantif × modèle
# ════════════════════════════════════════════════════════════════════════════
ax = axes[0, 2]
for df, label, col, offset in [
        (df_llama, "Llama-3.2-1B", COL_LLAMA, -w/2),
        (df_qwen,  "Qwen2.5-1.5B", COL_QWEN,  +w/2)]:
    df2 = df.copy(); df2["tok_s"] = df2["tokens"] / df2["duree_s"]
    vals = [df2[df2.quantification==q]["tok_s"].median() for q in QUANTIFS]
    bars = ax.bar(x + offset, vals, w, label=label, color=col, alpha=0.88, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 0.1, f"{v:.1f}",
                ha="center", va="bottom", fontsize=9, color="white")

ax.set_xticks(x); ax.set_xticklabels(Q_LABELS)
ax.set_ylabel("Tokens / seconde")
ax.set_title("Vitesse d'inférence\n[tok/s]")
ax.legend(); ax.grid(axis="y", zorder=0)
ax.set_ylim(0, ax.get_ylim()[1] * 1.15)

# ════════════════════════════════════════════════════════════════════════════
# G4 — Loi linéaire E = a + b·tokens (Q4_K_M uniquement)
# ════════════════════════════════════════════════════════════════════════════
ax = axes[1, 0]
for df, label, col in [
        (df_llama, "Llama-3.2-1B", COL_LLAMA),
        (df_qwen,  "Qwen2.5-1.5B", COL_QWEN)]:
    sub = df[df.quantification == "Q4_K_M"]
    ax.scatter(sub["tokens"], sub["joules_pmic"], alpha=0.25, s=15, color=col)
    slope, intercept, r, *_ = stats.linregress(sub["tokens"], sub["joules_pmic"])
    xs = np.linspace(sub["tokens"].min(), sub["tokens"].max(), 100)
    ax.plot(xs, intercept + slope * xs, color=col, linewidth=2,
            label=f"{label}\nE = {intercept:.0f} + {slope:.2f}·tok  (r={r:.3f})")

ax.set_xlabel("Tokens générés")
ax.set_ylabel("Énergie PMIC (J)")
ax.set_title("Loi linéaire E = coût_fixe + α·tokens\n[Q4_K_M]")
ax.legend(fontsize=9); ax.grid(zorder=0)

# ════════════════════════════════════════════════════════════════════════════
# G5 — Surestimation CodeCarbon vs PMIC par modèle × quantif
# ════════════════════════════════════════════════════════════════════════════
ax = axes[1, 1]
for df, label, col, offset in [
        (df_llama, "Llama-3.2-1B", COL_LLAMA, -w/2),
        (df_qwen,  "Qwen2.5-1.5B", COL_QWEN,  +w/2)]:
    vals = []
    for q in QUANTIFS:
        sub = df[df.quantification == q]
        ratio = (sub["joules"].sum() / sub["joules_pmic"].sum() - 1) * 100
        vals.append(ratio)
    bars = ax.bar(x + offset, vals, w, label=label, color=col, alpha=0.88, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 0.3, f"+{v:.0f}%",
                ha="center", va="bottom", fontsize=9, color="white")

ax.axhline(0, color="#666", linewidth=1)
ax.set_xticks(x); ax.set_xticklabels(Q_LABELS)
ax.set_ylabel("Surestimation (%)")
ax.set_title("CodeCarbon vs PMIC\n[surestimation de CodeCarbon]")
ax.legend(); ax.grid(axis="y", zorder=0)
ax.set_ylim(0, ax.get_ylim()[1] * 1.2)

# ════════════════════════════════════════════════════════════════════════════
# G6 — Effet longueur du prompt (prompts longs)
# ════════════════════════════════════════════════════════════════════════════
ax = axes[1, 2]
df_long_m = df_long.groupby("input_tokens")[["joules_pmic", "joules"]].median().reset_index()

ax.scatter(df_long_m["input_tokens"], df_long_m["joules_pmic"],
           color=COL_LLAMA, s=80, zorder=4, label="PMIC (réel)")
ax.plot(df_long_m["input_tokens"], df_long_m["joules_pmic"],
        color=COL_LLAMA, linewidth=2, zorder=3)

ax.scatter(df_long_m["input_tokens"], df_long_m["joules"],
           color=COL_QWEN, s=80, zorder=4, label="CodeCarbon (estimé)", marker="^")
ax.plot(df_long_m["input_tokens"], df_long_m["joules"],
        color=COL_QWEN, linewidth=2, linestyle="--", zorder=3)

ax.set_xlabel("Tokens du prompt (input)")
ax.set_ylabel("Énergie (J)")
ax.set_title("Effet longueur du prompt\n[Llama-3.2-1B Q4_K_M]")
ax.legend(); ax.grid(zorder=0)

# ── Export ────────────────────────────────────────────────────────────────────
plt.tight_layout(pad=2.0)
out = "data/resultats_analyse_25juin.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0f0f1a")
print(f"Sauvegardé : {out}")
plt.show()
