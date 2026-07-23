-- Schema Phase 0 (relances + devis) - SQLite, migration vers Postgres a faire
-- separement (cf CLAUDE.md section 4 : "decidee" mais non commencee).
-- Reconstruit a partir du contrat verifie par les tests de services/relances/
-- et services/devis/ (chaque test charge ce fichier dans une base SQLite en
-- memoire) - colonnes volontairement limitees a ce que ce code utilise.
-- Non fait a ce stade (cf services/devis/README.md) : generation LLM/PDF des
-- devis, mentions legales/TVA, bibliotheque de prix (data/price-library/,
-- pas encore recu).

CREATE TABLE artisans (
    id INTEGER PRIMARY KEY,
    nom_entreprise TEXT NOT NULL,
    metier TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE clients (
    id INTEGER PRIMARY KEY,
    artisan_id INTEGER NOT NULL REFERENCES artisans(id),
    nom TEXT NOT NULL,
    email TEXT,
    telephone TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX clients_artisan_id_idx ON clients (artisan_id);

CREATE TABLE devis (
    id INTEGER PRIMARY KEY,
    artisan_id INTEGER NOT NULL REFERENCES artisans(id),
    client_id INTEGER NOT NULL REFERENCES clients(id),
    statut TEXT NOT NULL DEFAULT 'brouillon',
    montant_total REAL NOT NULL,
    valide_par_artisan INTEGER NOT NULL DEFAULT 0,
    date_envoi TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX devis_artisan_id_idx ON devis (artisan_id);

CREATE TABLE factures (
    id INTEGER PRIMARY KEY,
    artisan_id INTEGER NOT NULL REFERENCES artisans(id),
    client_id INTEGER NOT NULL REFERENCES clients(id),
    statut TEXT NOT NULL DEFAULT 'emise',
    montant_total REAL NOT NULL,
    date_echeance TEXT NOT NULL,
    date_paiement TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX factures_artisan_id_idx ON factures (artisan_id);

-- Sequencement J+3/J+7/J+15 (engine.PALIERS) ; anti-doublon gere en code
-- (engine._paliers_deja_envoyes), pas par contrainte DB - cf engine.py.
CREATE TABLE relances (
    id INTEGER PRIMARY KEY,
    artisan_id INTEGER NOT NULL REFERENCES artisans(id),
    cible_type TEXT NOT NULL,
    cible_id INTEGER NOT NULL,
    canal TEXT NOT NULL,
    palier INTEGER NOT NULL,
    envoyee_le TEXT NOT NULL,
    interrompue INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX relances_artisan_id_idx ON relances (artisan_id);
