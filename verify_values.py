import pandas as pd

ll = pd.read_csv("data/raw/resultats_Pi5_2026-06-19_05h16.csv")
qw = pd.read_csv("data/raw/resultats_Pi5_2026-06-24_16h01.csv")
gm = pd.read_csv("data/raw/resultats_Pi5_2026-06-25_15h57.csv")

print("=== Q4_K_M, max_tokens=64 — classement ===")
results = []
for df, nom in [(ll,"Llama-3.2-1B"),(qw,"Qwen2.5-1.5B"),(gm,"Gemma-3-1B")]:
    s = df[(df.quantification=="Q4_K_M") & (df.max_tokens==64)]
    jtok = (s["joules_pmic"]/s["tokens"]).median()
    spd  = (s["tokens"]/s["duree_s"]).median()
    e    = s["joules_pmic"].median()
    results.append((nom, e, jtok, spd))
    print(f"  {nom}: E={e:.1f}J | tok/s={spd:.1f} | J/tok={jtok:.3f}")

results_sorted = sorted(results, key=lambda x: x[2])
print("\n  Classement par J/tok (Q4_K_M):")
for i,(nom,e,jt,sp) in enumerate(results_sorted):
    print(f"    {i+1}. {nom}: {jt:.3f} J/tok")

print()
print("=== Gemma Q3_K_M — config optimale globale ===")
gm_q3 = gm[gm.quantification=="Q3_K_M"]
ll_q4 = ll[ll.quantification=="Q4_K_M"]
qw_q4 = qw[qw.quantification=="Q4_K_M"]
g3_jt = (gm_q3["joules_pmic"]/gm_q3["tokens"]).median()
l4_jt = (ll_q4["joules_pmic"]/ll_q4["tokens"]).median()
q4_jt = (qw_q4["joules_pmic"]/qw_q4["tokens"]).median()
g3_sp = (gm_q3["tokens"]/gm_q3["duree_s"]).median()
l4_sp = (ll_q4["tokens"]/ll_q4["duree_s"]).median()
print(f"  Gemma Q3_K_M : {g3_jt:.3f} J/tok @ {g3_sp:.1f} tok/s")
print(f"  Llama Q4_K_M : {l4_jt:.3f} J/tok @ {l4_sp:.1f} tok/s")
print(f"  Ecart Gemma Q3 vs Llama Q4 : {(g3_jt-l4_jt)/l4_jt*100:.1f}%")
print(f"  Ecart Gemma Q3 vs Qwen  Q4 : {(g3_jt-q4_jt)/q4_jt*100:.1f}%")

print()
print("=== Gemma — pattern quantification ===")
for q in ["Q3_K_M","Q4_K_M","Q8_0"]:
    s = gm[gm.quantification==q]
    jt = (s["joules_pmic"]/s["tokens"]).median()
    sp = (s["tokens"]/s["duree_s"]).median()
    print(f"  Gemma {q}: {jt:.3f} J/tok @ {sp:.1f} tok/s")
