import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router";
import { api, type Termin, type BookingContext, ApiError } from "../api";
import { useResource, eur, formatDateTime } from "../lib";
import { Spinner, Alert, Badge, Field } from "../components/ui";
import { useAuth } from "../auth";

export function Course() {
  const { id } = useParams();
  const { me } = useAuth();
  const { data: termin, loading, error } = useResource<Termin>(`/termine/${id}`);
  const { data: ctx } = useResource<BookingContext>(me ? `/termine/${id}/booking-context` : null, [me?.id]);

  if (loading) return <Spinner center />;
  if (error || !termin)
    return (
      <div className="page">
        <div className="container">
          <Alert kind="error">{error ?? "Schulung nicht gefunden"}</Alert>
          <Link to="/" className="btn btn-ghost" style={{ marginTop: 16 }}>
            ← Zurück zur Übersicht
          </Link>
        </div>
      </div>
    );

  const frei = termin.freie_plaetze;

  return (
    <div className="page">
      <div className="container">
        <Link to="/" className="muted" style={{ fontSize: "0.9rem" }}>
          ← Alle Schulungen
        </Link>
        <div className="grid cols-2" style={{ marginTop: 16, alignItems: "start" }}>
          {/* Detail */}
          <div className="stack">
            <div className="row row-wrap" style={{ gap: 6 }}>
              {termin.schulung.art && <Badge>{termin.schulung.art}</Badge>
              }
              <Badge tone={frei <= 0 ? "red" : frei <= 5 ? "amber" : "green"}>
                {frei <= 0 ? "Ausgebucht" : `${frei} freie Plätze`}
              </Badge>
            </div>
            <h1 style={{ margin: "6px 0" }}>{termin.schulung.name}</h1>
            <div className="card card-pad">
              <div className="course-meta" style={{ fontSize: "0.96rem" }}>
                <div className="line">📅 {formatDateTime(termin.datum_von)}</div>
                {termin.dauer && <div className="line">⏱️ Dauer: {termin.dauer}</div>}
                {termin.ort && (
                  <div className="line">
                    📍 {termin.ort.name}
                    {termin.ort.adresse ? `, ${termin.ort.adresse}` : ""}
                    {termin.ort.ort ? `, ${termin.ort.plz ?? ""} ${termin.ort.ort}` : ""}
                  </div>
                )}
              </div>
            </div>
            {termin.schulung.beschreibung && (
              <div className="card card-pad">
                <h3>Beschreibung</h3>
                <p className="muted" style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                  {termin.schulung.beschreibung}
                </p>
              </div>
            )}
            {termin.funktionen.length > 0 && (
              <div className="card card-pad">
                <h3>Geeignet für</h3>
                <div className="tag-list">
                  {termin.funktionen.map((f) => (
                    <span key={f} className="badge badge-yellow">
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Booking panel */}
          <div className="card card-pad" style={{ position: "sticky", top: 88 }}>
            <BookingPanel termin={termin} ctx={ctx} loggedIn={!!me} />
          </div>
        </div>
      </div>
    </div>
  );
}

function BookingPanel({ termin, ctx, loggedIn }: { termin: Termin; ctx: BookingContext | null; loggedIn: boolean }) {
  const price = ctx?.einzelpreis_cents ?? termin.schulung.preis_standard_cents;

  return (
    <>
      <div className="spread" style={{ alignItems: "baseline" }}>
        <span className="muted">Preis pro Teilnehmer</span>
        <span className="price" style={{ fontSize: "1.5rem" }}>
          {eur(price)}
        </span>
      </div>
      <hr className="divider" />

      {!loggedIn && (
        <div className="stack">
          <p className="muted">Melden Sie sich an, um diese Schulung zu buchen.</p>
          <Link to="/login" className="btn btn-primary btn-block">
            Anmelden & buchen
          </Link>
          <Link to="/registrieren" className="btn btn-ghost btn-block">
            Neues Konto erstellen
          </Link>
        </div>
      )}

      {loggedIn && !ctx && <Spinner center />}

      {loggedIn && ctx && (
        <>
          {ctx.betrieb_already_registered && (
            <Alert kind="info">Ihr Betrieb ist für diese Schulung bereits angemeldet.</Alert>
          )}
          {!ctx.can_book && !ctx.betrieb_already_registered && (
            <Alert kind="info">
              Für diese Buchung ist der Geschäftsführer Ihres Betriebs zuständig.
            </Alert>
          )}
          {ctx.freie_plaetze <= 0 && <Alert kind="error">Diese Schulung ist ausgebucht.</Alert>}
          {ctx.can_book && !ctx.betrieb_already_registered && ctx.freie_plaetze > 0 && (
            <Wizard termin={termin} ctx={ctx} />
          )}
        </>
      )}
    </>
  );
}

interface Participant {
  person_id: string | null;
  vorname: string;
  nachname: string;
  email: string;
  verpflegung: "Standard" | "Vegetarisch";
}

function emptyParticipant(): Participant {
  return { person_id: null, vorname: "", nachname: "", email: "", verpflegung: "Standard" };
}

function Wizard({ termin, ctx }: { termin: Termin; ctx: BookingContext }) {
  const nav = useNavigate();
  const [step, setStep] = useState(1);
  const [anzahl, setAnzahl] = useState(1);
  const [parts, setParts] = useState<Participant[]>([emptyParticipant()]);
  const [addr, setAddr] = useState({
    name: ctx.rechnungsadresse.name,
    strasse: ctx.rechnungsadresse.strasse ?? "",
    plz: ctx.rechnungsadresse.plz ?? "",
    ort: ctx.rechnungsadresse.ort ?? "",
  });
  const [agb, setAgb] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const maxSeats = Math.min(ctx.freie_plaetze, 50);
  const total = ctx.einzelpreis_cents * anzahl;

  function setCount(n: number) {
    const c = Math.max(1, Math.min(maxSeats, n));
    setAnzahl(c);
    setParts((prev) => {
      const next = prev.slice(0, c);
      while (next.length < c) next.push(emptyParticipant());
      return next;
    });
  }

  function updatePart(i: number, patch: Partial<Participant>) {
    setParts((prev) => prev.map((p, idx) => (idx === i ? { ...p, ...patch } : p)));
  }

  const chosenIds = parts.map((p) => p.person_id).filter(Boolean);
  const step2Valid = parts.every((p) =>
    ctx.is_business ? !!p.person_id : p.vorname.trim() && p.nachname.trim(),
  );
  const step3Valid = addr.name.trim().length > 0;

  async function submit() {
    setSubmitting(true);
    setErr(null);
    try {
      const res = await api.post<{ bestellung_id: string }>("/bestellungen", {
        schulungstermin_id: termin.id,
        anzahl,
        participants: parts.map((p) => ({
          person_id: ctx.is_business ? p.person_id : null,
          vorname: p.vorname || undefined,
          nachname: p.nachname || undefined,
          email: p.email || undefined,
          verpflegung: p.verpflegung,
        })),
        rechnungsadresse: addr,
        agb_akzeptiert: true,
      });
      nav(`/bestellung/${res.bestellung_id}`);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Bestellung fehlgeschlagen");
      setSubmitting(false);
    }
  }

  return (
    <div className="stack">
      <div className="steps">
        {["Menge", "Teilnehmer", "Rechnung", "Bestätigung"].map((label, i) => {
          const n = i + 1;
          return (
            <div key={label} className={`step${step === n ? " active" : ""}${step > n ? " done" : ""}`}>
              <span className="num">{step > n ? "✓" : n}</span>
              {label}
            </div>
          );
        })}
      </div>

      {err && <Alert kind="error">{err}</Alert>}

      {step === 1 && (
        <div className="stack">
          <Field label="Anzahl Teilnehmer" hint={`Maximal ${maxSeats} buchbar`}>
            <div className="row">
              <button className="btn btn-ghost btn-sm" onClick={() => setCount(anzahl - 1)}>
                −
              </button>
              <input
                className="input"
                style={{ width: 80, textAlign: "center" }}
                type="number"
                min={1}
                max={maxSeats}
                value={anzahl}
                onChange={(e) => setCount(Number(e.target.value))}
              />
              <button className="btn btn-ghost btn-sm" onClick={() => setCount(anzahl + 1)}>
                +
              </button>
            </div>
          </Field>
          <div className="spread">
            <span className="muted">Zwischensumme</span>
            <span className="price">{eur(total)}</span>
          </div>
          <button className="btn btn-primary btn-block" onClick={() => setStep(2)}>
            Weiter
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="stack">
          {parts.map((p, i) => (
            <div key={i} className="card card-pad" style={{ boxShadow: "none", background: "#fafbfc" }}>
              <strong style={{ fontSize: "0.9rem" }}>Teilnehmer {i + 1}</strong>
              {ctx.is_business ? (
                <Field label="Person">
                  <select
                    className="select"
                    value={p.person_id ?? ""}
                    onChange={(e) => updatePart(i, { person_id: e.target.value || null })}
                  >
                    <option value="">Bitte wählen…</option>
                    {ctx.related_persons.map((rp) => (
                      <option
                        key={rp.id}
                        value={rp.id}
                        disabled={chosenIds.includes(rp.id) && p.person_id !== rp.id}
                      >
                        {rp.name}
                      </option>
                    ))}
                  </select>
                </Field>
              ) : (
                <div className="grid cols-2" style={{ gap: 10 }}>
                  <Field label="Vorname">
                    <input className="input" value={p.vorname} onChange={(e) => updatePart(i, { vorname: e.target.value })} />
                  </Field>
                  <Field label="Nachname">
                    <input className="input" value={p.nachname} onChange={(e) => updatePart(i, { nachname: e.target.value })} />
                  </Field>
                  <Field label="E-Mail (optional)">
                    <input className="input" type="email" value={p.email} onChange={(e) => updatePart(i, { email: e.target.value })} />
                  </Field>
                  <Field label="Verpflegung">
                    <VerpflegungSelect value={p.verpflegung} onChange={(v) => updatePart(i, { verpflegung: v })} />
                  </Field>
                </div>
              )}
              {ctx.is_business && (
                <Field label="Verpflegung">
                  <VerpflegungSelect value={p.verpflegung} onChange={(v) => updatePart(i, { verpflegung: v })} />
                </Field>
              )}
            </div>
          ))}
          {ctx.is_business && ctx.related_persons.length < anzahl && (
            <Alert kind="info">
              Es stehen nicht genügend buchbare Mitarbeiter zur Verfügung. Legen Sie weitere Mitarbeiter
              an oder reduzieren Sie die Anzahl.
            </Alert>
          )}
          <div className="row">
            <button className="btn btn-ghost" onClick={() => setStep(1)}>
              Zurück
            </button>
            <button className="btn btn-primary btn-block" disabled={!step2Valid} onClick={() => setStep(3)}>
              Weiter
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="stack">
          <Field label="Rechnungsempfänger">
            <input className="input" value={addr.name} onChange={(e) => setAddr({ ...addr, name: e.target.value })} />
          </Field>
          <Field label="Straße">
            <input className="input" value={addr.strasse} onChange={(e) => setAddr({ ...addr, strasse: e.target.value })} />
          </Field>
          <div className="grid cols-2" style={{ gap: 10 }}>
            <Field label="PLZ">
              <input className="input" value={addr.plz} onChange={(e) => setAddr({ ...addr, plz: e.target.value })} />
            </Field>
            <Field label="Ort">
              <input className="input" value={addr.ort} onChange={(e) => setAddr({ ...addr, ort: e.target.value })} />
            </Field>
          </div>
          <div className="row">
            <button className="btn btn-ghost" onClick={() => setStep(2)}>
              Zurück
            </button>
            <button className="btn btn-primary btn-block" disabled={!step3Valid} onClick={() => setStep(4)}>
              Weiter
            </button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="stack">
          <div className="card card-pad" style={{ boxShadow: "none", background: "#fafbfc" }}>
            <div className="spread">
              <span className="muted">{termin.schulung.name}</span>
            </div>
            <div className="spread">
              <span className="muted">{anzahl} × {eur(ctx.einzelpreis_cents)}</span>
              <span className="price">{eur(total)}</span>
            </div>
          </div>
          <label className="checkbox">
            <input type="checkbox" checked={agb} onChange={(e) => setAgb(e.target.checked)} />
            <span>
              Ich akzeptiere die <Link to="/agb" target="_blank">AGB und Datenschutzbestimmungen</Link>.
            </span>
          </label>
          <div className="row">
            <button className="btn btn-ghost" onClick={() => setStep(3)}>
              Zurück
            </button>
            <button className="btn btn-primary btn-block" disabled={!agb || submitting} onClick={submit}>
              {submitting ? "Wird gebucht…" : "Zahlungspflichtig bestellen"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function VerpflegungSelect({
  value,
  onChange,
}: {
  value: "Standard" | "Vegetarisch";
  onChange: (v: "Standard" | "Vegetarisch") => void;
}) {
  return (
    <select className="select" value={value} onChange={(e) => onChange(e.target.value as "Standard" | "Vegetarisch")}>
      <option value="Standard">Standard</option>
      <option value="Vegetarisch">Vegetarisch</option>
    </select>
  );
}
