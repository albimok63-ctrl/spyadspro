import os
import sqlite3
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Carica variabili da .env (stesso folder del backend)
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") or os.getenv("YOUTUBE_API_KEY".upper()) or os.getenv("YOUTUBE_API_KEY".lower())

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
DETAILS_URL = "https://www.googleapis.com/youtube/v3/videos"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS youtube_ads (
    video_id TEXT PRIMARY KEY,
    titolo TEXT,
    canale TEXT,
    data_pubblicazione TEXT,
    views INTEGER,
    likes INTEGER,
    comments INTEGER,
    region TEXT,
    keyword TEXT,
    estrazione TEXT,
    engagement_rate REAL
);
"""

class YouTubeAds:
    def __init__(self, api_key: str | None = None, db_path: str = "spyads.db"):
        self.api_key = api_key or YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("⚠️ API Key di YouTube mancante! Imposta YOUTUBE_API_KEY nel file .env")
        self.db_path = db_path
        self._ensure_schema()

    # ---- DB helpers ---------------------------------------------------------
    def _ensure_schema(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(SCHEMA_SQL)
        # forza presenza delle colonne chiave anche se tabella esiste già
        cols = {r[1] for r in cur.execute("PRAGMA table_info(youtube_ads);").fetchall()}
        needed = {"engagement_rate","estrazione","keyword","region","likes","comments","views",
                  "video_id","titolo","canale","data_pubblicazione"}
        if not needed.issubset(cols):
            # ricrea tabella “morbida”: aggiunge colonne mancanti
            for col, typ in [
                ("engagement_rate","REAL"),("estrazione","TEXT"),("keyword","TEXT"),
                ("region","TEXT"),("likes","INTEGER"),("comments","INTEGER"),
                ("views","INTEGER"),("titolo","TEXT"),("canale","TEXT"),
                ("data_pubblicazione","TEXT")
            ]:
                if col not in cols:
                    try:
                        cur.execute(f"ALTER TABLE youtube_ads ADD COLUMN {col} {typ};")
                    except sqlite3.OperationalError:
                        pass
        conn.commit()
        conn.close()

    def save_to_db(self, items: list[dict]) -> tuple[int,int,int]:
        """Inserisce/aggiorna; ritorna (added, updated, ignored)."""
        added = updated = ignored = 0
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        sql = """
        INSERT INTO youtube_ads (
            video_id, titolo, canale, data_pubblicazione, views, likes, comments,
            region, keyword, estrazione, engagement_rate
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(video_id) DO UPDATE SET
            titolo=excluded.titolo,
            canale=excluded.canale,
            data_pubblicazione=excluded.data_pubblicazione,
            views=excluded.views,
            likes=excluded.likes,
            comments=excluded.comments,
            region=excluded.region,
            keyword=excluded.keyword,
            estrazione=excluded.estrazione,
            engagement_rate=excluded.engagement_rate;
        """
        for row in items:
            try:
                cur.execute(sql, (
                    row["video_id"], row["titolo"], row["canale"], row["data_pubblicazione"],
                    row["views"], row["likes"], row["comments"], row["region"], row["keyword"],
                    row["estrazione"], row["engagement_rate"]
                ))
                # se il video esisteva, count come updated
                updated += 1 if cur.rowcount == 0 else 0
                added += 1 if cur.rowcount == 1 else 0
            except sqlite3.IntegrityError:
                ignored += 1
            except Exception:
                ignored += 1
        conn.commit()
        conn.close()
        return added, updated, ignored

    # ---- YouTube API --------------------------------------------------------
    def _search_ids(self, keyword: str, region: str, max_results: int = 10) -> list[str]:
        params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "regionCode": region,
            "maxResults": max_results,
            "key": self.api_key
        }
        r = requests.get(SEARCH_URL, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return [it["id"]["videoId"] for it in data.get("items", []) if "id" in it and "videoId" in it["id"]]

    def _fetch_details(self, ids: list[str]) -> list[dict]:
        if not ids:
            return []
        params = {
            "part": "snippet,statistics",
            "id": ",".join(ids),
            "key": self.api_key
        }
        r = requests.get(DETAILS_URL, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("items", [])

    def fetch_videos(self, keyword: str, region: str = "US", max_results: int = 10) -> list[dict]:
        """Ritorna record completi + engagement_rate, pronti per il DB."""
        ids = self._search_ids(keyword, region, max_results=max_results)
        details = self._fetch_details(ids)
        now_iso = datetime.now(timezone.utc).isoformat()
        out: list[dict] = []
        for it in details:
            stats = it.get("statistics", {}) or {}
            snip = it.get("snippet", {}) or {}
            vid = it.get("id")
            views = int(stats.get("viewCount", 0) or 0)
            likes = int(stats.get("likeCount", 0) or 0)
            comments = int(stats.get("commentCount", 0) or 0)
            eng = ((likes + comments) / views * 100.0) if views > 0 else 0.0
            out.append({
                "video_id": vid,
                "titolo": snip.get("title", ""),
                "canale": (snip.get("channelTitle") or "").strip(),
                "data_pubblicazione": snip.get("publishedAt", ""),
                "views": views,
                "likes": likes,
                "comments": comments,
                "region": region,
                "keyword": keyword,
                "estrazione": now_iso,
                "engagement_rate": round(eng, 3),
            })
        return out

    # Alias per evitare futuri errori di naming
    def search_videos(self, *args, **kwargs):
        return self.fetch_videos(*args, **kwargs)