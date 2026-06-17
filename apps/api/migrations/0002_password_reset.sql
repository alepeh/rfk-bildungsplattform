-- Password-reset tokens. Additive migration (R-002 house style).
-- The emailed token is a random URL-safe string; only its SHA-256 hash is
-- stored here, single-use (used_at) and time-limited (expires_at).

CREATE TABLE password_reset (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL,                  -- -> users.id
  token_hash TEXT NOT NULL,                  -- SHA-256 hex of the emailed token
  expires_at TEXT NOT NULL,
  used_at    TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX idx_pwreset_token ON password_reset(token_hash);
CREATE INDEX idx_pwreset_user ON password_reset(user_id);
