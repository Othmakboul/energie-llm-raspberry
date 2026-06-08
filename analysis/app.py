"""Interface de visualisation (Streamlit).

Lancer :  streamlit run analysis/app.py
Lit le CSV des mesures et affiche des comparaisons du coût par prompt.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

RACINE = Path(__file__).resolve().parents[1]
CSV = RACINE / "data" / "raw" / "mesures.csv"

st.set_page_config(page_title="Énergie LLM sur Raspberry Pi", layout="wide")
st.title("Coût énergétique d'un LLM embarqué")

if not CSV.exists():
    st.warning(f"Aucune mesure trouvée. Lancez d'abord une campagne (→ {CSV}).")
    st.stop()

df = pd.read_csv(CSV)
st.subheader("Données brutes")
st.dataframe(df, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Durée par catégorie de prompt")
    if "categorie" in df:
        st.bar_chart(df.groupby("categorie")["duree_s"].mean())
with col2:
    st.subheader("Énergie vs tokens générés")
    if "energie_kwh" in df and df["energie_kwh"].notna().any():
        st.scatter_chart(df, x="n_tokens_generes", y="energie_kwh")
    else:
        st.info("Pas encore de données d'énergie.")
