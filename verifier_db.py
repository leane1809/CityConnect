
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "projet.db"

with sqlite3.connect(db_path) as connexion:
    tables = connexion.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' ORDER BY name"
    ).fetchall()

    print("TABLES TROUVEES :")
    for table in tables:
        print("-", table[0])

    for table in ("categories", "quartiers", "agents",
                  "signalements", "interventions"):
        nombre = connexion.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        print(f"{table} : {nombre}")
