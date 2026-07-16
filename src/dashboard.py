"""
Dashboard energie LLM Raspberry Pi 5 -- LISTIC.
Navigation par mode (une question de recherche = une campagne source),
pas de filtres plats croises : evite les combinaisons jamais mesurees.
Lancer avec : streamlit run src/dashboard.py
"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Energie LLM Pi5", layout="wide", page_icon=":material/bolt:")

DATA = "data/raw"
CARACTERES_PAR_TOKEN = 4.0   # approximation calibree (script latin, FR/EN) -- pas de tokenizer reel dispo hors Pi
BATTERIE_SMARTPHONE_J = 55_440  # 4000 mAh x 3.85 V x 3600 s -- a resourcer avec le modele de tel utilise en demo

# ============================================================
#  DESIGN SYSTEM -- CSS + PALETTE + HELPERS PLOTLY
# ============================================================

PALETTE = ["#2563EB", "#0EA5E9", "#14B8A6", "#F59E0B", "#8B5CF6", "#EC4899"]

st.markdown("""
<style>
.block-container { padding-top: 2rem; padding-bottom: 3rem; }

.kpi-card {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 14px;
    padding: 1.1rem 1.35rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    height: 100%;
}
.kpi-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: .05em;
    opacity: .60;
    margin-bottom: .35rem;
    font-weight: 600;
}
.kpi-value { font-size: 1.65rem; font-weight: 700; line-height: 1.15; }
.kpi-sub { font-size: 0.78rem; opacity: .55; margin-top: .3rem; }

.hero-title { font-size: 2.1rem; font-weight: 800; margin-bottom: .1rem; }
.hero-sub { opacity: .65; font-size: 0.95rem; margin-bottom: 1.4rem; }

section[data-testid="stSidebar"] .stMarkdown h4 {
    font-size: 0.8rem; text-transform: uppercase; letter-spacing: .05em;
    opacity: .6; margin-top: 1.1rem; margin-bottom: .3rem;
}

.gros-chiffre { font-size: 3rem; font-weight: 800; line-height: 1.05; }
.tag-loi { font-size: 0.72rem; padding: .15rem .55rem; border-radius: 999px; font-weight: 600; }
.tag-mesuree { background: #D1FAE5; color: #065F46; }
.tag-approx { background: #FEF3C7; color: #92400E; }
</style>
""", unsafe_allow_html=True)


def kpi_row(items):
    """items: liste de (label, valeur, sous-texte optionnel)."""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value, sub = (item + ("",))[:3]
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)


def style_fig(fig, height=420, rounded_bars=False):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, -apple-system, Segoe UI, sans-serif", size=13),
        title=dict(font=dict(size=15)),
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", title=None),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=height,
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#e5e7eb"),
        colorway=PALETTE,
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(120,120,120,0.12)", zeroline=False)
    if rounded_bars:
        fig.update_traces(marker=dict(cornerradius=8), selector=dict(type="bar"))
    return fig


def sidebar_section(titre):
    st.sidebar.markdown(f"#### {titre}")


def fmt(v, decimals=3, unit=""):
    return f"{v:.{decimals}f}{unit}"


# ============================================================
#  CHARGEMENT (mis en cache -- le filtrage ensuite reste instantane)
# ============================================================

@st.cache_data
def load_csv(path):
    return pd.read_csv(path)


@st.cache_data
def load_nthreads():
    df = load_csv(f"{DATA}/resultats_Pi5_2026-07-09_13h58.csv")
    df["tok_s"] = df["tokens"] / df["duree_s"]
    df["j_par_tok"] = df["joules_pmic"] / df["tokens"]
    df["label"] = df["modele"] + " " + df["quantification"]
    return df


@st.cache_data
def load_prise_nthreads():
    df = load_csv(f"{DATA}/resultats_Pi5_2026-07-09_13h58_prise.csv")
    return df.rename(columns={
        "energie_mur_J": "energie_prise_J",
        "energie_mur_marginale_J": "energie_prise_marginale_J",
        "J_par_requete_mur": "J_par_requete_prise",
        "puissance_moyenne_mur_W": "puissance_moyenne_prise_W",
        "rendement_pmic_sur_mur_pct": "rendement_pmic_sur_prise_pct",
    })


@st.cache_data
def load_nctx():
    df = load_csv(f"{DATA}/nctx_Pi5_2026-07-05_06h32.csv")
    df["tok_s"] = df["tokens"] / df["duree_s"]
    df["j_par_tok"] = df["joules_pmic"] / df["tokens"]
    df["label"] = df["modele"] + " " + df["quantification"]
    return df


@st.cache_data
def load_prompt_size():
    df = load_csv(f"{DATA}/prompt_size_Pi5_2026-06-17_11h22.csv")
    df["j_par_tok"] = df["joules_pmic"] / df["output_tokens"]
    return df


@st.cache_data
def load_prompt_length_nctx():
    df = load_csv(f"{DATA}/prompt_length_nctx_Pi5_2026-07-06_11h26.csv")
    df["j_par_tok"] = df["joules_pmic"] / df["output_tokens"]
    return df


VUE_GLOBALE_FICHIERS = [
    "resultats_Pi5_2026-06-15_14h45.csv",
    "resultats_Pi5_2026-06-19_05h16.csv",
    "resultats_Pi5_2026-06-24_16h01.csv",
    "resultats_Pi5_2026-06-25_15h57.csv",
    "resultats_Pi5_2026-07-01_13h35.csv",
]


@st.cache_data
def load_vue_globale():
    frames = []
    for nom in VUE_GLOBALE_FICHIERS:
        try:
            d = load_csv(f"{DATA}/{nom}")
            d["campagne"] = nom
            frames.append(d)
        except FileNotFoundError:
            continue
    df = pd.concat(frames, ignore_index=True)
    df = df[df["modele"] != "SmolLM2-1.7B"]  # campagne test isolee, pas de suite -- exclu partout
    df["j_par_tok"] = df["joules_pmic"] / df["tokens"]
    df["label"] = df["modele"] + " " + df["quantification"]
    return df


def mesures_disponibles(df, group_cols):
    """Table de secours affichee quand le filtre choisi renvoie 0 ligne."""
    return (
        df.groupby(group_cols).size().reset_index(name="n_mesures")
        .sort_values("n_mesures", ascending=False)
    )


def bloc_vide(df_complet, group_cols, message="Aucune mesure pour cette combinaison."):
    st.warning(message + " Combinaisons disponibles :")
    st.dataframe(mesures_disponibles(df_complet, group_cols), width="stretch", height=250)


# ============================================================
#  LOIS ENERGETIQUES POUR LA DEMO SENSIBILISATION
#  Ajustees depuis les CSV a chaque lancement, jamais codees en dur
# ============================================================

@st.cache_data
def taux_decodage():
    """J par token genere, moyenne mesuree par (modele, quantification) -- campagnes principales."""
    df = load_vue_globale()
    return df.groupby(["modele", "quantification"])["j_par_tok"].mean().to_dict()


@st.cache_data
def loi_prefill_llama_q4():
    """Regression quadratique E(input_tokens) pour Llama-3.2-1B Q4_K_M, sortie fixe 64 tokens.
    Seule config avec longueur de prompt variee -- loi non extrapolable aux autres modeles."""
    df = pd.read_csv(f"{DATA}/prompt_size_Pi5_2026-06-17_11h22.csv")
    df = df[(df["modele"] == "Llama-3.2-1B") & (df["quantification"] == "Q4_K_M")]
    c, b, a = np.polyfit(df["input_tokens"], df["joules_pmic"], 2)  # E = a + b*n + c*n^2
    return {"a": a, "b": b, "c": c, "output_tokens_ref": 64}


def estimer_energie(modele, quant, nb_tokens_input, nb_tokens_output):
    taux = taux_decodage()
    rate = taux.get((modele, quant))
    if rate is None:
        return None, "inconnu"

    if modele == "Llama-3.2-1B" and quant == "Q4_K_M":
        loi = loi_prefill_llama_q4()
        e_totale_64 = loi["a"] + loi["b"] * nb_tokens_input + loi["c"] * nb_tokens_input ** 2
        e_prefill = e_totale_64 - loi["output_tokens_ref"] * rate
        energie = max(e_prefill, 0) + nb_tokens_output * rate
        return energie, "mesuree"
    else:
        energie = (nb_tokens_input + nb_tokens_output) * rate
        return energie, "approximee"


# ============================================================
#  MODE 1 : IMPACT n_threads
# ============================================================

def mode_nthreads():
    st.markdown('<div class="hero-title">Impact de n_threads</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">resultats_Pi5_2026-07-09_13h58.csv -- campagne corrigee '
                '(fix prise Z-Wave) -- n_ctx fixe = 2048</div>', unsafe_allow_html=True)
    df = load_nthreads()

    sidebar_section("Modele & quantification")
    modeles = st.sidebar.pills("Modele(s)", sorted(df["modele"].unique()),
                                selection_mode="multi", default=sorted(df["modele"].unique()))
    quants = st.sidebar.pills("Quantification(s)", sorted(df["quantification"].unique()),
                               selection_mode="multi", default=sorted(df["quantification"].unique()))
    sidebar_section("Parametres")
    threads = st.sidebar.pills("n_threads", sorted(df["n_threads"].unique()),
                                selection_mode="multi", default=sorted(df["n_threads"].unique()))

    sub = df[df["modele"].isin(modeles) & df["quantification"].isin(quants) & df["n_threads"].isin(threads)]
    if sub.empty:
        bloc_vide(df, ["modele", "quantification", "n_threads"])
        return

    meilleur = sub.loc[sub["j_par_tok"].idxmin()]
    kpi_row([
        ("Efficacite moyenne", fmt(sub["j_par_tok"].mean(), 3, " J/tok"), f"{len(sub)} mesures"),
        ("Debit moyen", fmt(sub["tok_s"].mean(), 1, " tok/s"), ""),
        ("Puissance moyenne", fmt(sub["w_moyen_pmic"].mean(), 2, " W"), "mesure PMIC onboard"),
        ("Meilleure config", f"{int(meilleur['n_threads'])} threads", meilleur["label"]),
    ])
    st.divider()

    agg = (sub.groupby(["label", "n_threads"])
           .agg(j_par_tok=("j_par_tok", "mean"), tok_s=("tok_s", "mean"),
                w_moyen=("w_moyen_pmic", "mean"), n=("j_par_tok", "size"))
           .reset_index())
    agg["n_threads"] = agg["n_threads"].astype(str)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(agg, x="label", y="j_par_tok", color="n_threads", barmode="group",
                     labels={"j_par_tok": "J / token", "label": "", "n_threads": "n_threads"},
                     title="Efficacite energetique (J/tok) selon n_threads",
                     color_discrete_sequence=PALETTE)
        fig.update_traces(hovertemplate="%{x}<br>%{y:.3f} J/tok<extra></extra>")
        st.plotly_chart(style_fig(fig, rounded_bars=True), width="stretch")
    with c2:
        fig = px.bar(agg, x="label", y="tok_s", color="n_threads", barmode="group",
                     labels={"tok_s": "Tokens / s", "label": "", "n_threads": "n_threads"},
                     title="Debit selon n_threads", color_discrete_sequence=PALETTE)
        fig.update_traces(hovertemplate="%{x}<br>%{y:.1f} tok/s<extra></extra>")
        st.plotly_chart(style_fig(fig, rounded_bars=True), width="stretch")

    st.markdown("**Meilleur choix par modele (energie la plus basse) :**")
    for label_modele in sorted(agg["label"].unique()):
        meilleur_ligne = agg[agg["label"] == label_modele].loc[
            agg[agg["label"] == label_modele]["j_par_tok"].idxmin()]
        st.markdown(f"- **{label_modele}** → {meilleur_ligne['n_threads']} threads "
                    f"({meilleur_ligne['j_par_tok']:.3f} J/tok)")


# ============================================================
#  MODE 2 : IMPACT n_ctx
# ============================================================

def mode_nctx():
    st.markdown('<div class="hero-title">Impact de n_ctx</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">nctx_Pi5_2026-07-05_06h32.csv -- n_threads fixe = 4</div>',
                unsafe_allow_html=True)
    df = load_nctx()

    sidebar_section("Modele & quantification")
    modeles = st.sidebar.pills("Modele(s)", sorted(df["modele"].unique()),
                                selection_mode="multi", default=sorted(df["modele"].unique()))
    quants = st.sidebar.pills("Quantification(s)", sorted(df["quantification"].unique()),
                               selection_mode="multi", default=sorted(df["quantification"].unique()))
    sidebar_section("Parametres")
    ctxs = st.sidebar.pills("n_ctx", sorted(df["n_ctx"].unique()),
                             selection_mode="multi", default=sorted(df["n_ctx"].unique()))

    sub = df[df["modele"].isin(modeles) & df["quantification"].isin(quants) & df["n_ctx"].isin(ctxs)]
    if sub.empty:
        bloc_vide(df, ["modele", "quantification", "n_ctx"])
        return

    kpi_row([
        ("Efficacite moyenne", fmt(sub["j_par_tok"].mean(), 3, " J/tok"), f"{len(sub)} mesures"),
        ("Debit moyen", fmt(sub["tok_s"].mean(), 1, " tok/s"), ""),
        ("Valeurs n_ctx testees", str(len(ctxs)), ", ".join(str(c) for c in sorted(ctxs))),
        ("Ecart max observe", fmt((sub["j_par_tok"].max() - sub["j_par_tok"].min()) /
                                   sub["j_par_tok"].min() * 100, 1, " %"), "entre valeurs n_ctx"),
    ])
    st.divider()

    agg = (sub.groupby(["label", "n_ctx"])
           .agg(j_par_tok=("j_par_tok", "mean"), tok_s=("tok_s", "mean"))
           .reset_index())
    agg["n_ctx"] = agg["n_ctx"].astype(str)

    fig = px.bar(agg, x="label", y="j_par_tok", color="n_ctx", barmode="group",
                 labels={"j_par_tok": "J / token", "label": ""},
                 title="Efficacite energetique (J/tok) selon n_ctx -- cout cache du contexte alloue",
                 color_discrete_sequence=PALETTE)
    fig.update_traces(hovertemplate="%{x}<br>%{y:.3f} J/tok<extra></extra>")
    st.plotly_chart(style_fig(fig, rounded_bars=True), width="stretch")

    st.caption("Rappel etat de l'art : n_ctx n'a d'effet mesurable qu'a saturation quasi totale du contexte.")


# ============================================================
#  MODE 3 : IMPACT TAILLE PROMPT
# ============================================================

def mode_taille_prompt():
    st.markdown('<div class="hero-title">Impact de la taille du prompt</div>', unsafe_allow_html=True)

    sidebar_section("Campagne")
    sous_mode = st.sidebar.pills("Source", ["Longueur seule", "Longueur x n_ctx"],
                                  selection_mode="single", default="Longueur seule")

    if sous_mode == "Longueur seule":
        st.markdown('<div class="hero-sub">prompt_size_Pi5_2026-06-17_11h22.csv -- sortie fixe</div>',
                    unsafe_allow_html=True)
        df = load_prompt_size()
        sidebar_section("Modele & quantification")
        modeles = st.sidebar.pills("Modele(s)", sorted(df["modele"].unique()),
                                    selection_mode="multi", default=sorted(df["modele"].unique()))
        quants = st.sidebar.pills("Quantification(s)", sorted(df["quantification"].unique()),
                                   selection_mode="multi", default=sorted(df["quantification"].unique()))
        sub = df[df["modele"].isin(modeles) & df["quantification"].isin(quants)]
        if sub.empty:
            bloc_vide(df, ["modele", "quantification"])
            return

        kpi_row([
            ("Energie moyenne", fmt(sub["joules_pmic"].mean(), 1, " J"), f"{len(sub)} mesures"),
            ("Tokens entree (max)", str(int(sub["input_tokens"].max())), ""),
            ("Tokens entree (min)", str(int(sub["input_tokens"].min())), ""),
            ("Modeles compares", str(sub["modele"].nunique()), ""),
        ])
        st.divider()

        fig = px.scatter(sub, x="input_tokens", y="joules_pmic", color="modele",
                          symbol="quantification", color_discrete_sequence=PALETTE,
                          labels={"input_tokens": "Tokens en entree", "joules_pmic": "Energie PMIC (J)"},
                          title="Energie vs longueur du prompt (sortie fixe)")
        fig.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=0)))
        st.plotly_chart(style_fig(fig, height=460), width="stretch")
    else:
        st.markdown('<div class="hero-sub">prompt_length_nctx_Pi5_2026-07-06_11h26.csv -- '
                     'isole l\'effet du remplissage du contexte alloue</div>', unsafe_allow_html=True)
        df = load_prompt_length_nctx()
        sidebar_section("Modele & parametres")
        modeles = st.sidebar.pills("Modele(s)", sorted(df["modele"].unique()),
                                    selection_mode="multi", default=sorted(df["modele"].unique()))
        ctxs = st.sidebar.pills("n_ctx", sorted(df["n_ctx"].unique()),
                                 selection_mode="multi", default=sorted(df["n_ctx"].unique()))
        sub = df[df["modele"].isin(modeles) & df["n_ctx"].isin(ctxs)]
        if sub.empty:
            bloc_vide(df, ["modele", "n_ctx"])
            return

        kpi_row([
            ("Energie moyenne", fmt(sub["joules_pmic"].mean(), 1, " J"), f"{len(sub)} mesures"),
            ("Remplissage max", fmt(sub["fraction_ctx_remplie"].max() * 100, 0, " %"), ""),
            ("n_ctx testes", str(len(ctxs)), ", ".join(str(c) for c in sorted(ctxs))),
            ("Modeles compares", str(sub["modele"].nunique()), ""),
        ])
        st.divider()

        sub = sub.copy()
        sub["n_ctx"] = sub["n_ctx"].astype(str)
        fig = px.scatter(sub, x="input_tokens", y="joules_pmic", color="n_ctx",
                          color_discrete_sequence=PALETTE,
                          labels={"input_tokens": "Tokens en entree", "joules_pmic": "Energie PMIC (J)",
                                  "n_ctx": "n_ctx"},
                          title="Energie vs longueur du prompt, par n_ctx -- points superposes "
                                "= n_ctx sans effet a longueur egale")
        fig.update_traces(marker=dict(size=11, opacity=0.85, line=dict(width=0)))
        st.plotly_chart(style_fig(fig, height=460), width="stretch")
        st.caption("A meme longueur de prompt (input_tokens), les couleurs (n_ctx) se superposent -- "
                   "preuve que n_ctx n'a pas d'effet propre. La hausse generale suit la longueur du prompt, "
                   "pas la valeur de n_ctx.")


# ============================================================
#  MODE 4 : VUE GLOBALE MODELE / QUANTIFICATION
# ============================================================

def mode_vue_globale():
    st.markdown('<div class="hero-title">Vue globale modele / quantification</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Campagnes principales (06-15 -> 07-01) -- n_threads/n_ctx '
                'fixes par defaut de campaign.py (4, 2048), colonnes absentes de ces fichiers</div>',
                unsafe_allow_html=True)
    df = load_vue_globale()

    sidebar_section("Modele & quantification")
    modeles = st.sidebar.pills("Modele(s)", sorted(df["modele"].unique()),
                                selection_mode="multi", default=sorted(df["modele"].unique()))
    quants = st.sidebar.pills("Quantification(s)", sorted(df["quantification"].unique()),
                               selection_mode="multi", default=sorted(df["quantification"].unique()))
    sidebar_section("Parametres")
    max_toks = st.sidebar.pills("max_tokens", sorted(df["max_tokens"].unique()),
                                 selection_mode="multi", default=sorted(df["max_tokens"].unique()))

    sub = df[df["modele"].isin(modeles) & df["quantification"].isin(quants) & df["max_tokens"].isin(max_toks)]
    if sub.empty:
        bloc_vide(df, ["modele", "quantification", "max_tokens"])
        return

    meilleur = sub.loc[sub["j_par_tok"].idxmin()]
    kpi_row([
        ("Efficacite moyenne", fmt(sub["j_par_tok"].mean(), 3, " J/tok"), f"{len(sub)} mesures"),
        ("Meilleure config", fmt(meilleur["j_par_tok"], 3, " J/tok"), meilleur["label"]),
        ("Modeles compares", str(sub["modele"].nunique()), ""),
        ("Campagnes sources", str(sub["campagne"].nunique()), ""),
    ])
    st.divider()

    agg = (sub.groupby(["label", "max_tokens"])
           .agg(j_par_tok=("j_par_tok", "mean"))
           .reset_index())
    agg["max_tokens"] = agg["max_tokens"].astype(str)

    fig = px.bar(agg, x="label", y="j_par_tok", color="max_tokens", barmode="group",
                 labels={"j_par_tok": "J / token", "label": ""},
                 title="Efficacite energetique par modele/quantification",
                 color_discrete_sequence=PALETTE)
    fig.update_traces(hovertemplate="%{x}<br>%{y:.3f} J/tok<extra></extra>")
    st.plotly_chart(style_fig(fig, rounded_bars=True), width="stretch")


# ============================================================
#  MODE 5 : COMPARAISON 3 METHODES (CodeCarbon / PMIC / Prise)
# ============================================================

def mode_comparaison_methodes():
    st.markdown('<div class="hero-title">Comparaison des 3 methodes de mesure</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Restreint a la campagne 2026-07-09 (13h58) -- seule campagne '
                'ou la prise Z-Wave a fonctionne en meme temps que n_threads etait varie</div>',
                unsafe_allow_html=True)
    df = load_nthreads()
    prise = load_prise_nthreads()

    # Repartition proportionnelle : prise_estimee par requete = poids PMIC x total prise marginal du modele
    df = df.merge(prise[["modele", "energie_prise_marginale_J"]], on="modele", how="left")
    somme_pmic_modele = df.groupby("modele")["joules_pmic"].transform("sum")
    df["prise_estimee_J"] = df["joules_pmic"] / somme_pmic_modele * df["energie_prise_marginale_J"]

    sidebar_section("Modele & quantification")
    modeles = st.sidebar.pills("Modele(s)", sorted(df["modele"].unique()),
                                selection_mode="multi", default=sorted(df["modele"].unique()))
    quants = st.sidebar.pills("Quantification(s)", sorted(df["quantification"].unique()),
                               selection_mode="multi", default=sorted(df["quantification"].unique()))
    sidebar_section("Parametres")
    threads = st.sidebar.pills("n_threads", sorted(df["n_threads"].unique()),
                                selection_mode="multi", default=sorted(df["n_threads"].unique()))
    sidebar_section("Vue")
    vue_brute = st.sidebar.toggle("Vue agregee brute (vraies valeurs mesurees)", value=False)

    sub = df[df["modele"].isin(modeles) & df["quantification"].isin(quants) & df["n_threads"].isin(threads)]
    if sub.empty:
        bloc_vide(df, ["modele", "quantification", "n_threads"])
        return

    if vue_brute:
        st.info("Vue agregee : 3 vraies mesures independantes, une par modele sur toute la campagne "
                "(ne varie pas avec les filtres n_threads/quantification ci-dessus).")
        p = prise[prise["modele"].isin(modeles)]
        items = [(row["modele"], fmt(row["rendement_pmic_sur_prise_pct"], 1, " %"),
                  f"PMIC {row['somme_J_pmic']:.0f} J / prise {row['energie_prise_marginale_J']:.0f} J")
                 for _, row in p.iterrows()]
        if items:
            kpi_row(items)
        return

    kpi_row([
        ("Rendement PMIC/prise", fmt(prise[prise["modele"].isin(modeles)]["rendement_pmic_sur_prise_pct"].mean(),
                                      1, " %"), "moyenne modeles selectionnes"),
        ("CodeCarbon vs PMIC", fmt((sub["joules"].mean() / sub["joules_pmic"].mean() - 1) * 100, 1, " %"),
         "surestimation logicielle"),
        ("Ratio prise/PMIC", "~0.976", "stable sur les 3 modeles"),
        ("Mesures", str(len(sub)), ""),
    ])
    st.divider()

    st.warning("Valeurs **prise estimees** par repartition proportionnelle du total mesure par modele "
               "(hypothese : rendement PMIC/prise constant a travers n_threads et quantification -- "
               "non verifie independamment, car la mesure a la prise n'existe qu'agregee par modele).")

    agg = (sub.groupby(["label", "n_threads"])
           .agg(codecarbon_J=("joules", "mean"), pmic_J=("joules_pmic", "mean"),
                prise_estimee_J=("prise_estimee_J", "mean"))
           .reset_index())
    agg["n_threads"] = agg["n_threads"].astype(str)
    agg_melt = agg.melt(id_vars=["label", "n_threads"],
                         value_vars=["codecarbon_J", "pmic_J", "prise_estimee_J"],
                         var_name="methode", value_name="joules")
    agg_melt["methode"] = agg_melt["methode"].replace({
        "codecarbon_J": "CodeCarbon (estime logiciel)",
        "pmic_J": "PMIC (mesure reelle)",
        "prise_estimee_J": "Prise -- estime (derive)",
    })

    fig = px.bar(agg_melt, x="label", y="joules", color="methode", facet_col="n_threads",
                 barmode="group", pattern_shape="methode",
                 pattern_shape_map={"Prise -- estime (derive)": "/", "PMIC (mesure reelle)": "",
                                     "CodeCarbon (estime logiciel)": ""},
                 color_discrete_map={
                     "CodeCarbon (estime logiciel)": "#94A3B8",
                     "PMIC (mesure reelle)": "#0EA5E9",
                     "Prise -- estime (derive)": "#F59E0B",
                 },
                 labels={"joules": "Energie moyenne par requete (J)", "label": ""},
                 title="CodeCarbon vs PMIC vs Prise (estime) par n_threads")
    fig.update_traces(hovertemplate="%{x}<br>%{y:.1f} J<extra></extra>")
    st.plotly_chart(style_fig(fig, height=460, rounded_bars=True), width="stretch")


# ============================================================
#  MODE 6 : SENSIBILISATION -- COMBIEN COUTE TA QUESTION ?
# ============================================================

def mode_sensibilisation():
    st.markdown('<div class="hero-title">Combien coute ta question a une IA ?</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Prediction basee sur les lois ajustees a partir des campagnes -- '
                'pas une mesure en direct sur le Pi</div>', unsafe_allow_html=True)

    taux = taux_decodage()
    modeles_dispo = sorted({m for m, _ in taux.keys()})

    sidebar_section("Modele")
    modele = st.sidebar.selectbox("Modele", modeles_dispo,
                                   index=modeles_dispo.index("Llama-3.2-1B") if "Llama-3.2-1B" in modeles_dispo else 0)
    quants_dispo = sorted({q for m, q in taux.keys() if m == modele})
    quant = st.sidebar.selectbox("Quantification", quants_dispo,
                                  index=quants_dispo.index("Q4_K_M") if "Q4_K_M" in quants_dispo else 0)
    sidebar_section("Reponse")
    max_tokens = st.sidebar.slider("Longueur de reponse (tokens)", 16, 512, 128, step=16)

    if modele == "Llama-3.2-1B" and quant == "Q4_K_M":
        st.markdown('<span class="tag-loi tag-mesuree">Loi mesuree (prefill + decodage)</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<span class="tag-loi tag-approx">Approximation lineaire -- pas de loi de longueur '
                    'mesuree pour cette config</span>', unsafe_allow_html=True)

    question = st.text_area("Tape ta question", placeholder="Explique-moi la relativite generale...",
                             height=100)

    nb_car = len(question)
    nb_tokens_input = max(round(nb_car / CARACTERES_PAR_TOKEN), 1) if nb_car else 0

    if nb_car == 0:
        st.info("Tape une question pour voir son cout energetique estime.")
        return

    energie, statut = estimer_energie(modele, quant, nb_tokens_input, max_tokens)
    if energie is None:
        st.error("Pas de mesure disponible pour cette combinaison modele/quantification.")
        return
    st.divider()

    pct_batterie = energie / BATTERIE_SMARTPHONE_J * 100
    kpi_row([
        ("Energie estimee", fmt(energie, 1, " J"),
         f"~{nb_tokens_input} tok entree ({CARACTERES_PAR_TOKEN:.0f} car/tok) + {max_tokens} tok sortie"),
        ("Equivalent batterie smartphone", fmt(pct_batterie, 4, " %"), "sur ~4000 mAh (55 440 J)"),
    ])
    st.progress(min(pct_batterie / 100, 1.0))

    nb_requetes_pour_charge = BATTERIE_SMARTPHONE_J / energie
    st.markdown(f"**Il faudrait poser cette question environ "
                f"{nb_requetes_pour_charge:,.0f} fois**".replace(",", " ") +
                " pour consommer l'equivalent d'une charge complete de smartphone.")
    st.caption("Une requete individuelle est negligeable en elle-meme -- l'enjeu est le volume : "
               "des milliards de requetes IA sont envoyees chaque jour dans le monde.")

    if statut == "approximee":
        st.caption(":warning: Estimation lineaire (J/tok constant) -- pas de loi de longueur de prompt "
                   "mesuree pour ce modele/quantification. Precision moindre que Llama-3.2-1B Q4_K_M.")


# ============================================================
#  NAVIGATION PRINCIPALE
# ============================================================

st.markdown('<div class="hero-title">Energie LLM sur Raspberry Pi 5</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Stage LISTIC -- mesures energetiques d\'inference LLM quantifies</div>',
            unsafe_allow_html=True)

with st.expander(":material/info: Contexte -- a lire avant les graphes", expanded=False):
    st.markdown("""
**Ce qui est mesure.** Des LLM legers quantifies (Llama-3.2-1B, Qwen2.5-1.5B, Gemma-3-1B)
tournent en inference sur un Raspberry Pi 5 (16 Go). A chaque requete, l'energie consommee
est mesuree/estimee par **3 methodes en parallele** :
- **CodeCarbon** -- estimation logicielle par TDP (pas de compteur materiel sur ARM, donc peu fiable seule).
- **PMIC** -- mesure reelle onboard (`vcgencmd pmic_read_adc`), par composant (CPU, RAM...), ne voit pas le rail d'entree.
- **Prise connectee** -- mesure reelle au mur (Aeotec Z-Wave), inclut les pertes de l'alimentation, seule mesure du systeme total.

**Ce qui varie entre les modes ci-dessous** : n_threads, n_ctx, taille du prompt, modele/quantification --
chaque mode isole un seul parametre pour rester lisible (pas de croisement de filtres qui melangerait
des combinaisons jamais mesurees ensemble).

**Comment lire les graphes** : l'unite de reference est le **J/tok** (Joules par token genere) --
plus bas = plus efficace. Le detail methodologique complet est dans `docs/architecture_mesure.md`
et `docs/etat_de_lart.md`.
    """)

MODES = {
    "Impact n_threads": mode_nthreads,
    "Impact n_ctx": mode_nctx,
    "Impact taille prompt": mode_taille_prompt,
    "Vue globale modele/quantification": mode_vue_globale,
    "Comparaison 3 methodes (CodeCarbon/PMIC/Prise)": mode_comparaison_methodes,
    "Sensibilisation -- combien coute ta question ?": mode_sensibilisation,
}

mode = st.pills("Quelle question tu veux explorer ?", list(MODES.keys()), selection_mode="single",
                 default="Impact n_threads")
st.divider()
st.sidebar.markdown("### Filtres")
MODES[mode or "Impact n_threads"]()
