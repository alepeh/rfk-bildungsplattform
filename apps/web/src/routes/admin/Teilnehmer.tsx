import { useState } from "react";
import { useParams, Link } from "react-router";
import { api, ApiError, downloadFile } from "../../api";
import { useResource } from "../../lib";
import { Spinner, Alert, Empty, Badge } from "../../components/ui";

interface Teilnehmer {
  id: string;
  status: "Angemeldet" | "Teilgenommen" | "Entschuldigt" | "Unentschuldigt";
  verpflegung: "Standard" | "Vegetarisch";
  vorname: string;
  nachname: string;
  email: string | null;
  telefon: string | null;
  betrieb_name: string | null;
  dsv_akzeptiert: boolean | number;
}

const STATUS: Teilnehmer["status"][] = [
  "Angemeldet",
  "Teilgenommen",
  "Entschuldigt",
  "Unentschuldigt",
];
const VERPFLEGUNG: Teilnehmer["verpflegung"][] = ["Standard", "Vegetarisch"];

export function AdminTeilnehmer() {
  const { id } = useParams<{ id: string }>();
  const path = id ? `/admin/schulungstermine/${id}/teilnehmer` : null;
  const { data, loading, error: loadError, reload } = useResource<Teilnehmer[]>(path);

  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reminder, setReminder] = useState<string | null>(null);

  async function patch(tid: string, body: Partial<Pick<Teilnehmer, "status" | "verpflegung">>) {
    setBusy(tid);
    setError(null);
    try {
      await api.patch(`/admin/teilnehmer/${tid}`, body);
      reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Speichern fehlgeschlagen");
    } finally {
      setBusy(null);
    }
  }

  async function exportCsv() {
    if (!id) return;
    setError(null);
    try {
      await downloadFile(`/admin/schulungstermine/${id}/export.csv`, `teilnehmer-${id}.csv`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Export fehlgeschlagen");
    }
  }

  async function sendReminder() {
    if (!id) return;
    setBusy("reminder");
    setError(null);
    setReminder(null);
    try {
      const res = await api.post<{ ok: boolean; sent: number }>(
        `/admin/schulungstermine/${id}/reminder`
      );
      setReminder(`Erinnerung an ${res.sent} Teilnehmer versendet.`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Versand fehlgeschlagen");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="stack">
      <div className="spread">
        <div>
          <Link to="/admin/termine" className="muted" style={{ fontSize: "0.9rem" }}>
            ← Zurück zu Terminen
          </Link>
          <h2 style={{ margin: "6px 0 0" }}>Teilnehmer</h2>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <button className="btn btn-ghost btn-sm" onClick={exportCsv}>
            CSV Export
          </button>
          <button
            className="btn btn-dark btn-sm"
            disabled={busy === "reminder"}
            onClick={sendReminder}
          >
            Erinnerung senden
          </button>
        </div>
      </div>

      {reminder && <Alert kind="success">{reminder}</Alert>}
      {error && <Alert kind="error">{error}</Alert>}
      {loadError && <Alert kind="error">{loadError}</Alert>}

      {loading ? (
        <Spinner center />
      ) : !data || data.length === 0 ? (
        <Empty icon="👥" title="Keine Teilnehmer angemeldet" />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Name</th>
                <th>E-Mail</th>
                <th>Betrieb</th>
                <th>Status</th>
                <th>Verpflegung</th>
                <th>DSV</th>
              </tr>
            </thead>
            <tbody>
              {data.map((t) => (
                <tr key={t.id}>
                  <td>
                    {t.vorname} {t.nachname}
                  </td>
                  <td>{t.email ?? "—"}</td>
                  <td>{t.betrieb_name ?? "—"}</td>
                  <td>
                    <select
                      className="select"
                      style={{ minWidth: 150 }}
                      value={t.status}
                      disabled={busy === t.id}
                      onChange={(e) =>
                        patch(t.id, { status: e.target.value as Teilnehmer["status"] })
                      }
                    >
                      {STATUS.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <select
                      className="select"
                      style={{ minWidth: 140 }}
                      value={t.verpflegung}
                      disabled={busy === t.id}
                      onChange={(e) =>
                        patch(t.id, { verpflegung: e.target.value as Teilnehmer["verpflegung"] })
                      }
                    >
                      {VERPFLEGUNG.map((v) => (
                        <option key={v} value={v}>
                          {v}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    {t.dsv_akzeptiert ? (
                      <Badge tone="green">Akzeptiert</Badge>
                    ) : (
                      <Badge tone="amber">Offen</Badge>
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
