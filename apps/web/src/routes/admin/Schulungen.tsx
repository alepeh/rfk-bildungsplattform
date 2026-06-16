import { useState } from "react";
import { api, ApiError } from "../../api";
import { useResource, eur } from "../../lib";
import { Spinner, Alert, Empty, Field } from "../../components/ui";

interface Schulung {
  id: string;
  name: string;
  beschreibung: string | null;
  art_id: string | null;
  preis_standard: number | null;
  preis_rabattiert: number | null;
}

interface RefItem {
  id: string;
  name: string;
}
interface RefList {
  items: RefItem[];
}

interface EligList {
  funktion_ids: string[];
}

interface FormState {
  id: string | null;
  name: string;
  beschreibung: string;
  art_id: string;
  preis_standard: string;
  preis_rabattiert: string;
}

const emptyForm: FormState = {
  id: null,
  name: "",
  beschreibung: "",
  art_id: "",
  preis_standard: "",
  preis_rabattiert: "",
};

function eurToCents(v: string): number {
  const n = Number(v.replace(",", "."));
  return Number.isFinite(n) ? Math.round(n * 100) : 0;
}
function centsToEur(c: number | null): string {
  return c == null ? "" : (c / 100).toFixed(2);
}

export function AdminSchulungen() {
  const { data, loading, error: loadError, reload } = useResource<Schulung[]>("/admin/schulungen");
  const arten = useResource<RefList>("/ref/schulungsarten");
  const funktionen = useResource<RefList>("/ref/funktionen");

  const [form, setForm] = useState<FormState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function openNew() {
    setForm({ ...emptyForm });
    setError(null);
  }
  function openEdit(s: Schulung) {
    setForm({
      id: s.id,
      name: s.name,
      beschreibung: s.beschreibung ?? "",
      art_id: s.art_id ?? "",
      preis_standard: centsToEur(s.preis_standard),
      preis_rabattiert: centsToEur(s.preis_rabattiert),
    });
    setError(null);
  }

  async function save() {
    if (!form) return;
    setSaving(true);
    setError(null);
    const body = {
      name: form.name,
      beschreibung: form.beschreibung || null,
      art_id: form.art_id || null,
      preis_standard: eurToCents(form.preis_standard),
      preis_rabattiert: form.preis_rabattiert ? eurToCents(form.preis_rabattiert) : null,
    };
    try {
      if (form.id) await api.put(`/admin/schulungen/${form.id}`, body);
      else await api.post(`/admin/schulungen`, body);
      setForm(null);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: string) {
    if (!confirm("Diese Schulung wirklich löschen?")) return;
    setError(null);
    try {
      await api.del(`/admin/schulungen/${id}`);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Löschen fehlgeschlagen");
    }
  }

  return (
    <div className="stack">
      <div className="spread">
        <h2 style={{ margin: 0 }}>Schulungen</h2>
        <button className="btn btn-primary btn-sm" onClick={openNew}>
          Neue Schulung
        </button>
      </div>

      {error && <Alert kind="error">{error}</Alert>}
      {loadError && <Alert kind="error">{loadError}</Alert>}

      {form && (
        <div className="card card-pad stack">
          <h3 style={{ margin: 0 }}>{form.id ? "Schulung bearbeiten" : "Neue Schulung"}</h3>
          <Field label="Name">
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </Field>
          <Field label="Beschreibung">
            <textarea
              className="input"
              rows={3}
              value={form.beschreibung}
              onChange={(e) => setForm({ ...form, beschreibung: e.target.value })}
            />
          </Field>
          <div className="grid cols-3">
            <Field label="Art">
              <select
                className="select"
                value={form.art_id}
                onChange={(e) => setForm({ ...form, art_id: e.target.value })}
              >
                <option value="">—</option>
                {(arten.data?.items ?? []).map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Preis Standard (€)">
              <input
                className="input"
                inputMode="decimal"
                value={form.preis_standard}
                onChange={(e) => setForm({ ...form, preis_standard: e.target.value })}
              />
            </Field>
            <Field label="Preis Rabattiert (€)">
              <input
                className="input"
                inputMode="decimal"
                value={form.preis_rabattiert}
                onChange={(e) => setForm({ ...form, preis_rabattiert: e.target.value })}
              />
            </Field>
          </div>
          <div className="row">
            <button className="btn btn-primary" disabled={saving || !form.name} onClick={save}>
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
        <Empty icon="📚" title="Noch keine Schulungen" />
      ) : (
        <div className="grid cols-2">
          {data.map((s) => (
            <SchulungCard
              key={s.id}
              s={s}
              arten={arten.data?.items ?? []}
              funktionen={funktionen.data?.items ?? []}
              onEdit={() => openEdit(s)}
              onDelete={() => remove(s.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SchulungCard({
  s,
  arten,
  funktionen,
  onEdit,
  onDelete,
}: {
  s: Schulung;
  arten: RefItem[];
  funktionen: RefItem[];
  onEdit: () => void;
  onDelete: () => void;
}) {
  const elig = useResource<EligList>(`/admin/schulungen/${s.id}/funktionen`);
  const [selected, setSelected] = useState<string[] | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [matName, setMatName] = useState("");
  const [matDesc, setMatDesc] = useState("");
  const [busy, setBusy] = useState(false);

  const current = selected ?? elig.data?.funktion_ids ?? [];
  const artName = arten.find((a) => a.id === s.art_id)?.name;

  function toggle(id: string) {
    const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
    setSelected(next);
  }

  async function saveElig() {
    setBusy(true);
    setMsg(null);
    try {
      await api.put(`/admin/schulungen/${s.id}/funktionen`, { funktion_ids: current });
      setMsg("Berechtigungen gespeichert.");
      elig.reload();
      setSelected(null);
    } catch (e) {
      setMsg(e instanceof ApiError ? e.message : "Fehler");
    } finally {
      setBusy(false);
    }
  }

  async function uploadMaterial() {
    if (!file) return;
    setBusy(true);
    setMsg(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("name", matName || file.name);
      if (matDesc) fd.append("description", matDesc);
      await api.upload(`/admin/schulungen/${s.id}/unterlagen`, fd);
      setMsg("Unterlage hochgeladen.");
      setFile(null);
      setMatName("");
      setMatDesc("");
      setUploadOpen(false);
    } catch (e) {
      setMsg(e instanceof ApiError ? e.message : "Upload fehlgeschlagen");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card card-pad stack">
      <div className="spread">
        <h3 style={{ margin: 0 }}>{s.name}</h3>
        {artName && <span className="badge">{artName}</span>}
      </div>
      {s.beschreibung && (
        <p className="muted" style={{ margin: 0 }}>
          {s.beschreibung}
        </p>
      )}
      <div className="row" style={{ gap: 16 }}>
        <span className="price">{eur(s.preis_standard)}</span>
        {s.preis_rabattiert != null && (
          <span className="muted">rabattiert {eur(s.preis_rabattiert)}</span>
        )}
      </div>

      <div>
        <div style={{ fontWeight: 600, fontSize: "0.88rem", marginBottom: 8 }}>
          Berechtigte Funktionen
        </div>
        {elig.loading ? (
          <Spinner />
        ) : (
          <div className="stack" style={{ gap: 6 }}>
            {funktionen.map((f) => (
              <label key={f.id} className="checkbox">
                <input
                  type="checkbox"
                  checked={current.includes(f.id)}
                  onChange={() => toggle(f.id)}
                />
                <span>{f.name}</span>
              </label>
            ))}
          </div>
        )}
        {selected !== null && (
          <button
            className="btn btn-dark btn-sm"
            style={{ marginTop: 10 }}
            disabled={busy}
            onClick={saveElig}
          >
            Berechtigungen speichern
          </button>
        )}
      </div>

      {uploadOpen && (
        <div className="card card-pad stack" style={{ background: "var(--bg)" }}>
          <Field label="Datei">
            <input
              className="input"
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </Field>
          <Field label="Name">
            <input
              className="input"
              value={matName}
              onChange={(e) => setMatName(e.target.value)}
            />
          </Field>
          <Field label="Beschreibung">
            <input
              className="input"
              value={matDesc}
              onChange={(e) => setMatDesc(e.target.value)}
            />
          </Field>
          <div className="row">
            <button className="btn btn-primary btn-sm" disabled={busy || !file} onClick={uploadMaterial}>
              Hochladen
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => setUploadOpen(false)}>
              Abbrechen
            </button>
          </div>
        </div>
      )}

      {msg && <Alert kind="info">{msg}</Alert>}

      <div className="row" style={{ marginTop: "auto" }}>
        <button className="btn btn-ghost btn-sm" onClick={onEdit}>
          Bearbeiten
        </button>
        <button className="btn btn-ghost btn-sm" onClick={() => setUploadOpen((o) => !o)}>
          Unterlage hochladen
        </button>
        <button className="btn btn-danger btn-sm" onClick={onDelete}>
          Löschen
        </button>
      </div>
    </div>
  );
}
