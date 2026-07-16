import json
import os

IMG_JSON = r"C:\Users\Amine\AppData\Local\Temp\claude\C--Users-Amine-Desktop-amiine-Rasbery-Pi\77e4c6d5-b563-4ec8-ab99-8b3d95143c5c\scratchpad\imgs.json"
OUT = r"C:\Users\Amine\Desktop\amiine_Rasbery_Pi\energie-llm-raspberry\docs\presentation_nctx_nthreads.html"

with open(IMG_JSON, encoding="utf-8") as f:
    imgs_raw = json.load(f)
imgs = {k.replace("\\", "/"): v for k, v in imgs_raw.items()}


def img(path, alt, h="46vh"):
    b64 = imgs[path.replace("\\", "/")]
    return f'<img src="data:image/png;base64,{b64}" alt="{alt}" style="max-height:{h};max-width:100%;object-fit:contain;">'


N_SLIDES = 11

html = f"""
<title>Point d'avancement — n_ctx, n_threads, longueur de prompt (Pi 5)</title>
<style>
:root {{ --bg:#0e1013; --panel:#15181d; --text:#dfe3e8; --muted:#8b93a1; --accent:#5b8a72; --accent2:#b5654f; --border:#282c33; }}
@media (prefers-color-scheme: light) {{
  :root {{ --bg:#fbfaf7; --panel:#ffffff; --text:#20242b; --muted:#5b6472; --accent:#3f6b53; --accent2:#9c4a35; --border:#dcdad2; }}
}}
:root[data-theme="light"] {{ --bg:#fbfaf7; --panel:#ffffff; --text:#20242b; --muted:#5b6472; --accent:#3f6b53; --accent2:#9c4a35; --border:#dcdad2; }}
:root[data-theme="dark"] {{ --bg:#0e1013; --panel:#15181d; --text:#dfe3e8; --muted:#8b93a1; --accent:#5b8a72; --accent2:#b5654f; --border:#282c33; }}
* {{ box-sizing:border-box; }}
html {{ scroll-snap-type:y proximity; }}
body {{ background:var(--bg); color:var(--text); font-family:Georgia,"Times New Roman",serif; margin:0; }}
h1, h2, h3, .kicker {{ font-family:-apple-system,Segoe UI,Roboto,sans-serif; }}
.slide {{ min-height:100vh; scroll-snap-align:start; display:flex; flex-direction:column; justify-content:center; padding:52px 84px; border-bottom:1px solid var(--border); position:relative; }}
.slide .num {{ position:absolute; top:20px; right:30px; color:var(--muted); font-size:0.8rem; font-family:-apple-system,Segoe UI,Roboto,sans-serif; }}
.slide .kicker {{ color:var(--accent); text-transform:uppercase; letter-spacing:0.06em; font-size:0.78rem; font-weight:600; margin-bottom:8px; }}
h1 {{ font-size:2.2rem; margin:0 0 10px; line-height:1.2; font-weight:600; }}
h2 {{ font-size:1.55rem; margin:0 0 14px; line-height:1.25; font-weight:600; }}
.sub {{ color:var(--muted); font-size:1rem; margin:2px 0; }}
.title-slide {{ justify-content:center; }}
.title-slide h1 {{ font-size:2.5rem; max-width:820px; }}
.authors {{ margin-top:26px; font-size:1rem; }}
.authors .role {{ color:var(--muted); font-size:0.88rem; }}
.center {{ align-items:center; text-align:center; }}
.card {{ background:var(--panel); border:1px solid var(--border); padding:16px 20px; }}
.kpi-row {{ display:flex; gap:1px; margin:16px 0; background:var(--border); border:1px solid var(--border); }}
.kpi {{ background:var(--panel); padding:14px 18px; flex:1; }}
.kpi .val {{ font-size:1.4rem; font-weight:600; font-family:-apple-system,Segoe UI,Roboto,sans-serif; }}
.kpi .lbl {{ color:var(--muted); font-size:0.76rem; margin-top:2px; }}
.up {{ color:var(--accent2); }}
.down {{ color:var(--accent); }}
table {{ border-collapse:collapse; width:100%; margin:10px 0; font-size:0.87rem; font-family:-apple-system,Segoe UI,Roboto,sans-serif; }}
th, td {{ border:1px solid var(--border); padding:5px 9px; text-align:right; }}
th:first-child, td:first-child {{ text-align:left; }}
th {{ background:rgba(128,128,128,0.08); font-weight:600; }}
.callout {{ border-left:3px solid var(--accent); padding:10px 16px; background:rgba(91,138,114,0.07); margin:12px 0; font-size:0.95rem; }}
.callout.warn {{ border-left-color:var(--accent2); background:rgba(181,101,79,0.07); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; align-items:start; }}
.grid3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; align-items:start; }}
.figwrap {{ display:flex; flex-direction:column; align-items:center; gap:6px; }}
.figcap {{ color:var(--muted); font-size:0.85rem; max-width:760px; text-align:center; font-family:-apple-system,Segoe UI,Roboto,sans-serif; }}
code {{ background:rgba(128,128,128,0.13); padding:1px 5px; font-size:0.88em; font-family:Consolas,monospace; }}
ul {{ font-size:0.95rem; line-height:1.55; margin:6px 0; }}
@media (max-width:900px) {{ .grid2, .grid3 {{ grid-template-columns:1fr; }} .slide {{ padding:32px 20px; }} h1 {{ font-size:1.7rem; }} h2 {{ font-size:1.25rem; }} }}
</style>

<!-- 1 -->
<section class="slide title-slide">
  <div class="kicker">Stage LISTIC — USMB / Polytech Annecy</div>
  <h1>Point d'avancement — energie des LLM sur Raspberry Pi 5</h1>
  <p class="sub">Ce qui a ete fait depuis le dernier point (25 juin) : effet de <code>n_ctx</code>, <code>n_threads</code>, et de la longueur du prompt sur la consommation d'energie</p>
  <div class="authors">
    <div><strong>Amine</strong> &amp; <strong>Othmane</strong></div>
    <div class="role">Encadrement : Stephane Plassart, Sebastien Monnet</div>
  </div>
</section>

<!-- 2 -->
<section class="slide">
  <div class="num">2 / {N_SLIDES}</div>
  <div class="kicker">Depuis le 25 juin</div>
  <h2>3 campagnes lancees, plus de 25 000 mesures</h2>
  <table>
    <tr><th>Campagne</th><th>Question</th><th>Parametre varie</th><th>Mesures</th></tr>
    <tr><td>n_ctx</td><td>Le contexte alloue coute-t-il de l'energie ?</td><td>512 / 2048 / 8192</td><td>19 197</td></tr>
    <tr><td>n_threads</td><td>Plus de coeurs = plus efficace ?</td><td>1 / 2 / 4</td><td>&gt; 6 000</td></tr>
    <tr><td>Longueur de prompt x n_ctx</td><td>Le contexte compte-t-il quand il est rempli ?</td><td>50 a 7 638 tokens</td><td>39</td></tr>
  </table>
  <div class="callout">3 modeles (Llama-3.2-1B, Gemma-3-1B, Qwen2.5-1.5B) x 3 quantifications (Q3/Q4/Q8), mesure de puissance reelle par PMIC embarque sur le Pi 5.</div>
</section>

<!-- 3 -->
<section class="slide">
  <div class="num">3 / {N_SLIDES}</div>
  <div class="kicker">Resultat 1 — n_ctx</div>
  <h2>n_ctx n'a aucun effet energetique mesurable</h2>
  <div class="kpi-row">
    <div class="kpi"><div class="val">+1.1%</div><div class="lbl">energie, 512 &rarr; 8192</div></div>
    <div class="kpi"><div class="val">+1.4%</div><div class="lbl">duree, 512 &rarr; 8192</div></div>
    <div class="kpi"><div class="val">0</div><div class="lbl">config. ou n_ctx change le classement</div></div>
  </div>
  <div class="callout">n_ctx fixe seulement la taille <em>maximale</em> allouee pour le contexte — pas la taille reellement utilisee. Tant que le prompt tient dedans, le calcul est identique : le tres faible surcout observe (~1%) est un cout d'allocation memoire au chargement, pas un cout de calcul.</div>
</section>

<!-- 4 -->
<section class="slide center">
  <div class="num">4 / {N_SLIDES}</div>
  <div class="kicker">n_ctx — preuve</div>
  <h2>Energie identique sur les 9 configurations, quel que soit n_ctx</h2>
  <div class="figwrap">
    {img("figures/nctx/fig5_heatmap_j_tok.png", "Heatmap J/tok n_ctx x modele", h="56vh")}
    <p class="figcap">Efficacite (J/token) par modele x quantification. Les 3 colonnes (512 / 2048 / 8192) sont quasi identiques ligne par ligne : n_ctx ne deplace aucune configuration.</p>
  </div>
</section>

<!-- 5 -->
<section class="slide">
  <div class="num">5 / {N_SLIDES}</div>
  <div class="kicker">Resultat 2 — n_threads</div>
  <h2>n_threads est un vrai levier — mais pas lineaire</h2>
  <div class="kpi-row">
    <div class="kpi"><div class="val down">2 threads</div><div class="lbl">optimum energetique moyen</div></div>
    <div class="kpi"><div class="val up">+8%</div><div class="lbl">energie a 4 threads vs 1</div></div>
    <div class="kpi"><div class="val down">-22%</div><div class="lbl">energie Q3 (1&rarr;4 threads)</div></div>
    <div class="kpi"><div class="val up">+44%</div><div class="lbl">energie Q8 (1&rarr;4 threads)</div></div>
  </div>
  <div class="callout warn">Plus de threads = plus rapide, mais aussi plus de puissance instantanee (+45% en moyenne). Le gain net depend de la quantification : les modeles Q3 (legers) beneficient a fond du parallelisme, les modeles Q8 (lourds) sont penalises — probable saturation de la bande memoire du Pi 5.</div>
</section>

<!-- 6 -->
<section class="slide center">
  <div class="num">6 / {N_SLIDES}</div>
  <div class="kicker">n_threads — preuve</div>
  <h2>Un optimum en U, et un effet oppose selon la quantification</h2>
  <div class="grid2">
    <div class="figwrap">
      {img("figures/nthreads/fig1_energie_totale.png", "Energie totale selon n_threads")}
      <p class="figcap">Energie totale : minimum a 2 threads pour la plupart des configurations.</p>
    </div>
    <div class="figwrap">
      {img("figures/nthreads/fig5_heatmap_j_tok.png", "Heatmap J/tok n_threads x modele")}
      <p class="figcap">Heatmap : Q3 (vert, gagne) vs Q8 (rouge, perd) a 4 threads.</p>
    </div>
  </div>
</section>

<!-- 7 -->
<section class="slide">
  <div class="num">7 / {N_SLIDES}</div>
  <div class="kicker">Resultat 3 — longueur de prompt x n_ctx</div>
  <h2>Ce qui compte, c'est la longueur reelle du prompt — pas n_ctx</h2>
  <p class="sub">Question posee au dernier echange : n_ctx aurait-il un effet si le prompt remplissait vraiment le contexte ? Reponse testee jusqu'a 95% de remplissage.</p>
  <div class="callout">Un prompt de 392 tokens coute <strong>73 J</strong>, que le contexte alloue soit rempli a 78% (n_ctx=512) ou a 5% (n_ctx=8192). Meme constat a 93% de remplissage (1862 tokens). Ecart &lt; 1%, non significatif.</div>
</section>

<!-- 8 -->
<section class="slide center">
  <div class="num">8 / {N_SLIDES}</div>
  <div class="kicker">Preuve — memes prompts, n_ctx differents</div>
  <h2>Meme prompt, n_ctx different : energie identique</h2>
  <div class="figwrap">
    {img("figures/prompt_length_nctx/fig1_meme_prompt_diff_nctx.png", "Meme prompt differents n_ctx")}
    <p class="figcap">3 longueurs de prompt (50 / 392 / 1862 tokens), chacune testee a plusieurs n_ctx : l'energie ne bouge pas, meme pres de 95% de remplissage.</p>
  </div>
</section>

<!-- 9 -->
<section class="slide center">
  <div class="num">9 / {N_SLIDES}</div>
  <div class="kicker">Preuve — loi energetique</div>
  <h2>L'energie suit une loi quadratique en fonction du prompt</h2>
  <div class="figwrap">
    {img("figures/prompt_length_nctx/fig2_loi_quadratique.png", "Loi quadratique energie vs longueur prompt")}
    <p class="figcap">E &asymp; 0.000012&middot;n&sup2; + 0.104&middot;n + 29.6 J, R&sup2;=1.000 de 50 a 7 638 tokens. Le terme en n&sup2; = cout d'auto-attention sur le prompt lui-meme, independant de n_ctx.</p>
  </div>
</section>

<!-- 10 -->
<section class="slide">
  <div class="num">10 / {N_SLIDES}</div>
  <div class="kicker">Synthese</div>
  <h2>Trois leviers, trois comportements</h2>
  <div class="grid3">
    <div class="card">
      <h3 style="margin-top:0">n_ctx</h3>
      <p class="sub">Aucun effet, meme plein a 95%. Parametre a regler selon le besoin fonctionnel uniquement.</p>
    </div>
    <div class="card">
      <h3 style="margin-top:0">n_threads</h3>
      <p class="sub">Effet fort, non-lineaire, depend de la quantification. Vrai levier d'optimisation.</p>
    </div>
    <div class="card">
      <h3 style="margin-top:0">Longueur de prompt</h3>
      <p class="sub">Le vrai facteur cache : loi quadratique. Impact bien plus fort que n_ctx ou n_threads sur les gros prompts.</p>
    </div>
  </div>
</section>

<!-- 11 -->
<section class="slide center">
  <div class="num">11 / {N_SLIDES}</div>
  <div class="kicker">Recommandations</div>
  <h2>Pour la suite</h2>
  <div class="card" style="max-width:720px; text-align:left;">
    <ul>
      <li>Regler <strong>n_threads=2</strong> par defaut pour les prochaines campagnes (meilleur compromis toutes quantifications confondues)</li>
      <li>Ne plus tester n_ctx pour l'energie — dossier clos, sauf besoin fonctionnel de contexte long</li>
      <li>Integrer la longueur de prompt comme variable de premier plan dans le modele de cout energetique (loi quadratique confirmee)</li>
      <li>Creuser la saturation memoire des quantifications Q8 a 4 threads</li>
    </ul>
  </div>
</section>
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("ecrit :", OUT)
