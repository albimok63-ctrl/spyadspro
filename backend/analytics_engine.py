# analytics_engine.py
# SpyAds Pro — Validazione + Trend Analysis (YouTube)
# Uso: python analytics_engine.py

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

DB_PATH = "spyads.db"
OUT_DIR = Path("reports")
OUT_DIR.mkdir(exist_ok=True)

def _load_df():
    con = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM youtube_ads", con)
    finally:
        con.close()
    if df.empty:
        print("⚠️  Nessun dato in youtube_ads.")
    return df

def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    # assicurati che esistano le colonne attese
    for c in ["video_id","titolo","canale","data_pubblicazione","views","likes","comments","keyword","region","estrazione","engagement_rate"]:
        if c not in df.columns:
            df[c] = pd.NA

    # tipizzazione
    df["views"]    = pd.to_numeric(df["views"], errors="coerce").fillna(0).astype(int)
    df["likes"]    = pd.to_numeric(df["likes"], errors="coerce").fillna(0).astype(int)
    df["comments"] = pd.to_numeric(df["comments"], errors="coerce").fillna(0).astype(int)
    df["engagement_rate"] = pd.to_numeric(df["engagement_rate"], errors="coerce").fillna(0.0).astype(float)
    df["estrazione_dt"] = pd.to_datetime(df["estrazione"], errors="coerce")
    df["data_pubblicazione_dt"] = pd.to_datetime(df["data_pubblicazione"], errors="coerce")
    df["keyword"] = df["keyword"].astype(str).str.strip().str.lower()
    df["region"]  = df["region"].astype(str).str.upper().str.strip()
    return df

def validate_df(df: pd.DataFrame) -> dict:
    rep = {}
    rep["rows_total"] = len(df)
    rep["null_video_id"] = int(df["video_id"].isna().sum())
    rep["dup_video_id"]  = int(df.duplicated(subset=["video_id"], keep=False).sum())
    rep["invalid_dates"] = int(df["estrazione_dt"].isna().sum())
    # sospetti: views == 0 ma likes > 0
    rep["suspicious"] = int(((df["views"] == 0) & (df["likes"] > 0)).sum())
    return rep

def _pct(a, b):
    # variazione percentuale da b -> a
    if b == 0:
        return 0.0
    return round((a - b) / b * 100.0, 2)

def trend_per_video(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola trend (Δ%) per singolo video_id confrontando l'ultima estrazione
    con la precedente (se disponibile).
    """
    if df["estrazione_dt"].isna().all():
        return pd.DataFrame()

    df = df.sort_values(["video_id","estrazione_dt"])
    last = df.groupby("video_id").tail(1).rename(columns={
        "views":"views_now", "likes":"likes_now", "comments":"comments_now", "engagement_rate":"er_now"
    })
    prev = df.groupby("video_id").nth(-2).reset_index().rename(columns={
        "views":"views_prev", "likes":"likes_prev", "comments":"comments_prev", "engagement_rate":"er_prev"
    })

    merged = pd.merge(last[["video_id","titolo","canale","keyword","region","views_now","likes_now","comments_now","er_now","estrazione_dt"]],
                      prev[["video_id","views_prev","likes_prev","comments_prev","er_prev"]],
                      on="video_id", how="left")

    # calcola Δ%
    merged["Δviews_%"] = merged.apply(lambda r: _pct(r["views_now"], r["views_prev"] if pd.notna(r["views_prev"]) else 0), axis=1)
    merged["Δlikes_%"] = merged.apply(lambda r: _pct(r["likes_now"], r["likes_prev"] if pd.notna(r["likes_prev"]) else 0), axis=1)
    merged["ΔER_%"]    = merged.apply(lambda r: _pct(r["er_now"],    r["er_prev"]    if pd.notna(r["er_prev"])    else 0), axis=1)

    # ordina per crescita ER
    merged = merged.sort_values("ΔER_%", ascending=False)
    return merged

def trend_per_keyword(df: pd.DataFrame) -> pd.DataFrame:
    """
    Confronta la media per keyword tra l'ultima finestra temporale e la precedente.
    Usa la penultima e l’ultima 'estrazione_dt' globali come finestre semplici.
    """
    if df["estrazione_dt"].isna().all():
        return pd.DataFrame()

    # individua due snapshot temporali (globali) più recenti
    snaps = sorted(df["estrazione_dt"].dropna().dt.floor("min").unique())
    if len(snaps) < 2:
        return pd.DataFrame()

    snap_now  = snaps[-1]
    snap_prev = snaps[-2]

    cur  = df[df["estrazione_dt"] == snap_now]
    prev = df[df["estrazione_dt"] == snap_prev]

    g_now  = cur.groupby("keyword", as_index=False).agg(
        views_now=("views","mean"),
        likes_now=("likes","mean"),
        er_now=("engagement_rate","mean"),
        n_now=("video_id","count")
    )
    g_prev = prev.groupby("keyword", as_index=False).agg(
        views_prev=("views","mean"),
        likes_prev=("likes","mean"),
        er_prev=("engagement_rate","mean"),
        n_prev=("video_id","count")
    )

    m = pd.merge(g_now, g_prev, on="keyword", how="left")
    m["Δviews_%"] = m.apply(lambda r: _pct(r["views_now"], r["views_prev"] if pd.notna(r["views_prev"]) else 0), axis=1)
    m["Δlikes_%"] = m.apply(lambda r: _pct(r["likes_now"], r["likes_prev"] if pd.notna(r["likes_prev"]) else 0), axis=1)
    m["ΔER_%"]    = m.apply(lambda r: _pct(r["er_now"],    r["er_prev"]    if pd.notna(r["er_prev"])    else 0), axis=1)

    m = m.sort_values("ΔER_%", ascending=False)
    m["snap_prev"] = snap_prev
    m["snap_now"]  = snap_now
    return m

def save_reports(df_valid: pd.DataFrame, per_video: pd.DataFrame, per_kw: pd.DataFrame):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    p_base = OUT_DIR / f"analytics_{ts}"
    p_base.mkdir(exist_ok=True)

    df_valid.to_csv(p_base / "dataset_clean.csv", index=False)
    per_video.to_csv(p_base / "trend_per_video.csv", index=False)
    per_kw.to_csv(p_base / "trend_per_keyword.csv", index=False)

    print(f"\n📁 Report salvati in: {p_base}")

def print_console_summary(val_report: dict, per_video: pd.DataFrame, per_kw: pd.DataFrame):
    print("\n================ VALIDATION SUMMARY ================")
    for k, v in val_report.items():
        print(f"- {k}: {v}")
    print("====================================================")

    if not per_kw.empty:
        print("\n🏷️  Top keyword per crescita ER (ultime 2 estrazioni):")
        print(per_kw[["keyword","ΔER_%","n_now","snap_prev","snap_now"]].head(5).to_string(index=False))

    if not per_video.empty:
        print("\n🎬 Top video in crescita ER (ultime 2 estrazioni):")
        cols = ["video_id","titolo","canale","keyword","ΔER_%","views_now","likes_now"]
        print(per_video[cols].head(5).to_string(index=False))

def main():
    df = _load_df()
    if df.empty:
        return

    df = _coerce_types(df)
    val = validate_df(df)

    # versione “clean” per output (dedup per video_id, tieni ultima estrazione)
    df_clean = (df.sort_values(["video_id","estrazione_dt"])
                  .drop_duplicates(subset=["video_id"], keep="last")
                  .reset_index(drop=True))

    per_vid = trend_per_video(df)
    per_kw  = trend_per_keyword(df)

    save_reports(df_clean, per_vid, per_kw)
    print_console_summary(val, per_vid, per_kw)
    print("\n✅ Analytics completata.")

if __name__ == "__main__":
    main()