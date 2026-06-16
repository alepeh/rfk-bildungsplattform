import { useState } from "react";
import { api, ApiError } from "../api";
import { useResource } from "../lib";
import { Spinner, Alert, Badge, Empty, Field, PageHeader } from "../components/ui";

interface Employee {
  id: string;
  vorname: string;
  nachname: string;
  email: string | null;
  telefon: string | null;
  funktion_id: string | null;
  funktion_name: string | null;
  has_login: number;
}
interface Funktion {
  id: string;
  name: string;
}

const blank = { vorname: "", nachname: "", email: "", telefon: "", funktion_id: "" };

export function Mitarbeiter() {
  const list = useResource<{ items: Employee[]; geschaeftsfuehrer_id: string }>("/mitarbeiter");
  const { data: funktionen } = useResource<{ items: Funktion[] }>("/ref/funktionen");
  const [form, setForm] = useState(blank);
  const [editId, setEditId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof typeof blank>(k: K, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }
  function reset() {
    setForm(blank);
    setEditId(null);
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    const body = {
      vorname: form.vorname,
      nachname: form.nachname,
      email: form.email || null,
      telefon: form.telefon || null,
      funktion_id: form.funktion_id || null,
    };
    try {
      if (editId) await api.put(`/mitarbeiter/${editId}`, body);
      else await api.post("/mitarbeiter", body);
      reset();
      list.reload();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: string) {
    if (!confirm("Mitarbeiter wirklich entfernen?")) return;
    try {
      await api.del(`/mitarbeiter/${id}`);
      list.reload();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Löschen fehlgeschlagen");
    }
  }

  function edit(emp: Employee) {
    setEditId(emp.id);
    setForm({
      vorname: emp.vorname,
      nachname: emp.nachname,
      email: emp.email ?? "",
      telefon: emp.telefon ?? "",
      funktion_id: emp.funktion_id ?? "",
    });
  }

  return (
    <div className="page">
      <div className="container">
        <PageHeader
          title="Mitarbeiter verwalten"
          subtitle="Erfassen Sie Ihre Mitarbeiter, um sie zu Schulungen anzumelden."
        />
        {err && (
          <div style={{ marginBottom: 16 }}>
            <Alert kind="error">{err}</Alert>
          </div>
        )}
        <div className="grid cols-2" style={{ alignItems: "start" }}>
          <div className="card card-pad">
            <h3>{editId ? "Mitarbeiter bearbeiten" : "Neuer Mitarbeiter"}</h3>
            <form onSubmit={save}>
              <div className="grid cols-2" style={{ gap: 10 }}>
                <Field label="Vorname">
                  <input className="input" value={form.vorname} onChange={(e) => set("vorname", e.target.value)} required />
                </Field>
                <Field label="Nachname">
                  <input className="input" value={form.nachname} onChange={(e) => set("nachname", e.target.value)} required />
                </Field>
              </div>
              <Field label="E-Mail">
                <input className="input" type="email" value={form.email} onChange={(e) => set("email", e.target.value)} />
              </Field>
              <Field label="Telefon">
                <input className="input" value={form.telefon} onChange={(e) => set("telefon", e.target.value)} />
              </Field>
              <Field label="Funktion">
                <select className="select" value={form.funktion_id} onChange={(e) => set("funktion_id", e.target.value)}>
                  <option value="">Keine</option>
                  {funktionen?.items.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </select>
              </Field>
              <div className="row">
                <button className="btn btn-primary btn-block" disabled={busy} type="submit">
                  {editId ? "Speichern" : "Hinzufügen"}
                </button>
                {editId && (
                  <button type="button" className="btn btn-ghost" onClick={reset}>
                    Abbrechen
                  </button>
                )}
              </div>
            </form>
          </div>

          <div>
            {list.loading && <Spinner center />}
            {list.data && list.data.items.length === 0 && (
              <Empty icon="👥" title="Noch keine Mitarbeiter erfasst" />
            )}
            <div className="stack">
              {list.data?.items.map((emp) => {
                const isGf = emp.id === list.data!.geschaeftsfuehrer_id;
                return (
                  <div key={emp.id} className="card card-pad spread">
                    <div>
                      <strong>
                        {emp.vorname} {emp.nachname}
                      </strong>
                      {isGf && (
                        <Badge tone="yellow">
                          <span style={{ marginLeft: 4 }}>Geschäftsführer</span>
                        </Badge>
                      )}
                      <div className="muted" style={{ fontSize: "0.86rem" }}>
                        {emp.funktion_name ?? "—"}
                        {emp.email ? ` · ${emp.email}` : ""}
                      </div>
                    </div>
                    {!isGf && (
                      <div className="row" style={{ gap: 6 }}>
                        <button className="btn btn-ghost btn-sm" onClick={() => edit(emp)}>
                          Bearbeiten
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => remove(emp.id)}>
                          Entfernen
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
