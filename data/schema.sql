-- PROPOSÉ — schéma Phase 0 initial (artisans, clients, devis, factures,
-- relances), pas encore validé. Toute table métier porte artisan_id :
-- isolation stricte par tenant obligatoire (principe 5, CLAUDE.md).
--
-- L'extension (dossier chantier, engagements, micro-CRM, logbook, role,
-- session par device) doit se faire en une seule passe, pas ici — cf
-- CLAUDE.md §6 "Extension de schéma — une seule passe".

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE artisans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL UNIQUE,
    nom TEXT NOT NULL,
    metier TEXT NOT NULL DEFAULT 'plombier',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artisan_id UUID NOT NULL REFERENCES artisans(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    email TEXT,
    telephone TEXT,
    adresse TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX clients_artisan_id_idx ON clients (artisan_id);

CREATE TABLE devis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artisan_id UUID NOT NULL REFERENCES artisans(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    statut TEXT NOT NULL DEFAULT 'brouillon',
    montant_ht NUMERIC(10, 2),
    contenu TEXT,
    valide_par_artisan BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX devis_artisan_id_idx ON devis (artisan_id);

CREATE TABLE factures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artisan_id UUID NOT NULL REFERENCES artisans(id) ON DELETE CASCADE,
    devis_id UUID REFERENCES devis(id) ON DELETE SET NULL,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    statut TEXT NOT NULL DEFAULT 'emise',
    montant_ttc NUMERIC(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX factures_artisan_id_idx ON factures (artisan_id);

-- Séquencement J+3/J+7/J+15, anti-doublon via UNIQUE(devis_id, palier).
CREATE TABLE relances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artisan_id UUID NOT NULL REFERENCES artisans(id) ON DELETE CASCADE,
    devis_id UUID NOT NULL REFERENCES devis(id) ON DELETE CASCADE,
    palier TEXT NOT NULL CHECK (palier IN ('j3', 'j7', 'j15')),
    envoyee_at TIMESTAMPTZ,
    desactivee BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (devis_id, palier)
);
CREATE INDEX relances_artisan_id_idx ON relances (artisan_id);

-- Corpus RAG — filtrage artisan_id obligatoire sur toute requête vectorielle
-- (principe 5 : une requête sans filtre tenant est un bug critique).
CREATE TABLE corpus_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artisan_id UUID NOT NULL REFERENCES artisans(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    contenu TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX corpus_documents_artisan_id_idx ON corpus_documents (artisan_id);
