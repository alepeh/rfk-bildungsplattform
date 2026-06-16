-- RFK Bildungsplattform — initial D1 schema
-- Faithful port of the legacy Django domain (see legacy/core/models.py).
--
-- House style (architecture/guidelines.md): TEXT UUID primary keys, ISO-8601
-- UTC TEXT timestamps, enums as TEXT + CHECK, and NO foreign-key constraints
-- (D1 convention — referential integrity is enforced in application code).
-- Relationships are documented in comments and backed by indexes.
--
-- Domain vocabulary is German and intentionally preserved. Auth lives in
-- `users`; the master profile record is `person` (a person may exist without
-- a login account). Money is stored in cents (INTEGER) to avoid float drift.

-- ── Auth ─────────────────────────────────────────────────────────────
CREATE TABLE users (
  id            TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE,
  username      TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  is_active     INTEGER NOT NULL DEFAULT 0,   -- login enabled only after activation
  is_staff      INTEGER NOT NULL DEFAULT 0,
  is_superuser  INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- ── Reference / taxonomy ─────────────────────────────────────────────
CREATE TABLE organisation (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  preisrabatt INTEGER NOT NULL DEFAULT 0,     -- members get the discounted price
  created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE funktion (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  sortierung INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE schulungsart (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Minimum training requirement: which course type a role needs, and how often.
CREATE TABLE schulungsart_funktion (
  id              TEXT PRIMARY KEY,
  schulungsart_id TEXT NOT NULL,              -- -> schulungsart.id
  funktion_id     TEXT NOT NULL,              -- -> funktion.id
  intervall       INTEGER NOT NULL            -- repeat interval (years), informational
);
CREATE INDEX idx_saf_schulungsart ON schulungsart_funktion(schulungsart_id);
CREATE INDEX idx_saf_funktion ON schulungsart_funktion(funktion_id);

CREATE TABLE schulungsort (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  adresse    TEXT,
  plz        TEXT,
  ort        TEXT,
  kontakt    TEXT,
  telefon    TEXT,
  email      TEXT,
  hinweise   TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- ── Businesses & people ──────────────────────────────────────────────
CREATE TABLE betrieb (
  id                   TEXT PRIMARY KEY,
  name                 TEXT NOT NULL,
  kehrgebiet           TEXT,
  adresse              TEXT,
  plz                  TEXT,
  ort                  TEXT,
  telefon              TEXT,
  email                TEXT,
  geschaeftsfuehrer_id TEXT,                  -- -> person.id (managing director)
  created_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX idx_betrieb_gf ON betrieb(geschaeftsfuehrer_id);

CREATE TABLE person (
  id                      TEXT PRIMARY KEY,
  user_id                 TEXT UNIQUE,        -- -> users.id (nullable)
  vorname                 TEXT NOT NULL,
  nachname                TEXT NOT NULL,
  email                   TEXT,
  telefon                 TEXT,
  firmenname              TEXT,
  firmenanschrift         TEXT,
  adresse                 TEXT,
  plz                     TEXT,
  ort                     TEXT,
  dsv_akzeptiert          INTEGER NOT NULL DEFAULT 0,
  funktion_id             TEXT,               -- -> funktion.id
  organisation_id         TEXT,               -- -> organisation.id
  betrieb_id              TEXT,               -- -> betrieb.id
  is_activated            INTEGER NOT NULL DEFAULT 0,
  activation_requested_at TEXT,
  activated_at            TEXT,
  activated_by_id         TEXT,               -- -> users.id
  can_book_schulungen     INTEGER NOT NULL DEFAULT 1,
  created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX idx_person_betrieb ON person(betrieb_id);
CREATE INDEX idx_person_funktion ON person(funktion_id);
CREATE INDEX idx_person_organisation ON person(organisation_id);
CREATE INDEX idx_person_user ON person(user_id);

-- ── Courses ──────────────────────────────────────────────────────────
CREATE TABLE schulung (
  id               TEXT PRIMARY KEY,
  name             TEXT NOT NULL,
  beschreibung     TEXT NOT NULL DEFAULT '',
  art_id           TEXT,                      -- -> schulungsart.id
  preis_standard   INTEGER NOT NULL DEFAULT 0, -- cents
  preis_rabattiert INTEGER,                   -- cents, nullable
  created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Eligibility: which roles a course is suitable for (empty = no restriction).
CREATE TABLE schulung_funktion (
  schulung_id TEXT NOT NULL,                  -- -> schulung.id
  funktion_id TEXT NOT NULL,                  -- -> funktion.id
  PRIMARY KEY (schulung_id, funktion_id)
);

CREATE TABLE schulungstermin (
  id             TEXT PRIMARY KEY,
  schulung_id    TEXT NOT NULL,              -- -> schulung.id
  ort_id         TEXT,                       -- -> schulungsort.id
  datum_von      TEXT NOT NULL,
  datum_bis      TEXT NOT NULL,
  dauer          TEXT,
  max_teilnehmer INTEGER NOT NULL DEFAULT 0,
  min_teilnehmer INTEGER NOT NULL DEFAULT 0,
  buchbar        INTEGER NOT NULL DEFAULT 1,
  created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX idx_termin_schulung ON schulungstermin(schulung_id);
CREATE INDEX idx_termin_datum ON schulungstermin(datum_von);

-- ── Orders & participants ────────────────────────────────────────────
CREATE TABLE bestellung (
  id                       TEXT PRIMARY KEY,
  person_id                TEXT,             -- -> person.id (buyer)
  schulungstermin_id       TEXT NOT NULL,    -- -> schulungstermin.id
  anzahl                   INTEGER NOT NULL,
  einzelpreis              INTEGER NOT NULL, -- cents, snapshot at purchase
  gesamtpreis              INTEGER NOT NULL, -- cents
  status                   TEXT NOT NULL DEFAULT 'Bestellt'
                             CHECK (status IN ('Bestellt','Storniert')),
  rechnungsadresse_name    TEXT,
  rechnungsadresse_strasse TEXT,
  rechnungsadresse_plz     TEXT,
  rechnungsadresse_ort     TEXT,
  created_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at               TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX idx_bestellung_person ON bestellung(person_id);
CREATE INDEX idx_bestellung_termin ON bestellung(schulungstermin_id);

CREATE TABLE schulungsteilnehmer (
  id                 TEXT PRIMARY KEY,
  schulungstermin_id TEXT NOT NULL,          -- -> schulungstermin.id
  bestellung_id      TEXT,                   -- -> bestellung.id (nullable)
  person_id          TEXT,                   -- -> person.id (nullable; external = snapshot)
  vorname            TEXT,
  nachname           TEXT,
  email              TEXT,
  verpflegung        TEXT NOT NULL DEFAULT 'Standard'
                       CHECK (verpflegung IN ('Standard','Vegetarisch')),
  status             TEXT NOT NULL DEFAULT 'Angemeldet'
                       CHECK (status IN ('Angemeldet','Teilgenommen','Entschuldigt','Unentschuldigt')),
  created_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX idx_teilnehmer_termin ON schulungsteilnehmer(schulungstermin_id);
CREATE INDEX idx_teilnehmer_bestellung ON schulungsteilnehmer(bestellung_id);
CREATE INDEX idx_teilnehmer_person ON schulungsteilnehmer(person_id);

-- ── Documents (blobs live in R2; metadata here) ──────────────────────
CREATE TABLE document (
  id           TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  description  TEXT,
  r2_key       TEXT NOT NULL,
  filename     TEXT NOT NULL,
  content_type TEXT,
  size         INTEGER,
  created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

-- Access control: empty set = visible to everyone.
CREATE TABLE document_funktion (
  document_id TEXT NOT NULL,                  -- -> document.id
  funktion_id TEXT NOT NULL,                  -- -> funktion.id
  PRIMARY KEY (document_id, funktion_id)
);

CREATE TABLE schulungsunterlage (
  id           TEXT PRIMARY KEY,
  schulung_id  TEXT NOT NULL,                 -- -> schulung.id
  name         TEXT NOT NULL,
  description  TEXT,
  r2_key       TEXT NOT NULL,
  filename     TEXT NOT NULL,
  content_type TEXT,
  size         INTEGER,
  created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX idx_unterlage_schulung ON schulungsunterlage(schulung_id);

-- ── Internal todo / issue tracker (admin only) ───────────────────────
CREATE TABLE todo (
  id           TEXT PRIMARY KEY,
  typ          TEXT NOT NULL CHECK (typ IN ('Fehler','Erweiterung')),
  prioritaet   TEXT NOT NULL DEFAULT 'Niedrig'
                 CHECK (prioritaet IN ('Niedrig','Mittel','Hoch')),
  name         TEXT NOT NULL,
  beschreibung TEXT NOT NULL DEFAULT '',
  erledigt     INTEGER NOT NULL DEFAULT 0,
  created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
  updated_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE comment (
  id         TEXT PRIMARY KEY,
  todo_id    TEXT NOT NULL,                   -- -> todo.id
  user_id    TEXT,                            -- -> users.id
  text       TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX idx_comment_todo ON comment(todo_id);
