import pandas as pd
import numpy as np
from scipy import stats

files = {
    "Llama S1 (15/06)": "data/raw/resultats_Pi5_2026-06-15_14h45.csv",
    "Llama (19/06)":     "data/raw/resultats_Pi5_2026-06-19_05h16.csv",
    "Qwen (24/06)":      "data/raw/resultats_Pi5_2026-06-24_16h01.csv",
    "Gemma-3-1B (25/06)":"data/raw/resultats_Pi5_2026-06-25_15h57.csv",
    "Prompts longs":     "data/raw/prompt_size_Pi5_2026-06-17_11h22.csv",
}

for name, f in files.items():
    df = pd.read_csv(f)
    print(f"\n{'='*55}")
    print(f"  {name}  ({len(df)} mesures)")
    print(f"{'='*55}")

    if "quantification" in df.columns and "tokens" in df.columns:
        df["tok_s"]  = df["tokens"] / df["duree_s"]
        df["j_tok"]  = df["joules_pmic"] / df["tokens"]
        df["cc_sur"] = (df["joules"] / df["joules_pmic"] - 1) * 100

        for q in sorted(df["quantification"].unique()):
            s = df[df["quantification"] == q]
            print(f"\n  [{q}]")
            print(f"    Energie PMIC mediane : {s['joules_pmic'].median():.1f} J (toutes configs)")
            print(f"    Vitesse              : {s['tok_s'].median():.1f} tok/s")
            print(f"    J/token              : {s['j_tok'].median():.3f} J/tok")
            print(f"    CodeCarbon surestime : +{s['cc_sur'].median():.1f}%")

            # Loi lineaire
            slope, intercept, r, _, _ = stats.linregress(s["tokens"], s["joules_pmic"])
            print(f"    Loi lineaire PMIC    : E = {intercept:.1f} + {slope:.3f} x tokens  (r={r:.4f})")

        # Puissance moyenne
        print(f"\n  Puissance moyenne PMIC par quantif :")
        print(df.groupby("quantification")["w_moyen_pmic"].median().round(2).to_string())

        # Effet taille prompt
        if "classe" in df.columns:
            print(f"\n  Effet classe de prompt (max_tokens=64) :")
            sub64 = df[df["max_tokens"] == 64]
            print(sub64.pivot_table(index="quantification", columns="classe",
                                    values="joules_pmic", aggfunc="median").round(1).to_string())

    elif "input_tokens" in df.columns:
        print("\n  Energie PMIC par taille de prompt (input_tokens) :")
        g = df.groupby("input_tokens")[["joules_pmic", "joules"]].median().round(1)
        print(g.to_string())
        slope, intercept, r, _, _ = stats.linregress(df["input_tokens"], df["joules_pmic"])
        print(f"\n  Loi lineaire PMIC : E = {intercept:.1f} + {slope:.4f} x input_tokens  (r={r:.4f})")

print("\n" + "="*55)
print("  COMPARAISON FINALE 3 modèles (Q4_K_M, 64 tokens)")
print("="*55)
ll = pd.read_csv("data/raw/resultats_Pi5_2026-06-19_05h16.csv")
qw = pd.read_csv("data/raw/resultats_Pi5_2026-06-24_16h01.csv")
gm = pd.read_csv("data/raw/resultats_Pi5_2026-06-25_15h57.csv")
for df, nom in [(ll, "Llama-3.2-1B"), (qw, "Qwen2.5-1.5B"), (gm, "Gemma-3-1B")]:
    s = df[(df["quantification"] == "Q4_K_M") & (df["max_tokens"] == 64)]
    print(f"  {nom:15s}: E={s['joules_pmic'].median():.1f}J | "
          f"tok/s={(s['tokens']/s['duree_s']).median():.1f} | "
          f"J/tok={(s['joules_pmic']/s['tokens']).median():.3f}")
