
import os
from flask_wtf.csrf import CSRFProtect
import re
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from functools import wraps
from uuid import uuid4
from PIL import Image, UnidentifiedImageError

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, abort
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "projet.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_PHOTO_SIZE = 2 * 1024 * 1024

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "cle-de-developpement-a-remplacer"
)

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

csrf = CSRFProtect(app)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", secrets.token_hex(32)
)
app.config["MAX_CONTENT_LENGTH"] = MAX_PHOTO_SIZE + 1024 * 1024
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    connexion = sqlite3.connect(DB_PATH)
    connexion.row_factory = sqlite3.Row
    connexion.execute("PRAGMA foreign_keys = ON")
    return connexion


def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def agent_connecte(fonction):
    @wraps(fonction)
    def wrapper(*args, **kwargs):
        if "agent_id" not in session:
            flash("Connecte-toi pour accéder à cet espace.", "warning")
            return redirect(url_for("connexion"))
        return fonction(*args, **kwargs)
    return wrapper


@app.errorhandler(404)
def page_introuvable(error):
    return render_template("404.html"), 404


@app.errorhandler(413)
def fichier_trop_volumineux(error):
    flash("La requête est trop volumineuse. La photo doit faire moins de 2 Mo.", "danger")
    return redirect(url_for("signaler"))

EXTENSIONS_AUTORISEES = {"jpg", "jpeg", "png"}
FORMATS_IMAGE_AUTORISES = {"JPEG", "PNG"}


def enregistrer_photo(fichier):
    """
    Vérifie le contenu réel de l'image puis l'enregistre
    sous un nom généré par le serveur.
    Retourne le nom du fichier ou None si aucune photo n'est fournie.
    """
    if not fichier or not fichier.filename:
        return None

    nom_original = fichier.filename.strip()

    if "." not in nom_original:
        raise ValueError("Le fichier doit être une image JPG, JPEG ou PNG.")

    extension = nom_original.rsplit(".", 1)[1].lower()

    if extension not in EXTENSIONS_AUTORISEES:
        raise ValueError("Seuls les fichiers JPG, JPEG et PNG sont autorisés.")

    contenu = fichier.stream

    

    try:
        contenu.seek(0)

        with Image.open(contenu) as image:
            format_reel = image.format

            if format_reel not in FORMATS_IMAGE_AUTORISES:
                raise ValueError("Le contenu du fichier n'est pas une image JPG ou PNG.")

            image.verify()

        contenu.seek(0)

        with Image.open(contenu) as image:
            if image.format != format_reel:
                raise ValueError("Le contenu du fichier est incohérent.")

    except (UnidentifiedImageError, OSError) as erreur:
        raise ValueError("Le fichier envoyé est une image invalide.") from erreur
    finally:
        contenu.seek(0)

    dossier_upload = app.config.get(
        "UPLOAD_FOLDER",
        os.path.join(app.root_path, "static", "uploads")
    )

    os.makedirs(dossier_upload, exist_ok=True)

    extension_reelle = "jpg" if format_reel == "JPEG" else "png"
    nom_securise = f"{uuid4().hex}.{extension_reelle}"

    fichier.save(os.path.join(dossier_upload, nom_securise))

    return nom_securise

@app.route("/")
def accueil():
    with get_db() as db:
        signalements = db.execute("""SELECT
            s.id,
            s.description,
            s.adresse,
            s.statut,
            s.date_creation,
            s.code_suivi,
            c.nom AS categorie,
            q.nom AS quartier,
            COUNT(st.id) AS nb_soutiens
        FROM signalements s
        JOIN categories c ON c.id = s.categorie_id
        JOIN quartiers q ON q.id = s.quartier_id
        LEFT JOIN soutiens st ON st.signalement_id = s.id
        WHERE s.statut != 'rejeté'
        GROUP BY
            s.id,
            s.description,
            s.adresse,
            s.statut,
            s.date_creation,
            s.code_suivi,
            c.nom,
            q.nom
        ORDER BY s.date_creation DESC
        LIMIT 20
    """).fetchall()
        
        categories = db.execute(
            "SELECT COUNT(*) FROM categories"
        ).fetchone()[0]

        total = db.execute(
            "SELECT COUNT(*) FROM signalements WHERE statut != 'rejeté'"
        ).fetchone()[0]

        resolus = db.execute(
            "SELECT COUNT(*) FROM signalements WHERE statut = 'résolu'"
        ).fetchone()[0]

    return render_template(
        "index.html",
        signalements=signalements,
        total=total,
        resolus=resolus,
        nb_categories=categories
    )


@app.route("/signalement/<int:signalement_id>/moi-aussi", methods=["POST"])
def soutenir_signalement(signalement_id):
    telephone = request.form.get("telephone_soutien", "").strip()

    # Normaliser le numéro pour limiter les doublons de format.
    telephone_normalise = re.sub(r"\D", "", telephone)

    if not 6 <= len(telephone_normalise) <= 15:
        flash("Entre un numéro de téléphone valide.", "danger")
        return redirect(url_for("accueil"))

    with get_db() as db:
        signalement = db.execute("""
            SELECT id
            FROM signalements
            WHERE id = ? AND statut != 'rejeté'
        """, (signalement_id,)).fetchone()

        if not signalement:
            abort(404)

        try:
            db.execute("""
                INSERT INTO soutiens (
                    signalement_id,
                    telephone_citoyen
                )
                VALUES (?, ?)
            """, (signalement_id, telephone_normalise))

            flash("Merci ! Ton soutien a été enregistré.", "success")

        except sqlite3.IntegrityError:
            flash(
                "Ce numéro a déjà soutenu ce signalement.",
                "warning"
            )

    return redirect(url_for("accueil"))



@app.route("/signaler", methods=["GET", "POST"])

def signaler():
    with get_db() as db:
        categories = db.execute(
            "SELECT id, nom FROM categories ORDER BY nom"
        ).fetchall()
        quartiers = db.execute(
            "SELECT id, nom FROM quartiers ORDER BY nom"
        ).fetchall()

    if request.method == "POST":
        categorie_id = request.form.get("categorie_id", "").strip()
        quartier_id = request.form.get("quartier_id", "").strip()
        description = request.form.get("description", "").strip()
        adresse = request.form.get("adresse", "").strip()
        telephone = request.form.get("telephone", "").strip()

        # Coordonnées facultatives : elles seront renseignées
        # grâce à la carte dans le formulaire.
        latitude_form = request.form.get("latitude", "").strip()
        longitude_form = request.form.get("longitude", "").strip()

        fichier = request.files.get("photo")

        def afficher_formulaire():
            return render_template(
                "signaler.html",
                categories=categories,
                quartiers=quartiers
            )

        if not all([
            categorie_id, quartier_id, description,
            adresse, telephone
        ]):
            flash(
                "Tous les champs obligatoires doivent être remplis.",
                "danger"
            )
            return afficher_formulaire()

        if len(description) < 20:
            flash(
                "La description doit contenir au moins 20 caractères.",
                "danger"
            )
            return afficher_formulaire()

        if not re.fullmatch(r"[0-9+(). \-]{6,25}", telephone):
            flash("Le numéro de téléphone n'est pas valide.", "danger")
            return afficher_formulaire()

        # Vérifier que la catégorie et le quartier existent.
        with get_db() as db:
            categorie_valide = db.execute(
                "SELECT id FROM categories WHERE id = ?",
                (categorie_id,)
            ).fetchone()

            quartier_valide = db.execute(
                "SELECT id FROM quartiers WHERE id = ?",
                (quartier_id,)
            ).fetchone()

        if not categorie_valide or not quartier_valide:
            flash(
                "La catégorie ou le quartier sélectionné est invalide.",
                "danger"
            )
            return afficher_formulaire()

        # Vérifier les coordonnées GPS si elles sont fournies.
        latitude = None
        longitude = None

        if latitude_form or longitude_form:
            try:
                latitude = float(latitude_form)
                longitude = float(longitude_form)

                if not (
                    -90 <= latitude <= 90
                    and -180 <= longitude <= 180
                ):
                    raise ValueError
            except (ValueError, TypeError):
                flash(
                    "La position GPS est invalide. "
                    "Sélectionne un point sur la carte.",
                    "danger"
                )
                return afficher_formulaire()

        # Enregistrer la photo, si elle existe.
        photo_nom = None

        if fichier and fichier.filename:
            if len(fichier.read()) > 2 * 1024 * 1024:
                flash("La photo ne doit pas dépasser 2 Mo.", "danger")
                return afficher_formulaire()

            fichier.stream.seek(0)

            try:
                photo_nom = enregistrer_photo(fichier)
            except ValueError as erreur:
                flash(str(erreur), "danger")
                return afficher_formulaire()

        code_suivi = (
            secrets.token_urlsafe(8)
            .replace("-", "")
            .replace("_", "")[:12]
            .upper()
        )

        try:
            with get_db() as db:
                curseur = db.execute("""
                    INSERT INTO signalements (
                        categorie_id,
                        quartier_id,
                        description,
                        photo,
                        adresse,
                        telephone_citoyen,
                        code_suivi,
                        latitude,
                        longitude
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(categorie_id),
                    int(quartier_id),
                    description,
                    photo_nom,
                    adresse,
                    telephone,
                    code_suivi,
                    latitude,
                    longitude
                ))

                signalement_id = curseur.lastrowid

        except sqlite3.Error:
            if photo_nom:
                (UPLOAD_DIR / photo_nom).unlink(missing_ok=True)

            app.logger.exception(
                "Erreur lors de l'enregistrement du signalement"
            )

            flash(
                "Impossible d'enregistrer le signalement. Réessaie.",
                "danger"
            )
            return afficher_formulaire()

        flash(
            f"Signalement enregistré ! Ton code de suivi est : {code_suivi}",
            "success"
        )

        return redirect(url_for("suivi", code=code_suivi))

    return render_template(
        "signaler.html",
        categories=categories,
        quartiers=quartiers
    )



@app.route("/suivi", methods=["GET", "POST"])
def suivi():
    code = request.args.get("code", "").strip().upper()

    if request.method == "POST":
        code = request.form.get("code_suivi", "").strip().upper()
        if not code:
            flash("Entre ton code de suivi.", "warning")
            return redirect(url_for("suivi"))
        return redirect(url_for("suivi", code=code))

    signalement = None
    interventions = []

    if code:
        with get_db() as db:
            signalement = db.execute("""
                SELECT s.*, c.nom AS categorie, q.nom AS quartier
                FROM signalements s
                JOIN categories c ON c.id = s.categorie_id
                JOIN quartiers q ON q.id = s.quartier_id
                WHERE s.code_suivi = ?
            """, (code,)).fetchone()

            if signalement:
                interventions = db.execute("""
                    SELECT i.date_intervention, i.commentaire,
                           i.nouveau_statut, a.nom AS agent
                    FROM interventions i
                    JOIN agents a ON a.id = i.agent_id
                    WHERE i.signalement_id = ?
                    ORDER BY i.date_intervention DESC, i.id DESC
                """, (signalement["id"],)).fetchall()

        if not signalement:
            flash("Aucun signalement trouvé pour ce code.", "warning")

    return render_template(
        "suivi.html", signalement=signalement,
        interventions=interventions, code=code
    )


@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        mot_de_passe = request.form.get("mot_de_passe", "")

        with get_db() as db:
            agent = db.execute("""
                SELECT id, nom, service, login, mot_de_passe_hash
                FROM agents
                WHERE login = ? AND actif = 1
            """, (login,)).fetchone()

        if agent and check_password_hash(
            agent["mot_de_passe_hash"], mot_de_passe
        ):
            session.clear()
            session["agent_id"] = agent["id"]
            session["agent_nom"] = agent["nom"]
            session["agent_service"] = agent["service"]
            return redirect(url_for("admin"))

        flash("Identifiants incorrects.", "danger")

    return render_template("connexion.html")


@app.route("/deconnexion", methods=["POST"])
def deconnexion():
    session.clear()
    flash("Tu es déconnecté.", "success")
    return redirect(url_for("accueil"))


@app.route("/admin")
@agent_connecte
def admin():
    with get_db() as db:
        signalements = db.execute("""
            SELECT s.id, s.description, s.adresse, s.statut,
                   s.date_creation, s.code_suivi,
                   c.nom AS categorie, c.service_responsable,
                   q.nom AS quartier
            FROM signalements s
            JOIN categories c ON c.id = s.categorie_id
            JOIN quartiers q ON q.id = s.quartier_id
            WHERE c.service_responsable = ?
            ORDER BY
                CASE s.statut
                    WHEN 'nouveau' THEN 0
                    WHEN 'en cours' THEN 1
                    ELSE 2
                END,
                s.date_creation ASC
        """, (session["agent_service"],)).fetchall()

    return render_template("admin.html", signalements=signalements)


@app.route("/admin/intervention/<int:signalement_id>", methods=["POST"])
@agent_connecte
def ajouter_intervention(signalement_id):
    commentaire = request.form.get("commentaire", "").strip()
    nouveau_statut = request.form.get("nouveau_statut", "").strip()
    motif_rejet = request.form.get("motif_rejet", "").strip()

    statuts = {"en cours", "résolu", "rejeté"}

    if not commentaire:
        flash("Le commentaire de l'intervention est obligatoire.", "danger")
        return redirect(url_for("admin"))

    if nouveau_statut not in statuts:
        flash("Statut invalide.", "danger")
        return redirect(url_for("admin"))

    if nouveau_statut == "rejeté" and not motif_rejet:
        flash("Indique le motif du rejet.", "danger")
        return redirect(url_for("admin"))

    with get_db() as db:
        signalement = db.execute("""
            SELECT s.id, s.statut, c.service_responsable
            FROM signalements s
            JOIN categories c ON c.id = s.categorie_id
            WHERE s.id = ?
        """, (signalement_id,)).fetchone()

        if (
            not signalement
            or signalement["service_responsable"] != session["agent_service"]
        ):
            abort(404)

        db.execute("""
            INSERT INTO interventions (
                signalement_id, agent_id, commentaire, nouveau_statut
            ) VALUES (?, ?, ?, ?)
        """, (
            signalement_id, session["agent_id"], commentaire, nouveau_statut
        ))

        db.execute("""
            UPDATE signalements
            SET statut = ?, motif_rejet = ?
            WHERE id = ?
        """, (
            nouveau_statut,
            motif_rejet if nouveau_statut == "rejeté" else None,
            signalement_id
        ))

    flash("Intervention enregistrée.", "success")
    return redirect(url_for("admin"))



@app.route("/api/statistiques")
def api_statistiques():
    with get_db() as db:
        # 1. Signalements par catégorie (hors signalements rejetés)
        par_categorie = db.execute("""
            SELECT c.nom AS categorie, COUNT(s.id) AS total
            FROM categories c
            LEFT JOIN signalements s
                ON s.categorie_id = c.id
                AND s.statut != 'rejeté'
            GROUP BY c.id, c.nom
            ORDER BY total DESC
        """).fetchall()

        # 2. Signalements par quartier
        par_quartier = db.execute("""
            SELECT q.nom AS quartier, COUNT(s.id) AS total
            FROM quartiers q
            LEFT JOIN signalements s
                ON s.quartier_id = q.id
                AND s.statut != 'rejeté'
            GROUP BY q.id, q.nom
            ORDER BY total DESC
        """).fetchall()

        # 3. Signalements nouveaux ou en cours depuis au moins 7 jours
        non_traites = db.execute("""
            SELECT COUNT(*)
            FROM signalements
            WHERE statut IN ('nouveau', 'en cours')
              AND datetime(date_creation) <= datetime('now', '-7 days')
        """).fetchone()[0]

        # 4. Évolution hebdomadaire des signalements
        evolution = db.execute("""
            SELECT strftime('%Y-%W', date_creation) AS semaine,
                   COUNT(*) AS total
            FROM signalements
            WHERE statut != 'rejeté'
            GROUP BY strftime('%Y-%W', date_creation)
            ORDER BY semaine
        """).fetchall()

        # 5. Délai de résolution par service.
        # On retient la première intervention qui marque le signalement
        # comme résolu, pour ne compter chaque signalement qu'une fois.
        delais = db.execute("""
            WITH premieres_resolutions AS (
                SELECT
                    i.signalement_id,
                    MIN(datetime(i.date_intervention)) AS date_resolution
                FROM interventions i
                WHERE i.nouveau_statut = 'résolu'
                GROUP BY i.signalement_id
            )
            SELECT
                c.service_responsable AS service,
                ROUND(
                    AVG(
                        julianday(pr.date_resolution) -
                        julianday(s.date_creation)
                    ),
                    2
                ) AS delai_moyen_jours,
                COUNT(s.id) AS signalements_resolus
            FROM premieres_resolutions pr
            JOIN signalements s ON s.id = pr.signalement_id
            JOIN categories c ON c.id = s.categorie_id
            GROUP BY c.service_responsable
            ORDER BY c.service_responsable
        """).fetchall()

    return jsonify({
        "signalements_par_categorie": [
            dict(r) for r in par_categorie
        ],
        "signalements_par_quartier": [
            dict(r) for r in par_quartier
        ],
        "signalements_nouveaux_non_traites_depuis_7_jours": non_traites,
        "evolution_hebdomadaire": [
            dict(r) for r in evolution
        ],
        "delai_moyen_resolution_par_service": [
            dict(r) for r in delais
        ]
    })


@app.route("/api/signalements")
def api_signalements():
    with get_db() as db:
        signalements = db.execute("""
            SELECT
                s.id,
                s.description,
                s.adresse,
                s.date_creation,
                s.statut,
                s.code_suivi,
                c.nom AS categorie,
                q.nom AS quartier
            FROM signalements s
            JOIN categories c ON c.id = s.categorie_id
            JOIN quartiers q ON q.id = s.quartier_id
            WHERE s.statut != 'rejeté'
            ORDER BY s.date_creation DESC
            LIMIT 50
        """).fetchall()

    return jsonify({
        "total": len(signalements),
        "signalements": [dict(s) for s in signalements]
    })


@app.route("/api/carte-signalements", methods=["GET"])
def api_carte_signalements():
    with get_db() as db:
        lignes = db.execute("""
            SELECT
                s.id,
                s.description,
                s.adresse,
                s.latitude,
                s.longitude,
                s.date_creation,
                s.statut,
                c.nom AS categorie,
                q.nom AS quartier
            FROM signalements s
            JOIN categories c ON c.id = s.categorie_id
            JOIN quartiers q ON q.id = s.quartier_id
            WHERE s.latitude IS NOT NULL
              AND s.longitude IS NOT NULL
              AND s.latitude BETWEEN -90 AND 90
              AND s.longitude BETWEEN -180 AND 180
              AND s.statut != 'rejeté'
            ORDER BY s.date_creation DESC
        """).fetchall()

    signalements = [
        {
            "id": ligne["id"],
            "description": ligne["description"],
            "adresse": ligne["adresse"],
            "latitude": ligne["latitude"],
            "longitude": ligne["longitude"],
            "date_creation": ligne["date_creation"],
            "statut": ligne["statut"],
            "categorie": ligne["categorie"],
            "quartier": ligne["quartier"]
        }
        for ligne in lignes
    ]

    return jsonify(signalements)


@app.route("/carte")
def carte_signalements():
    return render_template("carte.html")


if __name__ == "__main__":
    app.run(debug=False)
