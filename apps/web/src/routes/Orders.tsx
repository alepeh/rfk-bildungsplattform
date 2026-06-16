import { useResource, eur, formatDate } from "../lib";
import { Spinner, Alert, Badge, Empty, PageHeader } from "../components/ui";

interface Order {
  id: string;
  anzahl: number;
  einzelpreis: number;
  gesamtpreis: number;
  status: string;
  created_at: string;
  schulung_name: string;
  datum_von: string;
}

export function Orders() {
  const { data, loading, error } = useResource<{ items: Order[] }>("/bestellungen");

  return (
    <div className="page">
      <div className="container">
        <PageHeader title="Meine Bestellungen" subtitle="Übersicht Ihrer gebuchten Schulungen." />
        {loading && <Spinner center />}
        {error && <Alert kind="error">{error}</Alert>}
        {data && data.items.length === 0 && (
          <Empty icon="🧾" title="Noch keine Bestellungen">
            Hier erscheinen Ihre Schulungsbuchungen.
          </Empty>
        )}
        {data && data.items.length > 0 && (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Schulung</th>
                  <th>Termin</th>
                  <th>Plätze</th>
                  <th>Gesamt</th>
                  <th>Status</th>
                  <th>Bestellt am</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((o) => (
                  <tr key={o.id}>
                    <td>{o.schulung_name}</td>
                    <td>{formatDate(o.datum_von)}</td>
                    <td>{o.anzahl}</td>
                    <td>{eur(o.gesamtpreis)}</td>
                    <td>
                      <Badge tone={o.status === "Storniert" ? "red" : "green"}>{o.status}</Badge>
                    </td>
                    <td>{formatDate(o.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
