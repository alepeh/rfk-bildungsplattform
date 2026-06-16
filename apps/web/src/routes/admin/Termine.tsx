import { useState } from "react";
import { Link } from "react-router";
import { api, ApiError } from "../../api";
import { useResource, formatDateTime } from "../../lib";
import { Spinner, Alert, Empty, Field, Badge } from "../../components/ui";

interface Termin {
  id: string;
  schulung_id: string | null;
  ort_id: string | null;
  datum_von: string;
  datum_bis: string;
  dauer: string | null;
  max_teilnehmer: number | null;
  min_teilnehmer: number | null;
  buchbar: boolean | number;
}

interface RefItem {
  id: string;
  name: string;
}
interface RefList {
  items: RefItem[];
}

interface FormState {
  id: string | null;
  schulung_id: string;
  ort_id: string;
  datum_von: string;
  datum_bis: string;
  dauer: string;
  max_teilnehmer: string;
  min_teilnehmer: string;
  buchbar: boolean;
}

const emptyForm: FormState = {
  id: null,
  schulung_id: "",
  ort_id: "",
  datum_von: "",
  datum_bis: "",
  dauer: "",
  max_teilnehmer: "",
  min_teilnehmer: "",
  buchbar: true,
};

// ISO <-> datetime-local helpers (treat value as local wall-clock).
function isoToLocalInput(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(
    d.getMinutes()
  )}`;
}
function localInputToIso(v: string): string {
  return v ? new Date(v).toISOString() : "";
}

export function AdminTermine() {
  const { data, loading, error: loadError, reload } = useResource<Termin[]>("/admin/schulungstermine");
  const schulungen = useResource<RefList | RefItem[]>("/admin/schulungen");
  const orte = useResource<RefList>("/ref/schulungsorte");

  const [form, setForm] = useState<FormState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const schulungItems: RefItem[] = Array.isArray(schulungen.data)
    ? schulungen.data
    : schulungen.data?.items ?? [];
  const ortItems = orte.data?.items ?? [];

  function nameOfSchulung(id: string | null) {
    return schulungItems.find((s) => s.id === id)?.name ?? "—";
  }
  function nameOfOrt(id: string | null) {
    return ortItems.find((o) => o.id === id)?.name ?? "—";
  }

  function openNew() {
    setForm({ ...emptyForm });
    setError(null);
  }
  function openEdit(t: Termin) {
    setForm({
      id: t.id,
      schulung_id: t.schulung_id ?? "",
      ort_id: t.ort_id ?? "",
      datum_von: isoToLocalInput(t.datum_von),
      datum_bis: isoToLocalInput(t.datum_bis),
      dauer: t.dauer ?? "",
      max_teilnehmer: t.max_teilnehmer != null ? String(t.max_teilnehmer) : "",
      min_teilnehmer: t.min_teilnehmer != null ? String(t.min_teilnehmer) : "",
      buchbar: !!t.buchbar,
    });
    setError(null);
  }

  async function save() {
    if (!form) return;
    setSaving(true);
    setError(null);
    const body = {
      schulung_id: form.schulung_id || null,
      ort_id: form.ort_id || null,
      datum_von: localInputToIso(form.datum_von),
      datum_bis: localInputToIso(form.datum_bis),
      dauer: form.dauer || null,
      max_teilnehmer: form.max_teilnehmer ? Number(form.max_teilnehmer) : null,
      min_teilnehmer: form.min_teilnehmer ? Number(form.min_teilnehmer) : null,
      buchbar: form.buchbar ? 1 : 0,
    };
    try {
      if (form.id) await api.put(`/admin/schulungstermine/${form.id}`, body);
      else await api.post(`/admin/schulungstermine`, body);
      setForm(null);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: string) {
    if (!confirm("Diesen Termin wirklich löschen?")) return;
    setError(null);
    try {
      await api.del(`/admin/schulungstermine/${id}`);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Löschen fehlgeschlagen");
    }
  }

  return (
    <div className="stack">
      <div className="spread">
        <h2 style={{ margin: 0 }}>Termine</h2>
        <button className="btn btn-primary btn-sm" onClick={openNew}>
          Neuer Termin
        </button>
      </div>

      {error && <Alert kind="error">{error}</Alert>}
      {loadError && <Alert kind="error">{loadError}</Alert>}

      {form && (
        <div className="card card-pad stack">
          <h3 style={{ margin: 0 }}>{form.id ? "Termin bearbeiten" : "Neuer Termin"}</h3>
          <div className="grid cols-2">
            <Field label="Schulung">
              <select
                className="select"
                value={form.schulung_id}
                onChange={(e) => setForm({ ...form, schulung_id: e.target.value })}
              >
                <option value="">—</option>
                {schulungItems.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Ort">
              <select
                className="select"
                value={form.ort_id}
                onChange={(e) => setForm({ ...form, ort_id: e.target.value })}
              >
                <option value="">—</option>
                {ortItems.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Datum von">
              <input
                className="input"
                type="datetime-local"
                value={form.datum_von}
                onChange={(e) => setForm({ ...form, datum_von: e.target.value })}
              />
            </Field>
            <Field label="Datum bis">
              <input
                className="input"
                type="datetime-local"
                value={form.datum_bis}
                onChange={(e) => setForm({ ...form, datum_bis: e.target.value })}
              />
            </Field>
            <Field label="Dauer">
              <input
                className="input"
                value={form.dauer}
                onChange={(e) => setForm({ ...form, dauer: e.target.value })}
              />
            </Field>
            <div />
            <Field label="Max. Teilnehmer">
              <input
                className="input"
                type="number"
                value={form.max_teilnehmer}
                onChange={(e) => setForm({ ...form, max_teilnehmer: e.target.value })}
              />
            </Field>
            <Field label="Min. Teilnehmer">
              <input
                className="input"
                type="number"
                value={form.min_teilnehmer}
                onChange={(e) => setForm({ ...form, min_teilnehmer: e.target.value })}
              />
            </Field>
          </div>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={form.buchbar}
              onChange={(e) => setForm({ ...form, buchbar: e.target.checked })}
            />
            <span>Buchbar</span>
          </label>
          <div className="row">
            <button
              className="btn btn-primary"
              disabled={saving || !form.schulung_id || !form.datum_von}
              onClick={save}
            >
              Speichern
            </button>
            <button className="btn btn-ghost" onClick={() => setForm(null)}>
              Abbrechen
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <Spinner center />
      ) : !data || data.length === 0 ? (
        <Empty icon="📅" title="Noch keine Termine" />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Schulung</th>
                <th>Ort</th>
                <th>Von</th>
                <th>Bis</th>
                <th>Plätze</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.map((t) => (
                <tr key={t.id}>
                  <td>{nameOfSchulung(t.schulung_id)}</td>
                  <td>{nameOfOrt(t.ort_id)}</td>
                  <td>{formatDateTime(t.datum_von)}</td>
                  <td>{formatDateTime(t.datum_bis)}</td>
                  <td>{t.max_teilnehmer ?? "—"}</td>
                  <td>
                    {t.buchbar ? (
                      <Badge tone="green">Buchbar</Badge>
                    ) : (
                      <Badge tone="amber">Gesperrt</Badge>
                    )}
                  </td>
                  <td>
                    <div className="row" style={{ gap: 6 }}>
                      <Link to={`/admin/termine/${t.id}/teilnehmer`} className="btn btn-ghost btn-sm">
                        Teilnehmer
                      </Link>
                      <button className="btn btn-ghost btn-sm" onClick={() => openEdit(t)}>
                        Bearbeiten
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={() => remove(t.id)}>
                        Löschen
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
