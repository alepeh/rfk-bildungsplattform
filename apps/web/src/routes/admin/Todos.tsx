import { useState } from "react";
import { api, ApiError } from "../../api";
import { useResource, formatDate } from "../../lib";
import { Spinner, Alert, Empty, Field, Badge } from "../../components/ui";

type Typ = "Fehler" | "Erweiterung";
type Prioritaet = "Niedrig" | "Mittel" | "Hoch";

interface Todo {
  id: string;
  typ: Typ;
  prioritaet: Prioritaet;
  name: string;
  beschreibung: string | null;
  erledigt: boolean | number;
  created_at: string;
  updated_at: string;
}

const TYPEN: Typ[] = ["Fehler", "Erweiterung"];
const PRIOS: Prioritaet[] = ["Niedrig", "Mittel", "Hoch"];
const PRIO_ORDER: Record<Prioritaet, number> = { Hoch: 0, Mittel: 1, Niedrig: 2 };
const PRIO_TONE: Record<Prioritaet, "red" | "amber" | "green"> = {
  Hoch: "red",
  Mittel: "amber",
  Niedrig: "green",
};

export function AdminTodos() {
  const { data, loading, error: loadError, reload } = useResource<Todo[]>("/admin/todos");

  const [typ, setTyp] = useState<Typ>("Fehler");
  const [prioritaet, setPrioritaet] = useState<Prioritaet>("Mittel");
  const [name, setName] = useState("");
  const [beschreibung, setBeschreibung] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function create() {
    if (!name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await api.post(`/admin/todos`, { typ, prioritaet, name, beschreibung });
      setName("");
      setBeschreibung("");
      setTyp("Fehler");
      setPrioritaet("Mittel");
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Anlegen fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  }

  async function toggle(t: Todo) {
    setBusy(t.id);
    setError(null);
    try {
      await api.patch(`/admin/todos/${t.id}`, { erledigt: !t.erledigt });
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setBusy(null);
    }
  }

  const sorted = [...(data ?? [])].sort((a, b) => {
    const ae = a.erledigt ? 1 : 0;
    const be = b.erledigt ? 1 : 0;
    if (ae !== be) return ae - be;
    return PRIO_ORDER[a.prioritaet] - PRIO_ORDER[b.prioritaet];
  });

  return (
    <div className="stack">
      <div className="card card-pad stack">
        <h3 style={{ margin: 0 }}>Neues To-do</h3>
        <div className="grid cols-3">
          <Field label="Typ">
            <select className="select" value={typ} onChange={(e) => setTyp(e.target.value as Typ)}>
              {TYPEN.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Priorität">
            <select
              className="select"
              value={prioritaet}
              onChange={(e) => setPrioritaet(e.target.value as Prioritaet)}
            >
              {PRIOS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Name">
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
        </div>
        <Field label="Beschreibung">
          <textarea
            className="input"
            rows={2}
            value={beschreibung}
            onChange={(e) => setBeschreibung(e.target.value)}
          />
        </Field>
        {error && <Alert kind="error">{error}</Alert>}
        <div>
          <button className="btn btn-primary" disabled={saving || !name.trim()} onClick={create}>
            To-do anlegen
          </button>
        </div>
      </div>

      {loadError && <Alert kind="error">{loadError}</Alert>}

      {loading ? (
        <Spinner center />
      ) : sorted.length === 0 ? (
        <Empty icon="✅" title="Keine To-dos" />
      ) : (
        <div className="stack">
          {sorted.map((t) => {
            const done = !!t.erledigt;
            return (
              <div key={t.id} className="card card-pad">
                <div className="spread" style={{ alignItems: "flex-start" }}>
                  <label className="checkbox">
                    <input
                      type="checkbox"
                      checked={done}
                      disabled={busy === t.id}
                      onChange={() => toggle(t)}
                    />
                    <div>
                      <div
                        style={{
                          fontWeight: 600,
                          color: "var(--ink)",
                          textDecoration: done ? "line-through" : "none",
                          opacity: done ? 0.55 : 1,
                        }}
                      >
                        {t.name}
                      </div>
                      {t.beschreibung && (
                        <div
                          className="muted"
                          style={{
                            fontSize: "0.88rem",
                            textDecoration: done ? "line-through" : "none",
                          }}
                        >
                          {t.beschreibung}
                        </div>
                      )}
                      <div className="muted" style={{ fontSize: "0.78rem", marginTop: 4 }}>
                        {formatDate(t.created_at)}
                      </div>
                    </div>
                  </label>
                  <div className="row" style={{ gap: 6 }}>
                    <Badge>{t.typ}</Badge>
                    <Badge tone={PRIO_TONE[t.prioritaet]}>{t.prioritaet}</Badge>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
