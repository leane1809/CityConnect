
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "projet.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def initialiser_base():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Fichier SQL introuvable : {SCHEMA_PATH}"
        )

    with sqlite3.connect(DB_PATH) as connexion:
        connexion.execute("PRAGMA foreign_keys = ON")

        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connexion.executescript(schema)

        categories = [
            ("voirie", "Service de la voirie"),
            ("ordures", "Service de propreté"),
            ("éclairage", "Service de l'éclairage public"),
            ("eau", "Service hydraulique"),
            ("autre", "Services municipaux"),
        ]

        connexion.executemany(
            """
            INSERT OR IGNORE INTO categories
                (nom, service_responsable)
            VALUES (?, ?)
            """,
            categories,
        )

        quartiers = [
            "Akwa",
            "Bonanjo",
            "Bonapriso",
            "Deido",
            "Bali",
            "Bépanda",
            "Makepe",
            "Logpom",
            "Kotto",
            "Bonamoussadi",
            "New Bell",
            "Ndogpassi",
        ]

        connexion.executemany(
            """
            INSERT OR IGNORE INTO quartiers (nom)
            VALUES (?)
            """,
            [(quartier,) for quartier in quartiers],
        )

        agents = [
            ("Agent Voirie", "Service de la voirie", "voirie"),
            ("Agent Propreté", "Service de propreté", "ordures"),
            ("Agent Éclairage", "Service de l'éclairage public", "eclairage"),
            ("Agent Eau", "Service hydraulique", "eau"),
            ("Agent Municipal 1", "Services municipaux", "municipal1"),
            ("Agent Municipal 2", "Services municipaux", "municipal2"),
            ("Agent Voirie 2", "Service de la voirie", "voirie2"),
            ("Responsable Municipal", "Services municipaux", "responsable"),
        ]

        for nom, service, login in agents:
            connexion.execute(
                """
                INSERT OR IGNORE INTO agents
                    (nom, service, login, mot_de_passe_hash)
                VALUES (?, ?, ?, ?)
                """,
                (
                    nom,
                    service,
                    login,
                    generate_password_hash(
                        "Demo-2026-change-moi"
                    ),
                ),
            )

    print("Base de données initialisée avec succès.")
    print(f"Emplacement : {DB_PATH}")
    print("Catégories : 5")
    print("Quartiers : 12")
    print("Agents de démonstration : 8")
    # print("Attention : les mots de passe de démonstration doivent être changés.")


if __name__ == "__main__":
    initialiser_base()
