import { useState } from "react";
import { api, ApiError } from "../../api";
import { useResource } from "../../lib";
import { Spinner, Alert, Badge, Empty } from "../../components/ui";

interface PersonRow {
  id: string;
  vorname: string;
  nachname: string;
  email: string | null;
  telefon: string | null;
  is_activated: boolean;
  can_book_schulungen: boolean;
  funktion_id: string | null;
  organisation_id: string | null;
  betrieb_id: string | null;
  funktion_name: string | null;
  betrieb_name: string | null;
}

interface RefItem {
  id: string;
  name: string;
}
interface RefList {
  items: RefItem[];
}

type Filter = "alle" | "wartend" | "aktiv";

export function AdminPersonen() {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<Filter>("alle");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const activated = filter === "wartend" ? "0" : filter === "aktiv" ? "1" : "";
  const params = new URLSearchParams();
  if (activated) params.set("activated", activated);
  if (q.trim()) params.set("q", q.trim());
  const path = `/admin/personen${params.toString() ? `?${params}` : ""}`;

  const { data, loading, error: loadError, reload } = useResource<PersonRow[]>(path, [path]);

  const funktionen = useResource<RefList>("/ref/funktionen");
  const organisationen = useResource<RefList>("/ref/organisationen");
  const betriebe = useResource<RefItem[]>("/admin/betriebe");

  async function activate(id: string, on: boolean) {
    setBusy(id);
    setError(null);
    try {
      await api.post(`/admin/personen/${id}/${on ? "activate" : "deactivate"}`);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Aktion fehlgeschlagen");
    } finally {
      setBusy(null);
    }
  }

  async function patch(id: string, body: Record<string, unknown>) {
    setBusy(id);
    setError(null);
    try {
      await api.patch(`/admin/personen/${id}`, body);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="stack">
      <div className="card card-pad">
        <div className="row row-wrap" style={{ gap: 12 }}>
          <input
            className="input"
            style={{ maxWidth: 320 }}
            placeholder="Suche nach Name oder E-Mail…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select
            className="select"
            style={{ maxWidth: 200 }}
            value={filter}
            onChange={(e) => setFilter(e.target.value as Filter)}
          >
            <option value="alle">Alle</option>
            <option value="wartend">Wartend</option>
            <option value="aktiv">Aktiv</option>
          </select>
        </div>
      </div>

      {error && <Alert kind="error">{error}</Alert>}
      {loadError && <Alert kind="error">{loadError}</Alert>}

      {loading ? (
        <Spinner center />
      ) : !data || data.length === 0 ? (
        <Empty icon="👤" title="Keine Personen gefunden" />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Name</th>
                <th>E-Mail</th>
                <th>Betrieb</th>
                <th>Funktion</th>
                <th>Organisation</th>
                <th>Status</th>
                <th>Buchen</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.map((p) => (
                <tr key={p.id}>
                  <td>
                    {p.vorname} {p.nachname}
                  </td>
                  <td>{p.email ?? "—"}</td>
                  <td>
                    <select
                      className="select"
                      style={{ minWidth: 150 }}
                      value={p.betrieb_id ?? ""}
                      disabled={busy === p.id}
                      onChange={(e) => patch(p.id, { betrieb_id: e.target.value || null })}
                    >
                      <option value="">—</option>
                      {(betriebe.data ?? []).map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      className="select"
                      style={{ minWidth: 140 }}
                      value={p.funktion_id ?? ""}
                      disabled={busy === p.id}
                      onChange={(e) => patch(p.id, { funktion_id: e.target.value || null })}
                    >
                      <option value="">—</option>
                      {(funktionen.data?.items ?? []).map((f) => (
                        <option key={f.id} value={f.id}>
                          {f.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      className="select"
                      style={{ minWidth: 140 }}
                      value={p.organisation_id ?? ""}
                      disabled={busy === p.id}
                      onChange={(e) => patch(p.id, { organisation_id: e.target.value || null })}
                    >
                      <option value="">—</option>
                      {(organisationen.data?.items ?? []).map((o) => (
                        <option key={o.id} value={o.id}>
                          {o.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    {p.is_activated ? (
                      <Badge tone="green">Aktiv</Badge>
                    ) : (
                      <Badge tone="amber">Wartend</Badge>
                    )}
                  </td>
                  <td>
                    <label className="checkbox" style={{ justifyContent: "center" }}>
                      <input
                        type="checkbox"
                        checked={p.can_book_schulungen}
                        disabled={busy === p.id}
                        onChange={(e) => patch(p.id, { can_book_schulungen: e.target.checked })}
                      />
                    </label>
                  </td>
                  <td>
                    {p.is_activated ? (
                      <button
                        className="btn btn-danger btn-sm"
                        disabled={busy === p.id}
                        onClick={() => activate(p.id, false)}
                      >
                        Deaktivieren
                      </button>
                    ) : (
                      <button
                        className="btn btn-primary btn-sm"
                        disabled={busy === p.id}
                        onClick={() => activate(p.id, true)}
                      >
                        Freischalten
                      </button>
                    )}
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
