import json
import base64
import os

IMG_JSON = r"C:\Users\Amine\AppData\Local\Temp\claude\C--Users-Amine-Desktop-amiine-Rasbery-Pi\77e4c6d5-b563-4ec8-ab99-8b3d95143c5c\scratchpad\imgs.json"
OUT = r"C:\Users\Amine\AppData\Local\Temp\claude\C--Users-Amine-Desktop-amiine-Rasbery-Pi\77e4c6d5-b563-4ec8-ab99-8b3d95143c5c\scratchpad\rapport_nctx_nthreads.html"

with open(IMG_JSON, encoding="utf-8") as f:
    imgs_raw = json.load(f)
imgs = {k.replace("\\", "/"): v for k, v in imgs_raw.items()}


def img(path, alt):
    b64 = imgs[path.replace("\\", "/")]
    return f'<img src="data:image/png;base64,{b64}" alt="{alt}" style="max-width:100%;border-radius:8px;margin:12px 0;">'


html = f"""
<title>Analyse énergétique — n_ctx & n_threads (Pi5)</title>
<style>
:root {{ --bg:#0f1115; --panel:#171a21; --text:#e8eaed; --muted:#9aa4b2; --accent:#4CAF50; --accent2:#F44336; --border:#2a2f3a; }}
@media (prefers-color-scheme: light) {{
  :root {{ --bg:#f7f8fa; --panel:#ffffff; --text:#1a1d23; --muted:#5b6472; --border:#e2e5ea; }}
}}
:root[data-theme="light"] {{ --bg:#f7f8fa; --panel:#ffffff; --text:#1a1d23; --muted:#5b6472; --border:#e2e5ea; }}
:root[data-theme="dark"] {{ --bg:#0f1115; --panel:#171a21; --text:#e8eaed; --muted:#9aa4b2; --border:#2a2f3a; }}
* {{ box-sizing:border-box; }}
body {{ background:var(--bg); color:var(--text); font-family:-apple-system,Segoe UI,Roboto,sans-serif; line-height:1.55; max-width:1100px; margin:0 auto; padding:32px 20px 80px; }}
h1 {{ font-size:1.9rem; margin-bottom:4px; }}
h2 {{ margin-top:48px; border-bottom:2px solid var(--border); padding-bottom:8px; font-size:1.4rem; }}
h3 {{ margin-top:28px; font-size:1.1rem; color:var(--accent); }}
.subtitle {{ color:var(--muted); margin-top:0; margin-bottom:24px; }}
.card {{ background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:20px 24px; margin:16px 0; }}
.kpi-row {{ display:flex; gap:14px; flex-wrap:wrap; margin:18px 0; }}
.kpi {{ background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:14px 18px; flex:1; min-width:150px; }}
.kpi .val {{ font-size:1.5rem; font-weight:700; }}
.kpi .lbl {{ color:var(--muted); font-size:0.82rem; }}
.pos {{ color:var(--accent2); }}
.neg {{ color:var(--accent); }}
table {{ border-collapse:collapse; width:100%; margin:12px 0; font-size:0.92rem; }}
th, td {{ border:1px solid var(--border); padding:6px 10px; text-align:right; }}
th:first-child, td:first-child {{ text-align:left; }}
th {{ background:rgba(128,128,128,0.08); }}
.tag {{ display:inline-block; background:rgba(128,128,128,0.15); border-radius:6px; padding:2px 8px; font-size:0.78rem; margin-right:6px; }}
.callout {{ border-left:4px solid var(--accent); padding:10px 16px; background:rgba(76,175,80,0.08); border-radius:0 8px 8px 0; margin:16px 0; }}
.callout.warn {{ border-left-color:var(--accent2); background:rgba(244,67,54,0.08); }}
code {{ background:rgba(128,128,128,0.15); padding:1px 5px; border-radius:4px; font-size:0.9em; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
@media (max-width:800px) {{ .grid2 {{ grid-template-columns:1fr; }} }}
footer {{ margin-top:60px; color:var(--muted); font-size:0.82rem; border-top:1px solid var(--border); padding-top:16px; }}
</style>

<h1>Analyse énergétique — Raspberry Pi 5</h1>
<p class="subtitle">Impact de <code>n_ctx</code> et <code>n_threads</code> sur la consommation d'énergie des LLM légers quantifiés &nbsp;·&nbsp; 3 modèles × 3 quantifications × 3 valeurs &nbsp;·&nbsp; mesure PMIC + CodeCarbon &nbsp;·&nbsp; 2026-07-05/03</p>

<div class="card">
<strong>Verdict en une phrase :</strong> <code>n_ctx</code> a un effet <strong>quasi-nul</strong> sur l'énergie (+1 à +2% de 512 à 8192) tant que le prompt ne remplit pas le contexte, alors que <code>n_threads</code> a un effet <strong>fort mais non-monotone</strong> : plus de threads = plus rapide mais aussi plus de puissance instantanée, donc le gain énergétique dépend beaucoup de la quantification du modèle.
</div>

<h2>1. Analyse approfondie — <code>n_ctx</code></h2>

<p>Campagne : 9 configurations modèle×quant, <code>n_ctx</code> ∈ {{512, 2048, 8192}}, <code>max_tokens</code> ∈ {{16, 64, 256}}, 3 répétitions, prompts courts/moyens/longs. <code>n_threads</code> fixé à 4 pour isoler l'effet de <code>n_ctx</code>. Total : 19 197 mesures.</p>

<div class="kpi-row">
<div class="kpi"><div class="val">+1.1%</div><div class="lbl">énergie PMIC moyenne (512→8192)</div></div>
<div class="kpi"><div class="val">+1.1%</div><div class="lbl">J/token (512→8192)</div></div>
<div class="kpi"><div class="val neg">-1.5%</div><div class="lbl">débit tok/s (512→8192)</div></div>
<div class="kpi"><div class="val">+1.4%</div><div class="lbl">durée d'inférence (512→8192)</div></div>
</div>

<h3>1.1 Pourquoi un effet aussi faible ?</h3>
<p>Le paramètre <code>n_ctx</code> fixe la taille <em>maximale</em> du buffer KV-cache alloué au démarrage du modèle — il ne correspond pas à la taille réellement utilisée par le prompt. Nos prompts de test (29 à quelques centaines de caractères) restent très en-dessous de 512 tokens : le calcul d'attention porte donc sur le même nombre de tokens réels quel que soit <code>n_ctx</code>. Le petit surcoût observé (~1-2%) vient uniquement de :</p>
<ul>
<li><strong>l'allocation mémoire du buffer KV</strong> (plus grand buffer = plus de RAM à réserver/initialiser au chargement du modèle),</li>
<li><strong>un léger surcoût d'indexation/masquage d'attention</strong> même sur un contexte partiellement rempli.</li>
</ul>

<div class="callout">
Ce résultat est <strong>attendu et cohérent</strong> avec le fonctionnement de llama.cpp : <code>n_ctx</code> n'a d'impact fort sur le calcul (et donc l'énergie) que lorsque le contexte réellement utilisé (prompt + génération) approche la valeur de <code>n_ctx</code> — ce qui n'est pas notre cas ici avec des réponses de 16 à 256 tokens.
</div>

<h3>1.2 L'effet est monotone et reproductible sur les 9 configurations</h3>
<p>Le tableau ci-dessous confirme que l'énergie PMIC moyenne augmente <strong>systématiquement</strong> avec <code>n_ctx</code>, pour chacun des 9 couples modèle×quantification — la tendance n'est pas du bruit de mesure, mais son amplitude est négligeable en pratique (≤1.3 J sur ~40-80 J).</p>

<div style="overflow-x:auto">
<table>
<tr><th>Modèle / quant</th><th>n_ctx=512 (J)</th><th>n_ctx=2048 (J)</th><th>n_ctx=8192 (J)</th><th>Δ 512→8192</th></tr>
<tr><td>Gemma-3-1B Q3_K_M</td><td>38.49</td><td>39.04</td><td>39.27</td><td>+2.0%</td></tr>
<tr><td>Gemma-3-1B Q4_K_M</td><td>48.53</td><td>48.78</td><td>49.00</td><td>+1.0%</td></tr>
<tr><td>Gemma-3-1B Q8_0</td><td>57.79</td><td>58.09</td><td>58.34</td><td>+0.9%</td></tr>
<tr><td>Llama-3.2-1B Q3_K_L</td><td>52.43</td><td>53.29</td><td>53.45</td><td>+2.0%</td></tr>
<tr><td>Llama-3.2-1B Q4_K_M</td><td>48.26</td><td>48.62</td><td>48.92</td><td>+1.4%</td></tr>
<tr><td>Llama-3.2-1B Q8_0</td><td>68.21</td><td>68.42</td><td>69.03</td><td>+1.2%</td></tr>
<tr><td>Qwen2.5-1.5B Q3_K_L</td><td>67.13</td><td>67.21</td><td>67.28</td><td>+0.2%</td></tr>
<tr><td>Qwen2.5-1.5B Q4_K_M</td><td>55.74</td><td>56.08</td><td>56.37</td><td>+1.1%</td></tr>
<tr><td>Qwen2.5-1.5B Q8_0</td><td>82.02</td><td>82.43</td><td>82.63</td><td>+0.7%</td></tr>
</table>
</div>

<h3>1.3 L'effet ne dépend pas non plus de la longueur de génération</h3>
<p>Même en croisant avec <code>max_tokens</code> (16/64/256), l'écart 512→8192 reste de l'ordre de +0.9% quel que soit le nombre de tokens générés — preuve que le surcoût est bien lié à l'<em>allocation</em> du contexte (fixe, payée une fois au chargement) et non au <em>calcul</em> par token généré :</p>

<div style="overflow-x:auto">
<table>
<tr><th>max_tokens</th><th>n_ctx=512 (J)</th><th>n_ctx=2048 (J)</th><th>n_ctx=8192 (J)</th></tr>
<tr><td>16</td><td>11.12</td><td>11.17</td><td>11.22</td></tr>
<tr><td>64</td><td>37.63</td><td>37.93</td><td>38.07</td></tr>
<tr><td>256</td><td>124.12</td><td>124.89</td><td>125.48</td></tr>
</table>
</div>

<h3>1.4 Graphiques</h3>
{img("figures/nctx/fig1_energie_totale.png", "Énergie totale selon n_ctx")}
{img("figures/nctx/fig2_j_par_tok.png", "Efficacité J/tok selon n_ctx")}
{img("figures/nctx/fig3_debit_tok_s.png", "Débit tok/s selon n_ctx")}
{img("figures/nctx/fig4_puissance_w.png", "Puissance moyenne selon n_ctx")}
{img("figures/nctx/fig6_duree_s.png", "Durée d'inférence selon n_ctx")}
{img("figures/nctx/fig5_heatmap_j_tok.png", "Heatmap J/tok — n_ctx × modèle")}

<div class="callout">
<strong>Message clé pour la soutenance :</strong> sur des prompts courts/moyens (usage réaliste d'un assistant embarqué), <code>n_ctx</code> n'est <strong>pas un levier d'optimisation énergétique</strong> pertinent. Il faut le dimensionner selon le besoin fonctionnel (longueur max de conversation), pas selon l'énergie — sauf si le contexte est effectivement rempli en usage réel, cas que nous n'avons pas encore testé (prompt long ≈ n_ctx).
</div>

<h2>2. Analyse générale — <code>n_threads</code></h2>

<p>Campagne symétrique : mêmes 9 configurations, <code>n_threads</code> ∈ {{1, 2, 4}}, <code>n_ctx</code> fixé à 2048. Le Pi 5 dispose de 4 cœurs CPU (Cortex-A76) — cette campagne couvre donc de "1 thread" à "tous les cœurs".</p>

<div class="kpi-row">
<div class="kpi"><div class="val pos">+8.0%</div><div class="lbl">énergie PMIC moyenne (1→4 threads)</div></div>
<div class="kpi"><div class="val pos">+45%</div><div class="lbl">puissance instantanée moyenne (1→4)</div></div>
<div class="kpi"><div class="val neg">-27%</div><div class="lbl">durée d'inférence (1→4)</div></div>
<div class="kpi"><div class="val pos">+31%</div><div class="lbl">débit tok/s (1→4)</div></div>
</div>

<h3>2.1 Le compromis vitesse / puissance</h3>
<p>Contrairement à <code>n_ctx</code>, <code>n_threads</code> agit directement sur le <strong>parallélisme du calcul</strong> : plus de threads → plus de cœurs actifs → le calcul va plus vite (durée moyenne 12.35s → 8.98s) <em>mais</em> chaque cœur actif consomme de la puissance, donc la puissance instantanée moyenne grimpe fortement (4.53 W → 6.56 W, +45%). Le résultat net sur l'énergie totale (puissance × temps) est <strong>défavorable en moyenne</strong> (+8%), car le surcoût de puissance dépasse le gain de temps.</p>

<div class="callout warn">
Attention : <code>n_threads</code> ne se comporte pas de façon monotone au niveau global — 2 threads est en moyenne le point le <strong>plus efficace</strong> (50.7 J), meilleur que 1 thread (53.7 J) <em>et</em> que 4 threads (58.0 J). Le passage 1→2 apporte un gain de parallélisme quasi gratuit (peu de surcoût de synchronisation), alors que 2→4 sature les gains de vitesse tout en continuant à payer la puissance supplémentaire.
</div>

<h3>2.2 Effet très hétérogène selon la quantification</h3>
<p>C'est le résultat le plus riche à présenter : l'effet de <code>n_threads</code> sur l'énergie <strong>dépend fortement de la quantification</strong>, probablement parce que les quantifications les plus légères (Q3) sont plus vite limitées par la bande mémoire que par le calcul, donc profitent moins de threads supplémentaires.</p>

<div style="overflow-x:auto">
<table>
<tr><th>Modèle / quant</th><th>Énergie 1→4 threads</th><th>Débit 1→4 threads</th><th>Lecture</th></tr>
<tr><td>Llama-3.2-1B Q3_K_L</td><td class="neg">-20.6%</td><td class="pos">+121.8%</td><td>gagnant net : 2.2× plus rapide pour 20% d'énergie économisée</td></tr>
<tr><td>Qwen2.5-1.5B Q3_K_L</td><td class="neg">-22.2%</td><td class="pos">+126.6%</td><td>même profil, très favorable aux threads</td></tr>
<tr><td>Gemma-3-1B Q4_K_M</td><td>+0.2%</td><td class="pos">+53.4%</td><td>quasi neutre en énergie, net gain de vitesse</td></tr>
<tr><td>Qwen2.5-1.5B Q4_K_M</td><td>+4.3%</td><td class="pos">+40.7%</td><td>léger surcoût, bon compromis vitesse</td></tr>
<tr><td>Llama-3.2-1B Q4_K_M</td><td>+3.9%</td><td class="pos">+43.4%</td><td>idem</td></tr>
<tr><td>Gemma-3-1B Q3_K_M</td><td class="pos">+21.8%</td><td>+10.1%</td><td>défavorable : peu de gain vitesse pour un surcoût net</td></tr>
<tr><td>Gemma-3-1B Q8_0</td><td class="pos">+44.4%</td><td class="neg">-9.9%</td><td>perdant : plus lent ET plus gourmand à 4 threads</td></tr>
<tr><td>Llama-3.2-1B Q8_0</td><td class="pos">+39.5%</td><td class="neg">-7.1%</td><td>même profil : quant Q8 pénalisée par le multi-thread</td></tr>
<tr><td>Qwen2.5-1.5B Q8_0</td><td class="pos">+39.4%</td><td class="neg">-7.6%</td><td>idem</td></tr>
</table>
</div>

<div class="callout">
<strong>Tendance nette par quantification :</strong> les modèles <strong>Q3</strong> (les plus compressés) bénéficient le plus du multi-threading (jusqu'à +126% de débit pour -22% d'énergie), les <strong>Q4</strong> sont dans un entre-deux favorable, et les <strong>Q8</strong> (les moins compressés, donc les plus gros en mémoire) deviennent <em>contre-productifs</em> à 4 threads : plus de threads les ralentit et augmente leur énergie. Hypothèse : à Q8, le modèle sature déjà la bande passante mémoire du Pi5 avec peu de cœurs ; ajouter des threads ajoute de la contention sans accélérer le calcul, tout en gardant plusieurs cœurs actifs (donc plus de puissance).
</div>

<h3>2.3 Graphiques</h3>
{img("figures/nthreads/fig1_energie_totale.png", "Énergie totale selon n_threads")}
{img("figures/nthreads/fig2_j_par_tok.png", "Efficacité J/tok selon n_threads")}
{img("figures/nthreads/fig3_debit_tok_s.png", "Débit tok/s selon n_threads")}
{img("figures/nthreads/fig4_puissance_w.png", "Puissance moyenne selon n_threads")}
{img("figures/nthreads/fig5_heatmap_j_tok.png", "Heatmap J/tok — n_threads × modèle")}

<h2>3. Synthèse comparative n_ctx vs n_threads</h2>

<div class="grid2">
<div class="card">
<h3 style="margin-top:0">n_ctx</h3>
<ul>
<li>Effet énergie : <strong>négligeable</strong> (+1 à +2%) sur nos prompts courts/moyens</li>
<li>Monotone et reproductible sur les 9 configs</li>
<li>Coût = allocation mémoire, pas calcul (car contexte non rempli)</li>
<li>Levier de dimensionnement fonctionnel, pas énergétique</li>
</ul>
</div>
<div class="card">
<h3 style="margin-top:0">n_threads</h3>
<ul>
<li>Effet énergie : <strong>fort et non-monotone</strong> (-22% à +44% selon quant)</li>
<li>2 threads = optimum moyen (meilleur que 1 et 4)</li>
<li>Dépend fortement de la quantification (Q3 gagne, Q8 perd)</li>
<li>Vrai levier d'optimisation énergétique — à approfondir (tester 3 threads, corréler à la RAM/quant)</li>
</ul>
</div>
</div>

<h3>3.1 Recommandations pour la suite</h3>
<ul>
<li>Pour <code>n_ctx</code> : dossier <strong>clos</strong> pour les cas d'usage à prompts courts. Tester un scénario "contexte rempli" (prompt ≈ n_ctx) pour confirmer que l'effet devient significatif seulement dans ce cas.</li>
<li>Pour <code>n_threads</code> : creuser <strong>pourquoi Q8 est pénalisée</strong> (hypothèse bande mémoire) — un test avec <code>vcgencmd measure_clock</code> ou un profil mémoire (`perf`) confirmerait/infirmerait la saturation. Tester aussi 3 threads pour affiner l'optimum entre 2 et 4.</li>
<li>Recommandation opérationnelle immédiate : <strong>2 threads</strong> comme réglage par défaut pour la suite des campagnes (meilleur compromis énergie/latence toutes quantifications confondues), sauf modèle Q3 où 4 threads reste supérieur.</li>
</ul>

<footer>
Sources : <code>data/raw/nctx_Pi5_2026-07-05_06h32.csv</code> (19 197 lignes) &middot; <code>data/raw/nthreads_Pi5_2026-07-03_12h13.csv</code> &middot; scripts <code>src/analyse_nctx.py</code>, <code>src/analyse_nthreads.py</code> &middot; mesure de puissance : PMIC (rails VDD_CORE) &middot; Raspberry Pi 5, 16 Go RAM.
</footer>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("écrit :", OUT)
