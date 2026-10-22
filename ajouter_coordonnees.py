
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "projet.db"

if not DB_PATH.exists():
    raise SystemExit(f"Base de données introuvable : {DB_PATH}")

connexion = sqlite3.connect(DB_PATH)

try:
    colonnes = {
        ligne[1]
        for ligne in connexion.execute(
            "PRAGMA table_info(signalements)"
        ).fetchall()
    }

    if "latitude" not in colonnes:
        connexion.execute(
            "ALTER TABLE signalements ADD COLUMN latitude REAL"
        )
        print("Colonne latitude ajoutée.")

    if "longitude" not in colonnes:
        connexion.execute(
            "ALTER TABLE signalements ADD COLUMN longitude REAL"
        )
        print("Colonne longitude ajoutée.")

    connexion.commit()

    print("Migration terminée.")
    print("Les signalements et interventions existants sont conservés.")

except sqlite3.Error as erreur:
    connexion.rollback()
    print(f"Erreur SQLite : {erreur}")

finally:
    connexion.close()
