import sqlite3
import pandas as pd

DB_PATH = "spyads.db"

def validate_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 Inizio validazione dati...")

    # 1. Controllo duplicati
    df = pd.read_sql_query("SELECT * FROM youtube_ads", conn)
    duplicated = df[df.duplicated(subset=['video_id'], keep=False)]
    if not duplicated.empty:
        print(f"⚠️  Duplicati trovati: {len(duplicated)}")
    else:
        print("✅ Nessun duplicato trovato")

    # 2. Controllo valori nulli
    null_counts = df.isnull().sum()
    if null_counts.any():
        print("⚠️  Valori nulli trovati:")
        print(null_counts[null_counts > 0])
    else:
        print("✅ Nessun valore nullo trovato")

    # 3. Controllo timestamp e date
    if 'published_at' in df.columns:
        invalid_dates = df[~df['published_at'].str.match(r'^\d{4}-\d{2}-\d{2}')].shape[0]
        if invalid_dates > 0:
            print(f"⚠️  Date non valide trovate: {invalid_dates}")
        else:
            print("✅ Tutte le date valide")
    else:
        print("⚠️  Colonna 'published_at' mancante")

    # 4. Controllo numeri negativi (views, likes, ecc.)
    numeric_cols = [col for col in ['views', 'likes', 'comments'] if col in df.columns]
    for col in numeric_cols:
        negatives = (df[col] < 0).sum()
        if negatives > 0:
            print(f"⚠️  {negatives} valori negativi trovati in '{col}'")
        else:
            print(f"✅ Nessun valore negativo in '{col}'")

    print("\n🎯 Validazione completata con successo!")
    conn.close()

if __name__ == "__main__":
    validate_data()