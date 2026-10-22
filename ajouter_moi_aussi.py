
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "projet.db"

if not DB_PATH.exists():
    raise SystemExit(
        f"Base de données introuvable : {DB_PATH}"
    )

connexion = sqlite3.connect(DB_PATH)

try:
    connexion.execute("PRAGMA foreign_keys = ON")

    connexion.execute("""
        CREATE TABLE IF NOT EXISTS soutiens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signalement_id INTEGER NOT NULL,
            telephone_citoyen TEXT NOT NULL,
            date_soutien TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (signalement_id)
                REFERENCES signalements(id)
                ON DELETE CASCADE,

            UNIQUE (signalement_id, telephone_citoyen)
        )
    """)

    connexion.execute("""
        CREATE INDEX IF NOT EXISTS idx_soutiens_signalement
        ON soutiens(signalement_id)
    """)

    connexion.commit()

    print("Fonctionnalité « Moi aussi » : table prête.")

    resultat = connexion.execute("""
        SELECT COUNT(*) FROM soutiens
    """).fetchone()[0]

    print(f"Nombre de soutiens actuellement enregistrés : {resultat}")
    print("Les signalements et interventions existants sont conservés.")

except sqlite3.Error as erreur:
    connexion.rollback()
    print(f"Erreur SQLite : {erreur}")

finally:
    connexion.close()
