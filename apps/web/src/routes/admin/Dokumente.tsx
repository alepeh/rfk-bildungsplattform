import { useState } from "react";
import { api, ApiError } from "../../api";
import { useResource, formatDate } from "../../lib";
import { Spinner, Alert, Empty, Field, Badge } from "../../components/ui";

interface DocumentRow {
  id: string;
  name: string;
  description: string | null;
  filename: string;
  size: number;
  created_at: string;
  funktion_ids: string | null;
}

interface RefItem {
  id: string;
  name: string;
}
interface RefList {
  items: RefItem[];
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AdminDokumente() {
  const { data, loading, error: loadError, reload } = useResource<DocumentRow[]>("/admin/documents");
  const funktionen = useResource<RefList>("/ref/funktionen");

  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [funktionIds, setFunktionIds] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const funktionList = funktionen.data?.items ?? [];
  function funktionNames(ids: string | null): string[] {
    if (!ids) return [];
    const set = ids.split(",").map((s) => s.trim());
    return funktionList.filter((f) => set.includes(f.id)).map((f) => f.name);
  }

  function toggle(id: string) {
    setFunktionIds((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]));
  }

  async function upload() {
    if (!file) return;
    setSaving(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("name", name || file.name);
      if (description) fd.append("description", description);
      funktionIds.forEach((id) => fd.append("funktion_ids", id));
      await api.upload(`/admin/documents`, fd);
      setFile(null);
      setName("");
      setDescription("");
      setFunktionIds([]);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Upload fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: string) {
    if (!confirm("Dieses Dokument wirklich löschen?")) return;
    setError(null);
    try {
      await api.del(`/admin/documents/${id}`);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Löschen fehlgeschlagen");
    }
  }

  return (
    <div className="stack">
      <div className="card card-pad stack">
        <h3 style={{ margin: 0 }}>Dokument hochladen</h3>
        <div className="grid cols-2">
          <Field label="Datei">
            <input
              className="input"
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </Field>
          <Field label="Name">
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
          </Field>
        </div>
        <Field label="Beschreibung">
          <input
            className="input"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </Field>
        <Field label="Sichtbar für Funktionen" hint="Keine Auswahl = für alle sichtbar">
          <div className="row row-wrap" style={{ gap: 14 }}>
            {funktionList.map((f) => (
              <label key={f.id} className="checkbox">
                <input
                  type="checkbox"
                  checked={funktionIds.includes(f.id)}
                  onChange={() => toggle(f.id)}
                />
                <span>{f.name}</span>
              </label>
            ))}
          </div>
        </Field>
        {error && <Alert kind="error">{error}</Alert>}
        <div>
          <button className="btn btn-primary" disabled={saving || !file} onClick={upload}>
            Hochladen
          </button>
        </div>
      </div>

      {loadError && <Alert kind="error">{loadError}</Alert>}

      {loading ? (
        <Spinner center />
      ) : !data || data.length === 0 ? (
        <Empty icon="📄" title="Noch keine Dokumente" />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Name</th>
                <th>Datei</th>
                <th>Größe</th>
                <th>Funktionen</th>
                <th>Hochgeladen</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.map((d) => {
                const names = funktionNames(d.funktion_ids);
                return (
                  <tr key={d.id}>
                    <td>
                      {d.name}
                      {d.description && (
                        <div className="muted" style={{ fontSize: "0.82rem", whiteSpace: "normal" }}>
                          {d.description}
                        </div>
                      )}
                    </td>
                    <td className="muted">{d.filename}</td>
                    <td>{formatSize(d.size)}</td>
                    <td>
                      {names.length === 0 ? (
                        <span className="muted">Alle</span>
                      ) : (
                        <div className="tag-list">
                          {names.map((n) => (
                            <Badge key={n}>{n}</Badge>
                          ))}
                        </div>
                      )}
                    </td>
                    <td>{formatDate(d.created_at)}</td>
                    <td>
                      <button className="btn btn-danger btn-sm" onClick={() => remove(d.id)}>
                        Löschen
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
