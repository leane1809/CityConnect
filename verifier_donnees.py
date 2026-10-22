
import sqlite3
from pathlib import Path

# Utilise la base déjà présente dans le dossier du projet.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "projet.db"

if not DB_PATH.exists():
    print(f"ERREUR : base de données introuvable : {DB_PATH}")
    raise SystemExit(1)

# Connexion en lecture seule : aucune donnée ne sera modifiée.
connexion = sqlite3.connect(
    f"{DB_PATH.as_uri()}?mode=ro",
    uri=True
)

try:
    tables = [
        "categories",
        "quartiers",
        "agents",
        "signalements",
        "interventions"
    ]

    print("\n===== VERIFICATION DES DONNEES CITYCONNECT =====\n")

    for table in tables:
        # Les noms de tables viennent uniquement de la liste fixe ci-dessus.
        resultat = connexion.execute(
            f"SELECT COUNT(*) FROM [{table}]"
        ).fetchone()

        print(f"{table:20} : {resultat[0]}")

    print("\n===== DETAIL DES STATUTS =====\n")

    statuts = connexion.execute("""
        SELECT statut, COUNT(*) AS total
        FROM signalements
        GROUP BY statut
        ORDER BY statut
    """).fetchall()

    for statut, total in statuts:
        print(f"{statut:20} : {total}")

    print("\n===== VERIFICATION TERMINEE =====")
    print("Aucune donnée n'a été modifiée.")

finally:
    connexion.close()
