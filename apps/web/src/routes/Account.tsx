import { useState } from "react";
import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import { Alert, Field, PageHeader } from "../components/ui";

export function Account() {
  const { me } = useAuth();
  const [cur, setCur] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [msg, setMsg] = useState<{ kind: "error" | "success"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (next !== confirm) {
      setMsg({ kind: "error", text: "Die neuen Passwörter stimmen nicht überein." });
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      await api.post("/auth/change-password", { current_password: cur, new_password: next });
      setMsg({ kind: "success", text: "Passwort erfolgreich geändert." });
      setCur("");
      setNext("");
      setConfirm("");
    } catch (e) {
      setMsg({ kind: "error", text: e instanceof ApiError ? e.message : "Änderung fehlgeschlagen" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 620 }}>
        <PageHeader title="Mein Konto" subtitle={me ? `Angemeldet als ${me.username}` : undefined} />
        {me?.person && (
          <div className="card card-pad" style={{ marginBottom: 20 }}>
            <h3>Profil</h3>
            <div className="muted">
              {me.person.vorname} {me.person.nachname}
              <br />
              {me.person.email ?? me.email}
              {me.betrieb && (
                <>
                  <br />
                  Betrieb: {me.betrieb.name}
                </>
              )}
            </div>
          </div>
        )}
        <div className="card card-pad">
          <h3>Passwort ändern</h3>
          <form onSubmit={submit}>
            {msg && (
              <div style={{ marginBottom: 16 }}>
                <Alert kind={msg.kind}>{msg.text}</Alert>
              </div>
            )}
            <Field label="Aktuelles Passwort">
              <input className="input" type="password" value={cur} onChange={(e) => setCur(e.target.value)} required />
            </Field>
            <Field label="Neues Passwort" hint="Mindestens 8 Zeichen">
              <input className="input" type="password" value={next} onChange={(e) => setNext(e.target.value)} required minLength={8} />
            </Field>
            <Field label="Neues Passwort bestätigen">
              <input className="input" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} />
            </Field>
            <button className="btn btn-primary" disabled={busy} type="submit">
              {busy ? "Speichern…" : "Passwort ändern"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
