import { Link } from "react-router";
import { useResource, eur, formatDate, formatTime } from "../lib";
import { Spinner, Badge, Alert, Empty } from "../components/ui";
import type { Termin } from "../api";

export function Home() {
  const { data, loading, error } = useResource<{ items: Termin[] }>("/termine");

  return (
    <>
      <section className="hero">
        <div className="container">
          <span className="eyebrow">Für Umwelt und Leben</span>
          <h1>Schulungen für das burgenländische Rauchfangkehrer­handwerk</h1>
          <p className="lead">
            Pflichtschulungen, Technik-Workshops und Weiterbildungen — übersichtlich buchbar,
            mit Live-Verfügbarkeit und automatischer Anmeldebestätigung.
          </p>
          <div className="row" style={{ marginTop: 8 }}>
            <a href="#kurse" className="btn btn-primary">
              Termine ansehen
            </a>
            <Link to="/registrieren" className="btn btn-ghost">
              Konto erstellen
            </Link>
          </div>
        </div>
      </section>

      <section className="page" id="kurse" style={{ paddingTop: 8 }}>
        <div className="container">
          <div className="spread" style={{ marginBottom: 24 }}>
            <h2 style={{ margin: 0 }}>Kommende Termine</h2>
            {data && <span className="muted">{data.items.length} Termine verfügbar</span>}
          </div>

          {loading && <Spinner center />}
          {error && <Alert kind="error">{error}</Alert>}
          {data && data.items.length === 0 && (
            <Empty icon="📅" title="Derzeit keine Termine">
              Aktuell sind keine buchbaren Schulungen ausgeschrieben. Schauen Sie bald wieder vorbei.
            </Empty>
          )}

          <div className="grid cols-3">
            {data?.items.map((t) => (
              <CourseCard key={t.id} t={t} />
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function CourseCard({ t }: { t: Termin }) {
  const frei = t.freie_plaetze;
  const seatTone = frei <= 0 ? "red" : frei <= 5 ? "amber" : "green";
  const seatLabel = frei <= 0 ? "Ausgebucht" : `${frei} freie Plätze`;

  return (
    <Link to={`/schulung/${t.id}`} className="card card-hover course-card" style={{ color: "inherit" }}>
      <div className="accent" />
      <div className="body">
        <div className="row row-wrap" style={{ gap: 6 }}>
          {t.schulung.art && <Badge>{t.schulung.art}</Badge>}
          <Badge tone={seatTone}>{seatLabel}</Badge>
        </div>
        <h3>{t.schulung.name}</h3>
        <div className="course-meta">
          <div className="line">📅 {formatDate(t.datum_von)}</div>
          <div className="line">
            🕘 {formatTime(t.datum_von)} Uhr{t.dauer ? ` · ${t.dauer}` : ""}
          </div>
          {t.ort && <div className="line">📍 {[t.ort.name, t.ort.ort].filter(Boolean).join(", ")}</div>}
        </div>
        {t.funktionen.length > 0 && (
          <div className="tag-list">
            {t.funktionen.map((f) => (
              <span key={f} className="badge badge-yellow">
                {f}
              </span>
            ))}
          </div>
        )}
        <div className="foot">
          <div className="price">
            {eur(t.schulung.preis_rabattiert_cents ?? t.schulung.preis_standard_cents)}
            {t.schulung.preis_rabattiert_cents != null && (
              <small> / {eur(t.schulung.preis_standard_cents)} regulär</small>
            )}
          </div>
          <span className="btn btn-primary btn-sm">Details</span>
        </div>
      </div>
    </Link>
  );
}
