import sqlite3

# Connessione al database
conn = sqlite3.connect("spyads.db")
c = conn.cursor()

print("\n📊 Controllo colonne della tabella youtube_ads:\n")

# Mostra lo schema attuale
c.execute("PRAGMA table_info(youtube_ads)")
columns = c.fetchall()

for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close()