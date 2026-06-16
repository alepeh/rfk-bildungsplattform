import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { api, ApiError } from "../api";
import { useResource } from "../lib";
import { Alert, Field } from "../components/ui";

interface Ref {
  items: { id: string; name: string }[];
}

export function Register() {
  const nav = useNavigate();
  const { data: funktionen } = useResource<Ref>("/ref/funktionen");
  const { data: organisationen } = useResource<Ref>("/ref/organisationen");

  const [form, setForm] = useState({
    vorname: "",
    nachname: "",
    email: "",
    username: "",
    password: "",
    telefon: "",
    firmenname: "",
    firmenanschrift: "",
    adresse: "",
    plz: "",
    ort: "",
    funktion_id: "",
    organisation_id: "",
  });
  const [dsv, setDsv] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof typeof form>(k: K, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await api.post("/auth/register", {
        ...form,
        telefon: form.telefon || undefined,
        firmenname: form.firmenname || undefined,
        firmenanschrift: form.firmenanschrift || undefined,
        adresse: form.adresse || undefined,
        plz: form.plz || undefined,
        ort: form.ort || undefined,
        funktion_id: form.funktion_id || undefined,
        organisation_id: form.organisation_id || undefined,
        dsv_akzeptiert: true,
      });
      nav("/registrierung-erfolgreich");
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Registrierung fehlgeschlagen");
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="card card-pad auth-card wide">
        <h1 style={{ fontSize: "1.7rem" }}>Konto erstellen</h1>
        <p className="muted">
          Nach der Registrierung wird Ihr Konto von der Geschäftsstelle freigeschaltet.
        </p>
        <form onSubmit={submit} style={{ marginTop: 8 }}>
          {err && (
            <div style={{ marginBottom: 16 }}>
              <Alert kind="error">{err}</Alert>
            </div>
          )}
          <h3>Persönliche Daten</h3>
          <div className="grid cols-2" style={{ gap: 12 }}>
            <Field label="Vorname">
              <input className="input" value={form.vorname} onChange={(e) => set("vorname", e.target.value)} required />
            </Field>
            <Field label="Nachname">
              <input className="input" value={form.nachname} onChange={(e) => set("nachname", e.target.value)} required />
            </Field>
            <Field label="E-Mail">
              <input className="input" type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
            </Field>
            <Field label="Telefon">
              <input className="input" value={form.telefon} onChange={(e) => set("telefon", e.target.value)} />
            </Field>
            <Field label="Funktion">
              <select className="select" value={form.funktion_id} onChange={(e) => set("funktion_id", e.target.value)}>
                <option value="">Bitte wählen…</option>
                {funktionen?.items.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Organisation">
              <select className="select" value={form.organisation_id} onChange={(e) => set("organisation_id", e.target.value)}>
                <option value="">Keine / Externe</option>
                {organisationen?.items.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <h3 style={{ marginTop: 12 }}>Firma (optional)</h3>
          <div className="grid cols-2" style={{ gap: 12 }}>
            <Field label="Firmenname">
              <input className="input" value={form.firmenname} onChange={(e) => set("firmenname", e.target.value)} />
            </Field>
            <Field label="Firmenanschrift">
              <input className="input" value={form.firmenanschrift} onChange={(e) => set("firmenanschrift", e.target.value)} />
            </Field>
            <Field label="Adresse">
              <input className="input" value={form.adresse} onChange={(e) => set("adresse", e.target.value)} />
            </Field>
            <div className="grid cols-2" style={{ gap: 12 }}>
              <Field label="PLZ">
                <input className="input" value={form.plz} onChange={(e) => set("plz", e.target.value)} />
              </Field>
              <Field label="Ort">
                <input className="input" value={form.ort} onChange={(e) => set("ort", e.target.value)} />
              </Field>
            </div>
          </div>

          <h3 style={{ marginTop: 12 }}>Zugangsdaten</h3>
          <div className="grid cols-2" style={{ gap: 12 }}>
            <Field label="Benutzername">
              <input className="input" value={form.username} onChange={(e) => set("username", e.target.value)} required minLength={3} />
            </Field>
            <Field label="Passwort" hint="Mindestens 8 Zeichen">
              <input className="input" type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required minLength={8} />
            </Field>
          </div>

          <label className="checkbox" style={{ margin: "8px 0 20px" }}>
            <input type="checkbox" checked={dsv} onChange={(e) => setDsv(e.target.checked)} />
            <span>
              Ich habe die <Link to="/agb" target="_blank">Datenschutzvereinbarung</Link> gelesen und akzeptiere sie.
            </span>
          </label>

          <button className="btn btn-primary btn-block" disabled={busy || !dsv} type="submit">
            {busy ? "Wird gesendet…" : "Registrieren"}
          </button>
        </form>
        <p className="muted center" style={{ marginTop: 20, marginBottom: 0 }}>
          Bereits registriert? <Link to="/login">Anmelden</Link>
        </p>
      </div>
    </div>
  );
}
