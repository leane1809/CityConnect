
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    service_responsable TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quartiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    service TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    mot_de_passe_hash TEXT NOT NULL,
    actif INTEGER NOT NULL DEFAULT 1
        CHECK (actif IN (0, 1))
);

CREATE TABLE IF NOT EXISTS signalements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categorie_id INTEGER NOT NULL,
    quartier_id INTEGER NOT NULL,
    description TEXT NOT NULL
        CHECK (length(trim(description)) >= 20),
    photo TEXT,
    adresse TEXT NOT NULL,
    telephone_citoyen TEXT NOT NULL,
    date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    statut TEXT NOT NULL DEFAULT 'nouveau'
        CHECK (statut IN ('nouveau', 'en cours', 'résolu', 'rejeté')),
    code_suivi TEXT NOT NULL UNIQUE,
    motif_rejet TEXT,

    FOREIGN KEY (categorie_id)
        REFERENCES categories(id),
    FOREIGN KEY (quartier_id)
        REFERENCES quartiers(id)
);

CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signalement_id INTEGER NOT NULL,
    agent_id INTEGER NOT NULL,
    date_intervention TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    commentaire TEXT NOT NULL,
    nouveau_statut TEXT NOT NULL
        CHECK (nouveau_statut IN ('nouveau', 'en cours', 'résolu', 'rejeté')),

    FOREIGN KEY (signalement_id)
        REFERENCES signalements(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id)
        REFERENCES agents(id)
);

CREATE INDEX IF NOT EXISTS idx_signalements_categorie
    ON signalements(categorie_id);

CREATE INDEX IF NOT EXISTS idx_signalements_quartier
    ON signalements(quartier_id);

CREATE INDEX IF NOT EXISTS idx_signalements_statut
    ON signalements(statut);

CREATE INDEX IF NOT EXISTS idx_signalements_date
    ON signalements(date_creation);

CREATE INDEX IF NOT EXISTS idx_interventions_signalement
    ON interventions(signalement_id);

CREATE INDEX IF NOT EXISTS idx_interventions_agent
    ON interventions(agent_id);
