import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router";
import { api, ApiError } from "../api";
import { Alert, Field } from "../components/ui";

export function ResetPassword() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const token = params.get("token") ?? "";
  const [pw, setPw] = useState("");
  const [confirm, setConfirm] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (pw !== confirm) {
      setErr("Die Passwörter stimmen nicht überein.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await api.post("/auth/reset-password", { token, new_password: pw });
      setDone(true);
      setTimeout(() => nav("/login"), 2500);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Zurücksetzen fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card card-pad auth-card">
        {!token ? (
          <div className="center">
            <h1 style={{ fontSize: "1.6rem" }}>Ungültiger Link</h1>
            <p className="muted">Dieser Link ist unvollständig. Bitte fordern Sie einen neuen an.</p>
            <Link to="/passwort-vergessen" className="btn btn-primary btn-block" style={{ marginTop: 12 }}>
              Neuen Link anfordern
            </Link>
          </div>
        ) : done ? (
          <div className="center">
            <div style={{ fontSize: "2.6rem", marginBottom: 8 }}>✅</div>
            <h1 style={{ fontSize: "1.6rem" }}>Passwort geändert</h1>
            <p className="muted">Sie werden zur Anmeldung weitergeleitet…</p>
            <Link to="/login" className="btn btn-primary btn-block" style={{ marginTop: 12 }}>
              Jetzt anmelden
            </Link>
          </div>
        ) : (
          <>
            <h1 style={{ fontSize: "1.7rem" }}>Neues Passwort</h1>
            <p className="muted">Vergeben Sie ein neues Passwort für Ihr Konto.</p>
            <form onSubmit={submit} style={{ marginTop: 8 }}>
              {err && (
                <div style={{ marginBottom: 16 }}>
                  <Alert kind="error">{err}</Alert>
                </div>
              )}
              <Field label="Neues Passwort" hint="Mindestens 8 Zeichen">
                <input
                  className="input"
                  type="password"
                  value={pw}
                  onChange={(e) => setPw(e.target.value)}
                  required
                  minLength={8}
                  autoFocus
                />
              </Field>
              <Field label="Passwort bestätigen">
                <input
                  className="input"
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                  minLength={8}
                />
              </Field>
              <button className="btn btn-primary btn-block" disabled={busy} type="submit">
                {busy ? "Speichern…" : "Passwort festlegen"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
