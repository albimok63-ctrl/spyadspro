import os
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv
from google_ads_connector import connect_google_ads

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

google_client = connect_google_ads()

BASE_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEO_DETAILS_URL = "https://www.googleapis.com/youtube/v3/videos"

DB_PATH = "spyads.db"


# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS youtube_ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT,
        titolo TEXT,
        canale TEXT,
        data_pubblicazione TEXT,
        views INTEGER,
        likes INTEGER,
        comments INTEGER,
        engagement REAL,
        region TEXT,
        keyword TEXT,
        estrazione TEXT
    )
    """)
    conn.commit()
    conn.close()


# ================== FETCH VIDEO ==================
def fetch_videos(keyword, region="US", max_results=10):
    params = {
        "part": "snippet",
        "q": keyword,
        "regionCode": region,
        "maxResults": max_results,
        "type": "video",
        "key": API_KEY
    }
    res = requests.get(BASE_URL, params=params)
    res.raise_for_status()
    data = res.json()
    video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
    if not video_ids:
        return []

    # Otteniamo le metriche
    details_params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }
    res = requests.get(VIDEO_DETAILS_URL, params=details_params)
    res.raise_for_status()
    data = res.json()

    videos = []
    for v in data.get("items", []):
        stats = v.get("statistics", {})
        snippet = v.get("snippet", {})
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        engagement = round(((likes + comments) / views * 100), 2) if views > 0 else 0
        videos.append({
            "video_id": v["id"],
            "titolo": snippet.get("title", ""),
            "canale": snippet.get("channelTitle", ""),
            "data_pubblicazione": snippet.get("publishedAt", ""),
            "views": views,
            "likes": likes,
            "comments": comments,
            "engagement": engagement,
            "region": region,
            "keyword": keyword,
            "estrazione": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
    return videos


# ================== SALVATAGGIO ==================
def save_videos(videos):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for v in videos:
        c.execute("""
        INSERT INTO youtube_ads (video_id, titolo, canale, data_pubblicazione, views, likes, comments, engagement, region, keyword, estrazione)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            v["video_id"], v["titolo"], v["canale"], v["data_pubblicazione"],
            v["views"], v["likes"], v["comments"], v["engagement"],
            v["region"], v["keyword"], v["estrazione"]
        ))
    conn.commit()
    conn.close()


# ================== VALIDAZIONE ==================
def validate_trends(keyword):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    SELECT video_id, titolo, canale, views, likes, comments, engagement, estrazione
    FROM youtube_ads WHERE keyword=? ORDER BY estrazione DESC
    """, (keyword,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("[!] Nessun dato trovato per il confronto.")
        return

    print("\nVALIDATION SUMMARY\n======================")
    print(f"Keyword: {keyword}\n")

    latest = rows[:10]
    prev = rows[10:20] if len(rows) > 10 else []

    print(f"{'Titolo':60} {'Views':>10} {'Likes':>8} {'Comms':>8} {'Eng%':>7}")
    print("-" * 100)
    for v in latest:
        titolo, views, likes, comm, eng = v[1][:55], v[3], v[4], v[5], v[6]
        print(f"{titolo:<60} {views:>10} {likes:>8} {comm:>8} {eng:>7.2f}")

    if prev:
        print("\n📈 Confronto variazioni rispetto estrazione precedente:")
        for i in range(min(len(prev), len(latest))):
            dv = latest[i][3] - prev[i][3]
            dl = latest[i][4] - prev[i][4]
            dc = latest[i][5] - prev[i][5]
            print(f"- {latest[i][1][:40]}: ΔViews={dv:+}, ΔLikes={dl:+}, ΔComments={dc:+}")

    avg_eng = round(sum(v[6] for v in latest) / len(latest), 2)
    print(f"\nMedia Engagement Rate (%): {avg_eng}\n")
    print("Analisi completata ✅")


# ================== MAIN ==================
if __name__ == "__main__":
    init_db()
    print("[INFO] Avvio raccolta ed enrichment dati YouTube...")
    keyword = input("Inserisci una parola chiave per la ricerca: ")
    region = input("Inserisci area (es. IT, US, o lascia vuoto per globale): ") or "US"

    videos = fetch_videos(keyword, region)
    print(f"[INFO] {len(videos)} risultati trovati per '{keyword}'")
    save_videos(videos)
    print(f"[INFO] Salvati {len(videos)} video nel database.\n")
    validate_trends(keyword)