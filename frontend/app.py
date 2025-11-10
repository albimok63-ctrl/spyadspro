import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="SpyAds Pro – Dashboard", layout="wide")

BACKEND_URL = "http://127.0.0.1:8000/get_youtube_data"

st.title("🎯 SpyAds Pro — Dashboard Performance Video & Ads")

# --- Carica dati dal backend ---
@st.cache_data(ttl=60)
def fetch_data():
    try:
        r = requests.get(BACKEND_URL, timeout=10)
        r.raise_for_status()
        payload = r.json()
        if payload["status"] == "ok":
            df = pd.DataFrame(payload["data"])
            return df
        else:
            st.error(f"Errore dal backend: {payload['message']}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Errore di connessione al backend: {e}")
        return pd.DataFrame()

df = fetch_data()

if df.empty:
    st.warning("⚠️ Nessun dato disponibile. Assicurati che il backend sia attivo.")
    st.stop()

# --- Filtri laterali ---
st.sidebar.header("🎛️ Filtri di ricerca")

keyword = st.sidebar.text_input("🔍 Parola chiave (titolo o canale):")
canale = st.sidebar.selectbox("📺 Canale", ["Tutti"] + sorted(df["canale"].dropna().unique().tolist()))
ordinamento = st.sidebar.selectbox("📊 Ordina per", ["views", "likes", "comments", "engagement_rate"])

# --- Applica filtri ---
filtered = df.copy()
if keyword:
    filtered = filtered[filtered["titolo"].str.contains(keyword, case=False, na=False) | 
                        filtered["canale"].str.contains(keyword, case=False, na=False)]
if canale != "Tutti":
    filtered = filtered[filtered["canale"] == canale]

filtered = filtered.sort_values(by=ordinamento, ascending=False)

# --- Mostra risultati ---
st.success(f"{len(filtered)} risultati trovati")
st.dataframe(filtered, use_container_width=True)