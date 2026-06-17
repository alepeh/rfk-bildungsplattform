import { useState } from "react";
import { Link } from "react-router";
import { api, ApiError } from "../api";
import { Alert, Field } from "../components/ui";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await api.post("/auth/forgot-password", { email });
      setSent(true);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Anfrage fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card card-pad auth-card">
        {sent ? (
          <div className="center">
            <div style={{ fontSize: "2.6rem", marginBottom: 8 }}>✉️</div>
            <h1 style={{ fontSize: "1.6rem" }}>E-Mail unterwegs</h1>
            <p className="muted">
              Falls ein Konto mit dieser Adresse existiert, haben wir einen Link zum Zurücksetzen
              des Passworts gesendet. Der Link ist 60 Minuten gültig.
            </p>
            <Link to="/login" className="btn btn-primary btn-block" style={{ marginTop: 12 }}>
              Zur Anmeldung
            </Link>
          </div>
        ) : (
          <>
            <h1 style={{ fontSize: "1.7rem" }}>Passwort vergessen?</h1>
            <p className="muted">
              Geben Sie Ihre E-Mail-Adresse ein. Wir senden Ihnen einen Link zum Zurücksetzen.
            </p>
            <form onSubmit={submit} style={{ marginTop: 8 }}>
              {err && (
                <div style={{ marginBottom: 16 }}>
                  <Alert kind="error">{err}</Alert>
                </div>
              )}
              <Field label="E-Mail">
                <input
                  className="input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoFocus
                  required
                />
              </Field>
              <button className="btn btn-primary btn-block" disabled={busy} type="submit">
                {busy ? "Senden…" : "Link anfordern"}
              </button>
            </form>
            <p className="muted center" style={{ marginTop: 20, marginBottom: 0 }}>
              <Link to="/login">Zurück zur Anmeldung</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
