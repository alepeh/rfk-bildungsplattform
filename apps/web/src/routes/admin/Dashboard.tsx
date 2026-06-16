import { useState } from "react";
import { Link } from "react-router";
import { api, ApiError } from "../../api";
import { useResource } from "../../lib";
import { Spinner, Alert, Badge } from "../../components/ui";

interface PersonRow {
  id: string;
  vorname: string;
  nachname: string;
  email: string | null;
  betrieb_name: string | null;
  funktion_name: string | null;
  activation_requested_at: string | null;
}

interface SchulungRow {
  id: string;
}

interface TerminRow {
  id: string;
  datum_von: string;
}

export function AdminDashboard() {
  const pending = useResource<PersonRow[]>("/admin/personen?activated=0");
  const schulungen = useResource<SchulungRow[]>("/admin/schulungen");
  const termine = useResource<TerminRow[]>("/admin/schulungstermine");

  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function freischalten(id: string) {
    setBusy(id);
    setError(null);
    try {
      await api.post(`/admin/personen/${id}/activate`);
      pending.reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Freischaltung fehlgeschlagen");
    } finally {
      setBusy(null);
    }
  }

  const loading = pending.loading || schulungen.loading || termine.loading;
  if (loading) return <Spinner center />;

  const pendingCount = pending.data?.length ?? 0;
  const schulungenCount = schulungen.data?.length ?? 0;
  const now = Date.now();
  const upcoming = (termine.data ?? []).filter((t) => new Date(t.datum_von).getTime() >= now).length;

  return (
    <div className="stack">
      {error && <Alert kind="error">{error}</Alert>}
      {pending.error && <Alert kind="error">{pending.error}</Alert>}

      <div className="grid cols-3">
        <StatCard label="Offene Freischaltungen" value={pendingCount} tone="amber" />
        <StatCard label="Schulungen" value={schulungenCount} />
        <StatCard label="Kommende Termine" value={upcoming} />
      </div>

      <div className="card card-pad">
        <h2 style={{ marginBottom: 16 }}>Wartende Registrierungen</h2>
        {pendingCount === 0 ? (
          <p className="muted" style={{ margin: 0 }}>
            Keine offenen Freischaltungen.
          </p>
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>E-Mail</th>
                  <th>Betrieb</th>
                  <th>Funktion</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {pending.data!.map((p) => (
                  <tr key={p.id}>
                    <td>
                      {p.vorname} {p.nachname}
                    </td>
                    <td>{p.email ?? "—"}</td>
                    <td>{p.betrieb_name ?? "—"}</td>
                    <td>{p.funktion_name ?? "—"}</td>
                    <td>
                      <button
                        className="btn btn-primary btn-sm"
                        disabled={busy === p.id}
                        onClick={() => freischalten(p.id)}
                      >
                        Freischalten
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div style={{ marginTop: 16 }}>
          <Link to="/admin/personen" className="btn btn-ghost btn-sm">
            Alle Personen verwalten
          </Link>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, tone }: { label: string; value: number; tone?: "amber" }) {
  return (
    <div className="card card-pad">
      <div className="muted" style={{ fontSize: "0.85rem", fontWeight: 600 }}>
        {label}
      </div>
      <div className="row" style={{ marginTop: 8, gap: 10 }}>
        <span style={{ fontSize: "2.2rem", fontWeight: 800, color: "var(--ink)", lineHeight: 1 }}>
          {value}
        </span>
        {tone === "amber" && value > 0 && <Badge tone="amber">offen</Badge>}
      </div>
    </div>
  );
}
