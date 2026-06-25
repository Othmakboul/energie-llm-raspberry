"""Génère 4 figures haute qualité — 3 modèles complets — 25/06/2026."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

BG    = "#0f0f1a"; PANEL = "#16162a"
RED   = "#E94F37"; BLUE  = "#00B4D8"; GREEN = "#2ECC71"
GOLD  = "#F4D03F"; PURP  = "#9B59B6"; WHITE = "#FFFFFF"; GREY  = "#888899"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": PANEL,
    "axes.edgecolor": "#333", "axes.labelcolor": "#ccc",
    "axes.titlecolor": WHITE, "xtick.color": GREY, "ytick.color": GREY,
    "text.color": WHITE, "grid.color": "#222233", "grid.linestyle": "--",
    "grid.alpha": 0.6, "legend.facecolor": "#1a1a2e", "legend.edgecolor": "#333",
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
})

ll = pd.read_csv("data/raw/resultats_Pi5_2026-06-19_05h16.csv")
qw = pd.read_csv("data/raw/resultats_Pi5_2026-06-24_16h01.csv")
gm = pd.read_csv("data/raw/resultats_Pi5_2026-06-25_15h57.csv")
pl = pd.read_csv("data/raw/prompt_size_Pi5_2026-06-17_11h22.csv")

MODELES = [
    (ll, "Llama-3.2-1B", RED,  ["Q3_K_L","Q4_K_M","Q8_0"]),
    (qw, "Qwen2.5-1.5B", BLUE, ["Q3_K_L","Q4_K_M","Q8_0"]),
    (gm, "Gemma-3-1B",   PURP, ["Q3_K_M","Q4_K_M","Q8_0"]),
]

# ════════════════════════════════════════════════════════════════════════
# FIG 1 — Comparaison 3 modèles : J/tok, tok/s, énergie (Q4_K_M)
# ════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))
fig.patch.set_facecolor(BG)
fig.suptitle("Comparaison 3 architectures — Llama / Qwen / Gemma  [Q4_K_M]",
             fontsize=14, fontweight="bold", color=WHITE, y=1.02)

metrics = [
    ("joules_pmic", "Énergie médiane (J) [max_tokens=64]", "J"),
    ("j_tok",       "Joules / token  [efficacité énergie]", "J/tok"),
    ("tok_s",       "Vitesse  [tokens/seconde]",            "tok/s"),
]
noms  = ["Llama-3.2-1B", "Qwen2.5-1.5B", "Gemma-3-1B"]
cols  = [RED, BLUE, PURP]
x     = np.arange(3)

for ax, (met, title, unit) in zip(axes, metrics):
    ax.set_facecolor(PANEL)
    vals = []
    for df, nom, col, qs in MODELES:
        df = df.copy()
        df["tok_s"] = df["tokens"]/df["duree_s"]
        df["j_tok"] = df["joules_pmic"]/df["tokens"]
        s = df[(df["quantification"]=="Q4_K_M") & (df["max_tokens"]==64)]
        vals.append(s[met].median())
    bars = ax.bar(x, vals, 0.55, color=cols, alpha=0.88, zorder=3,
                  edgecolor="#333", linewidth=0.5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+v*0.02,
                f"{v:.2f}" if v<2 else f"{v:.1f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold", color=WHITE)
    ax.set_xticks(x); ax.set_xticklabels(noms, fontsize=10)
    ax.set_title(title); ax.set_ylabel(unit)
    ax.grid(axis="y", zorder=0)
    ax.set_ylim(0, max(vals)*1.22)

plt.tight_layout()
plt.savefig("data/fig1_3modeles_q4.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(); print("fig1 OK")

# ════════════════════════════════════════════════════════════════════════
# FIG 2 — J/tok par quantification × modèle (heatmap + bars)
# ════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))
fig.patch.set_facecolor(BG)
fig.suptitle("Efficacité énergétique (J/token) par quantification × modèle",
             fontsize=14, fontweight="bold", color=WHITE, y=1.02)

for ax, (df, nom, col, qs) in zip(axes, MODELES):
    ax.set_facecolor(PANEL)
    df = df.copy()
    df["j_tok"] = df["joules_pmic"]/df["tokens"]
    df["tok_s"] = df["tokens"]/df["duree_s"]
    jtoks  = [df[df.quantification==q]["j_tok"].median()  for q in qs]
    speeds = [df[df.quantification==q]["tok_s"].median()  for q in qs]
    best   = jtoks.index(min(jtoks))
    bar_cols = [GREEN if i==best else col for i in range(len(qs))]
    bars = ax.bar(qs, jtoks, color=bar_cols, alpha=0.88, zorder=3,
                  edgecolor="#333", linewidth=0.5)
    for b, v, sp in zip(bars, jtoks, speeds):
        ax.text(b.get_x()+b.get_width()/2, v+0.005,
                f"{v:.3f} J/tok\n{sp:.1f} tok/s",
                ha="center", va="bottom", fontsize=10, color=WHITE, fontweight="bold")
    if best == 0:
        ax.annotate("★ BEST", (best, jtoks[best]), textcoords="offset points",
                    xytext=(0, 35), ha="center", fontsize=12, color=GREEN, fontweight="bold")
    ax.set_title(nom, color=col, fontsize=14)
    ax.set_ylabel("J / token (PMIC)")
    ax.set_ylim(0, max(jtoks)*1.35)
    ax.grid(axis="y", zorder=0)

plt.tight_layout()
plt.savefig("data/fig2_jtok_par_quantif.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(); print("fig2 OK")

# ════════════════════════════════════════════════════════════════════════
# FIG 3 — Loi linéaire Q4_K_M 3 modèles + scatter speed vs jtok
# ════════════════════════════════════════════════════════════════════════
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))
fig.patch.set_facecolor(BG)
fig.suptitle("Loi linéaire & Carte efficacité — 3 modèles × 3 quantifications",
             fontsize=14, fontweight="bold", color=WHITE, y=1.02)

# Loi linéaire Q4 uniquement
ax1.set_facecolor(PANEL)
for df, nom, col, qs in MODELES:
    sub = df[df.quantification=="Q4_K_M"].copy()
    ax1.scatter(sub["tokens"], sub["joules_pmic"], alpha=0.12, s=10, color=col)
    sl, ic, r, *_ = stats.linregress(sub["tokens"], sub["joules_pmic"])
    xs = np.linspace(sub["tokens"].min(), sub["tokens"].max(), 200)
    ax1.plot(xs, ic+sl*xs, color=col, lw=2.5,
             label=f"{nom}\nE={ic:.1f}+{sl:.3f}·tok  r={r:.4f}")
ax1.set_xlabel("Tokens générés"); ax1.set_ylabel("Énergie PMIC (J)")
ax1.set_title("Loi linéaire — Q4_K_M")
ax1.legend(fontsize=9); ax1.grid(True)

# Carte efficacité : vitesse vs J/tok pour TOUTES les configs
ax2.set_facecolor(PANEL)
q_markers = {"Q3_K_L": "o", "Q3_K_M": "o", "Q4_K_M": "s", "Q8_0": "^"}
q_labels  = {"Q3_K_L": "Q3_K_L", "Q3_K_M": "Q3_K_M", "Q4_K_M": "Q4_K_M", "Q8_0": "Q8_0"}

plotted_q = set()
for df, nom, col, qs in MODELES:
    df = df.copy()
    df["j_tok"] = df["joules_pmic"]/df["tokens"]
    df["tok_s"] = df["tokens"]/df["duree_s"]
    for q in qs:
        sub = df[df.quantification==q]
        mk = q_markers.get(q, "o")
        jt = sub["j_tok"].median(); sp = sub["tok_s"].median()
        label_q = q_labels[q] if q not in plotted_q else ""
        ax2.scatter(sp, jt, s=200, color=col, marker=mk, zorder=5,
                    edgecolors="white", lw=1.2)
        ax2.annotate(f"{nom[:5]}\n{q}", (sp, jt),
                     textcoords="offset points", xytext=(6, 4),
                     fontsize=8, color=col)
        plotted_q.add(q)

# Gemma Q3 champion
gm2 = gm.copy()
gm2["j_tok"] = gm2["joules_pmic"]/gm2["tokens"]
gm2["tok_s"] = gm2["tokens"]/gm2["duree_s"]
sub_champ = gm2[gm2.quantification=="Q3_K_M"]
ax2.annotate("★ OPTIMAL\nGemma Q3",
             xy=(sub_champ["tok_s"].median(), sub_champ["j_tok"].median()),
             xytext=(sub_champ["tok_s"].median()+1.5, sub_champ["j_tok"].median()+0.03),
             arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5),
             color=GREEN, fontsize=11, fontweight="bold")

ax2.set_xlabel("Vitesse (tok/s)  →  plus rapide = mieux")
ax2.set_ylabel("J / token  →  plus bas = mieux")
ax2.set_title("Carte efficacité — toutes configurations")
ax2.grid(True)

# Légende couleurs modèles
for nom, col in [("Llama",RED),("Qwen",BLUE),("Gemma",PURP)]:
    ax2.scatter([],[], color=col, s=80, label=nom)
ax2.legend(fontsize=9)

plt.tight_layout()
plt.savefig("data/fig3_lineaire_et_carte.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(); print("fig3 OK")

# ════════════════════════════════════════════════════════════════════════
# FIG 4 — Prompts longs + CodeCarbon surestimation 3 modèles
# ════════════════════════════════════════════════════════════════════════
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))
fig.patch.set_facecolor(BG)
fig.suptitle("Prompts longs & Fiabilité CodeCarbon vs PMIC — 3 modèles",
             fontsize=14, fontweight="bold", color=WHITE, y=1.02)

# Prompts longs
ax1.set_facecolor(PANEL)
g = pl.groupby("input_tokens")[["joules_pmic","joules"]].median()
ax1.plot(g.index, g["joules_pmic"], "o-", color=RED, lw=2.5, ms=8, label="PMIC (réel)", zorder=4)
ax1.plot(g.index, g["joules"],     "^--", color=BLUE, lw=2,   ms=8, label="CodeCarbon (estimé)", zorder=4)
sl, ic, r, *_ = stats.linregress(pl["input_tokens"], pl["joules_pmic"])
xs = np.linspace(pl["input_tokens"].min(), pl["input_tokens"].max(), 200)
ax1.plot(xs, ic+sl*xs, color=RED, lw=1, alpha=0.4, linestyle=":")
for it, jp in zip(g.index, g["joules_pmic"]):
    if it in [126, 1004, 4012]:
        ax1.annotate(f"{jp:.0f} J", (it, jp), textcoords="offset points",
                     xytext=(8, 6), fontsize=9, color=RED, fontweight="bold")
ax1.annotate("×16\n126→4012 tok", xy=(4012, g.loc[4012,"joules_pmic"]),
             xytext=(2600, 420), arrowprops=dict(arrowstyle="->", color=GOLD),
             color=GOLD, fontsize=11, fontweight="bold")
ax1.set_xlabel("Tokens du prompt (input)")
ax1.set_ylabel("Énergie (J)")
ax1.set_title(f"Effet longueur du prompt [Llama Q4]\nE = {ic:.0f} + {sl:.3f}·input_tok  (r={r:.4f})")
ax1.legend(); ax1.grid(True)

# CodeCarbon surestimation 3 modèles × quantif
ax2.set_facecolor(PANEL)
all_df = pd.concat([ll, qw, gm])
group_cols = ["modele","quantification"]
rats = all_df.groupby(group_cols).apply(
    lambda s: (s["joules"].sum()/s["joules_pmic"].sum()-1)*100
).reset_index(name="pct")

mod_order = ["Llama-3.2-1B","Qwen2.5-1.5B","Gemma-3-1B"]
mod_cols  = [RED, BLUE, PURP]
n_q = 3
xbase = np.arange(n_q)

for mi, (mod, col) in enumerate(zip(mod_order, mod_cols)):
    sub = rats[rats["modele"]==mod].sort_values("quantification")
    xpos = xbase + mi*(n_q + 0.6)
    bars = ax2.bar(xpos, sub["pct"].values, 0.6, color=col, alpha=0.85, zorder=3, label=mod)
    for b, v in zip(bars, sub["pct"].values):
        ax2.text(b.get_x()+b.get_width()/2, v+0.3, f"+{v:.0f}%",
                 ha="center", va="bottom", fontsize=9, fontweight="bold", color=WHITE)
    xticks_pos  = list(xbase) + list(xbase+n_q+0.6) + list(xbase+2*(n_q+0.6))
    xticks_lab  = [q.replace("Q3_K_L","Q3").replace("Q3_K_M","Q3").replace("Q4_K_M","Q4").replace("Q8_0","Q8")
                   for q in sorted(ll["quantification"].unique())] * 3
    ax2.set_xticks(xticks_pos); ax2.set_xticklabels(xticks_lab, fontsize=9)

for mi, (mod, col) in enumerate(zip(mod_order, mod_cols)):
    ax2.text(n_q//2 + mi*(n_q+0.6) - 0.3, ax2.get_ylim()[1]*0.92,
             mod.split("-")[0], color=col, fontsize=11, fontweight="bold", ha="center")

ax2.set_ylabel("Surestimation CodeCarbon vs PMIC (%)")
ax2.set_title("CodeCarbon surestime systématiquement\n[RAPL absent sur ARM → estimation par TDP]")
ax2.grid(axis="y", zorder=0); ax2.legend(fontsize=9)

plt.tight_layout()
plt.savefig("data/fig4_prompts_et_cc.png", dpi=150, bbox_inches="tight", facecolor=BG)
plt.close(); print("fig4 OK")
print("\nTous les graphiques mis à jour dans data/")
