import os
import shutil

# Percorso base
BASE_DIR = os.path.join(os.getcwd(), "backend")

# File da rimuovere
REMOVE_FILES = [
    "backend.log",
    "test_keywords.py",
    "test_validation.py",
    "check_db_data.py",
    "youtube_scraper.py"
]

# File da spostare
MOVE_FILES = {
    "spyads.db": os.path.join(os.getcwd(), "frontend", "spyads.db")
}

print("🧹 Pulizia cartella backend in corso...\n")

# Rimuove file inutili
for file in REMOVE_FILES:
    path = os.path.join(BASE_DIR, file)
    if os.path.exists(path):
        os.remove(path)
        print(f"❌ Rimosso: {file}")

# Sposta database nel frontend
for src, dest in MOVE_FILES.items():
    src_path = os.path.join(BASE_DIR, src)
    if os.path.exists(src_path):
        shutil.move(src_path, dest)
        print(f"📦 Spostato: {src} → {dest}")

# Svuota cartella logs
logs_path = os.path.join(BASE_DIR, "logs")
if os.path.exists(logs_path):
    for f in os.listdir(logs_path):
        os.remove(os.path.join(logs_path, f))
    print("🗒️ Cartella logs svuotata.")

print("\n✅ Pulizia completata con successo!")