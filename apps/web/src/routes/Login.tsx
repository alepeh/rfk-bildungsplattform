import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { useAuth } from "../auth";
import { Alert, Field } from "../components/ui";
import { ApiError } from "../api";

export function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await login(username, password);
      nav("/");
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Anmeldung fehlgeschlagen");
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card card-pad auth-card">
        <h1 style={{ fontSize: "1.7rem" }}>Anmelden</h1>
        <p className="muted">Willkommen zurück bei der Bildungsplattform.</p>
        <form onSubmit={submit} style={{ marginTop: 8 }}>
          {err && (
            <div style={{ marginBottom: 16 }}>
              <Alert kind="error">{err}</Alert>
            </div>
          )}
          <Field label="Benutzername oder E-Mail">
            <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus required />
          </Field>
          <Field label="Passwort">
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </Field>
          <div style={{ textAlign: "right", marginBottom: 16, marginTop: -6 }}>
            <Link to="/passwort-vergessen" style={{ fontSize: "0.86rem" }}>
              Passwort vergessen?
            </Link>
          </div>
          <button className="btn btn-primary btn-block" disabled={busy} type="submit">
            {busy ? "Anmelden…" : "Anmelden"}
          </button>
        </form>
        <p className="muted center" style={{ marginTop: 20, marginBottom: 0 }}>
          Noch kein Konto? <Link to="/registrieren">Jetzt registrieren</Link>
        </p>
      </div>
    </div>
  );
}
