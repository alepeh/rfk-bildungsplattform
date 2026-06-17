import { downloadFile } from "../api";
import { useResource, formatDate } from "../lib";
import { Spinner, Alert, Badge, Empty, PageHeader } from "../components/ui";

interface Item {
  teilnehmer_id: string;
  status: string;
  schulung_id: string;
  schulung_name: string;
  datum_von: string;
  ort_name: string | null;
  unterlagen: { id: string; name: string; filename: string }[];
}

export function MyCourses() {
  const { data, loading, error } = useResource<{ items: Item[] }>("/bestellungen/meine-schulungen");

  return (
    <div className="page">
      <div className="container">
        <PageHeader
          title="Meine Schulungen"
          subtitle="Absolvierte Schulungen und zugehörige Unterlagen zum Download."
        />
        {loading && <Spinner center />}
        {error && <Alert kind="error">{error}</Alert>}
        {data && data.items.length === 0 && (
          <Empty icon="🎓" title="Noch keine abgeschlossenen Schulungen">
            Sobald Sie an einer Schulung teilgenommen haben, erscheint sie hier mit den Unterlagen.
          </Empty>
        )}
        <div className="stack">
          {data?.items.map((it) => (
            <div key={it.teilnehmer_id} className="card card-pad">
              <div className="spread">
                <div>
                  <h3 style={{ margin: 0 }}>{it.schulung_name}</h3>
                  <p className="muted" style={{ margin: "4px 0 0", fontSize: "0.9rem" }}>
                    {formatDate(it.datum_von)}
                    {it.ort_name ? ` · ${it.ort_name}` : ""}
                  </p>
                </div>
                <div className="row" style={{ gap: 8 }}>
                  <Badge tone="green">Teilgenommen</Badge>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() =>
                      downloadFile(
                        `/bestellungen/teilnahmebestaetigung/${it.teilnehmer_id}`,
                        `Teilnahmebestaetigung-${it.schulung_name}.pdf`,
                      )
                    }
                  >
                    📜 Teilnahmebestätigung
                  </button>
                </div>
              </div>
              {it.unterlagen.length > 0 && (
                <>
                  <hr className="divider" />
                  <div className="stack" style={{ gap: 8 }}>
                    {it.unterlagen.map((u) => (
                      <div key={u.id} className="spread">
                        <span className="muted">📄 {u.name}</span>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={() => downloadFile(`/documents/unterlagen/${u.id}/download`, u.filename)}
                        >
                          Herunterladen
                        </button>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
