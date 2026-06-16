import { downloadFile } from "../api";
import { useResource } from "../lib";
import { Spinner, Alert, Empty, PageHeader } from "../components/ui";

interface Doc {
  id: string;
  name: string;
  description: string | null;
  filename: string;
  size: number | null;
}

function kb(size: number | null): string {
  if (!size) return "";
  return size > 1024 * 1024 ? `${(size / 1024 / 1024).toFixed(1)} MB` : `${Math.round(size / 1024)} KB`;
}

export function Documents() {
  const { data, loading, error } = useResource<{ items: Doc[] }>("/documents");

  return (
    <div className="page">
      <div className="container">
        <PageHeader
          title="Dokumente"
          subtitle="Allgemeine Unterlagen und Formulare — gefiltert nach Ihrer Funktion."
        />
        {loading && <Spinner center />}
        {error && <Alert kind="error">{error}</Alert>}
        {data && data.items.length === 0 && (
          <Empty icon="📁" title="Keine Dokumente verfügbar" />
        )}
        <div className="grid cols-2">
          {data?.items.map((d) => (
            <div key={d.id} className="card card-pad spread">
              <div>
                <h3 style={{ margin: 0 }}>📄 {d.name}</h3>
                {d.description && (
                  <p className="muted" style={{ margin: "4px 0 0", fontSize: "0.9rem" }}>
                    {d.description}
                  </p>
                )}
                {d.size != null && (
                  <span className="muted" style={{ fontSize: "0.8rem" }}>
                    {kb(d.size)}
                  </span>
                )}
              </div>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => downloadFile(`/documents/${d.id}/download`, d.filename)}
              >
                Download
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
