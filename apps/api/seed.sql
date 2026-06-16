-- Local development seed. Idempotent (INSERT OR IGNORE on fixed IDs).
-- Admin login:  username "admin"  /  password "admin12345"  (dev only).

INSERT OR IGNORE INTO users (id, email, username, password_hash, is_active, is_staff, is_superuser)
VALUES ('u-admin', 'admin@example.com', 'admin',
        'pbkdf2$100000$xRLlhjpkzJCWrhzgldY76w$JWxveSHZBIVNxgE5zyrh-r1v19CTKUTpM-oTS5c_5xA',
        1, 1, 1);

INSERT OR IGNORE INTO funktion (id, name, sortierung) VALUES
  ('f-meister', 'Rauchfangkehrermeister', 1),
  ('f-geselle', 'Geselle', 2),
  ('f-lehrling', 'Lehrling', 3);

INSERT OR IGNORE INTO organisation (id, name, preisrabatt) VALUES
  ('o-wtg', 'WTG Burgenland', 1),
  ('o-extern', 'Externe Teilnehmer', 0);

INSERT OR IGNORE INTO schulungsart (id, name) VALUES
  ('sa-sicherheit', 'Sicherheitsschulung'),
  ('sa-technik', 'Technik & Feuerungsanlagen');

INSERT OR IGNORE INTO schulungsort (id, name, adresse, plz, ort, kontakt, telefon, email) VALUES
  ('ort-eisenstadt', 'WIFI Burgenland', 'Wienerstraße 150', '7000', 'Eisenstadt', 'Frau Müller', '+43 2682 12345', 'kurse@wifi-bgld.at');

-- Admin profile (activated).
INSERT OR IGNORE INTO person (id, user_id, vorname, nachname, email, funktion_id, organisation_id,
        dsv_akzeptiert, is_activated, can_book_schulungen)
VALUES ('p-admin', 'u-admin', 'Admin', 'RFK', 'admin@example.com', 'f-meister', 'o-wtg', 1, 1, 1);

-- A sample course with two upcoming sessions.
INSERT OR IGNORE INTO schulung (id, name, beschreibung, art_id, preis_standard, preis_rabattiert) VALUES
  ('s-grund', 'Jährliche Sicherheitsunterweisung',
   'Pflichtschulung zu Arbeitssicherheit, Brandschutz und aktuellen Vorschriften für das Rauchfangkehrerhandwerk.',
   'sa-sicherheit', 18000, 12000),
  ('s-technik', 'Moderne Feuerungsanlagen',
   'Technische Grundlagen moderner Heizsysteme, Emissionsmessung und Wartung.',
   'sa-technik', 24000, 18000);

INSERT OR IGNORE INTO schulungstermin (id, schulung_id, ort_id, datum_von, datum_bis, dauer, max_teilnehmer, min_teilnehmer, buchbar) VALUES
  ('t-grund-1', 's-grund', 'ort-eisenstadt', '2026-09-15T09:00:00Z', '2026-09-15T17:00:00Z', '1 Tag', 25, 5, 1),
  ('t-technik-1', 's-technik', 'ort-eisenstadt', '2026-10-08T09:00:00Z', '2026-10-08T16:00:00Z', '1 Tag', 20, 4, 1);
