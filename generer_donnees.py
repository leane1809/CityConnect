
import random
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

DOSSIER = Path(__file__).resolve().parent
BASE_DONNEES = DOSSIER / "projet.db"

OBJECTIF_SIGNALEMENTS = 200
OBJECTIF_INTERVENTIONS = 250

STATUTS = ["nouveau", "en cours", "résolu", "rejeté"]

DESCRIPTIONS = [
    "Présence de nombreux nids-de-poule sur cette route.",
    "Des ordures s'accumulent depuis plusieurs jours.",
    "Plusieurs lampadaires ne fonctionnent plus la nuit.",
    "Une fuite d'eau importante est visible sur la chaussée.",
    "Le passage des piétons est bloqué par des déchets.",
    "La chaussée est fortement dégradée à cet endroit.",
    "Un dépôt sauvage d'ordures gêne la circulation.",
    "L'éclairage public est en panne dans cette rue.",
    "Une canalisation semble endommagée près des habitations.",
    "Un problème de voirie nécessite une intervention rapide.",
]

COMMENTAIRES = [
    "Signalement examiné par le service concerné.",
    "Une visite sur le terrain est programmée.",
    "Le problème a été transmis à l'équipe technique.",
    "Une intervention est en cours de préparation.",
    "Les travaux nécessaires ont été réalisés.",
    "Le problème a été vérifié par un agent.",
    "Une vérification complémentaire est nécessaire.",
    "Le dossier a été examiné par le service municipal.",
    "Le signalement a été traité par l'équipe technique.",
    "Le signalement ne peut pas être traité en l'état.",
]


def date_aleatoire(debut, fin):
    """Retourne une date aléatoire entre deux dates."""
    ecart = max(0, int((fin - debut).total_seconds()))
    return debut + timedelta(seconds=random.randint(0, ecart))


def main():
    if not BASE_DONNEES.exists():
        print("ERREUR : projet.db est introuvable.")
        print("Vérifie que ce fichier est à la racine de CityConnect.")
        return

    maintenant = datetime.now().replace(microsecond=0)
    debut_periode = maintenant - timedelta(days=89)

    connexion = sqlite3.connect(BASE_DONNEES)
    connexion.execute("PRAGMA foreign_keys = ON")

    try:
        with connexion:
            # Vérifier les tables et les données de référence.
            tables = {
                ligne[0]
                for ligne in connexion.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }

            tables_requises = {
                "categories",
                "quartiers",
                "agents",
                "signalements",
                "interventions",
            }

            if not tables_requises.issubset(tables):
                raise RuntimeError(
                    "Certaines tables sont absentes. "
                    "Vérifie schema.sql et init_db.py."
                )

            categories = connexion.execute(
                "SELECT id FROM categories"
            ).fetchall()

            quartiers = connexion.execute(
                "SELECT id FROM quartiers"
            ).fetchall()

            agents = connexion.execute(
                "SELECT id FROM agents WHERE actif = 1"
            ).fetchall()

            if not categories or not quartiers or not agents:
                raise RuntimeError(
                    "Il faut au moins une catégorie, un quartier "
                    "et un agent actif."
                )

            # 1. Ajouter des signalements sans supprimer l'existant.
            total = connexion.execute(
                "SELECT COUNT(*) FROM signalements"
            ).fetchone()[0]

            codes_demo = connexion.execute(
                """
                SELECT id, date_creation
                FROM signalements
                WHERE code_suivi LIKE 'DEMO-%'
                ORDER BY id
                """
            ).fetchall()

            while total < OBJECTIF_SIGNALEMENTS or not codes_demo:
                date_creation = date_aleatoire(
                    debut_periode, maintenant
                )

                statut = random.choice(STATUTS)

                code = "DEMO-" + secrets.token_hex(5).upper()

                curseur = connexion.execute(
                    """
                    INSERT INTO signalements (
                        categorie_id,
                        quartier_id,
                        description,
                        photo,
                        adresse,
                        telephone_citoyen,
                        date_creation,
                        statut,
                        code_suivi,
                        motif_rejet
                    )
                    VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        random.choice(categories)[0],
                        random.choice(quartiers)[0],
                        random.choice(DESCRIPTIONS),
                        f"Rue de démonstration {random.randint(1, 150)}",
                        f"6{random.randint(50000000, 99999999)}",
                        date_creation.isoformat(sep=" "),
                        statut,
                        code,
                        (
                            "Motif de démonstration : signalement non recevable."
                            if statut == "rejeté"
                            else None
                        ),
                    ),
                )

                codes_demo.append(
                    (curseur.lastrowid, date_creation.isoformat(sep=" "))
                )
                total += 1

            # Convertir les signalements de démonstration en liste
            # avec leur date de création.
            signalements_demo = [
                (identifiant, datetime.fromisoformat(date_texte))
                for identifiant, date_texte in codes_demo
            ]

            # 2. Ajouter les interventions jusqu'à 250 au total.
            total_interventions = connexion.execute(
                "SELECT COUNT(*) FROM interventions"
            ).fetchone()[0]

            while total_interventions < OBJECTIF_INTERVENTIONS:
                signalement_id, date_signalement = random.choice(
                    signalements_demo
                )

                date_intervention = date_aleatoire(
                    date_signalement, maintenant
                )

                nouveau_statut = random.choice(STATUTS)

                commentaire = random.choice(COMMENTAIRES)

                if nouveau_statut == "rejeté":
                    commentaire = (
                        "Motif de démonstration : signalement "
                        "non recevable après vérification."
                    )

                connexion.execute(
                    """
                    INSERT INTO interventions (
                        signalement_id,
                        agent_id,
                        date_intervention,
                        commentaire,
                        nouveau_statut
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        signalement_id,
                        random.choice(agents)[0],
                        date_intervention.isoformat(sep=" "),
                        commentaire,
                        nouveau_statut,
                    ),
                )

                total_interventions += 1

            # 3. Mettre à jour le statut des seuls signalements DEMO
            # à partir de leur intervention la plus récente.
            connexion.execute(
                """
                UPDATE signalements
                SET statut = (
                    SELECT i.nouveau_statut
                    FROM interventions AS i
                    WHERE i.signalement_id = signalements.id
                    ORDER BY i.date_intervention DESC, i.id DESC
                    LIMIT 1
                ),
                motif_rejet = CASE
                    WHEN (
                        SELECT i.nouveau_statut
                        FROM interventions AS i
                        WHERE i.signalement_id = signalements.id
                        ORDER BY i.date_intervention DESC, i.id DESC
                        LIMIT 1
                    ) = 'rejeté'
                    THEN 'Motif de démonstration : signalement non recevable.'
                    ELSE NULL
                END
                WHERE code_suivi LIKE 'DEMO-%'
                AND EXISTS (
                    SELECT 1
                    FROM interventions AS i
                    WHERE i.signalement_id = signalements.id
                )
                """
            )

        # Afficher les résultats après validation de la transaction.
        print("\nGÉNÉRATION TERMINÉE")
        print("-------------------")

        for table in ("categories", "quartiers", "agents",
                      "signalements", "interventions"):
            nombre = connexion.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table} : {nombre}")

        nombre_demo = connexion.execute(
            """
            SELECT COUNT(*)
            FROM signalements
            WHERE code_suivi LIKE 'DEMO-%'
            """
        ).fetchone()[0]

        print(f"Signalements de démonstration : {nombre_demo}")
        # print("Les données existantes n'ont pas été supprimées.")

    except Exception as erreur:
        print(f"\nERREUR : {erreur}")
        print("La transaction a été annulée si une erreur est survenue.")
    finally:
        connexion.close()


if __name__ == "__main__":
    main()
