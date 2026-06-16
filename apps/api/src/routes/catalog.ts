import { Hono } from "hono";
import { verifyJwt } from "../crypto";
import {
  freiePlaetze,
  registrierteBetriebe,
  unitPriceCents,
  getCurrentContext,
  nowIso,
} from "../db";

export const catalog = new Hono<{ Bindings: Env }>();

interface TerminListRow {
  id: string;
  datum_von: string;
  datum_bis: string;
  dauer: string | null;
  max_teilnehmer: number;
  buchbar: number;
  schulung_id: string;
  schulung_name: string;
  beschreibung: string;
  preis_standard: number;
  preis_rabattiert: number | null;
  art_name: string | null;
  ort_name: string | null;
  ort_adresse: string | null;
  ort_plz: string | null;
  ort_ort: string | null;
  belegt: number;
  funktionen: string | null;
}

const LIST_SQL = `
  SELECT t.id, t.datum_von, t.datum_bis, t.dauer, t.max_teilnehmer, t.buchbar,
         s.id AS schulung_id, s.name AS schulung_name, s.beschreibung,
         s.preis_standard, s.preis_rabattiert,
         art.name AS art_name,
         o.name AS ort_name, o.adresse AS ort_adresse, o.plz AS ort_plz, o.ort AS ort_ort,
         (SELECT COUNT(*) FROM schulungsteilnehmer st WHERE st.schulungstermin_id = t.id) AS belegt,
         (SELECT GROUP_CONCAT(f.name, '|') FROM schulung_funktion sf
            JOIN funktion f ON f.id = sf.funktion_id WHERE sf.schulung_id = s.id) AS funktionen
    FROM schulungstermin t
    JOIN schulung s ON s.id = t.schulung_id
    LEFT JOIN schulungsart art ON art.id = s.art_id
    LEFT JOIN schulungsort o ON o.id = t.ort_id`;

function shapeTermin(r: TerminListRow) {
  return {
    id: r.id,
    datum_von: r.datum_von,
    datum_bis: r.datum_bis,
    dauer: r.dauer,
    buchbar: !!r.buchbar,
    max_teilnehmer: r.max_teilnehmer,
    freie_plaetze: r.max_teilnehmer - r.belegt,
    schulung: {
      id: r.schulung_id,
      name: r.schulung_name,
      beschreibung: r.beschreibung,
      art: r.art_name,
      preis_standard_cents: r.preis_standard,
      preis_rabattiert_cents: r.preis_rabattiert,
    },
    ort: r.ort_name
      ? { name: r.ort_name, adresse: r.ort_adresse, plz: r.ort_plz, ort: r.ort_ort }
      : null,
    funktionen: r.funktionen ? r.funktionen.split("|") : [],
  };
}

// Public: upcoming bookable sessions, soonest first.
catalog.get("/", async (c) => {
  const { results } = await c.env.DB.prepare(
    `${LIST_SQL} WHERE t.datum_von >= ? AND t.buchbar = 1 ORDER BY t.datum_von ASC`,
  )
    .bind(nowIso())
    .all<TerminListRow>();
  return c.json({ items: results.map(shapeTermin) });
});

// Public: single session detail.
catalog.get("/:id", async (c) => {
  const r = await c.env.DB.prepare(`${LIST_SQL} WHERE t.id = ?`).bind(c.req.param("id")).first<TerminListRow>();
  if (!r) return c.json({ error: "Nicht gefunden" }, 404);
  return c.json(shapeTermin(r));
});

// Authenticated: everything the checkout wizard needs for this session —
// price for THIS buyer, free seats, eligible employees, prefilled address.
catalog.get("/:id/booking-context", async (c) => {
  const authHeader = c.req.header("Authorization");
  const payload = authHeader?.startsWith("Bearer ")
    ? await verifyJwt(authHeader.slice(7), c.env.JWT_SECRET)
    : null;
  if (!payload) return c.json({ error: "Nicht angemeldet" }, 401);
  const ctx = await getCurrentContext(c.env.DB, payload.sub);
  if (!ctx?.person) return c.json({ error: "Kein Profil" }, 403);

  const terminId = c.req.param("id");
  const termin = await c.env.DB.prepare(
    "SELECT id, schulung_id, max_teilnehmer FROM schulungstermin WHERE id = ?",
  )
    .bind(terminId)
    .first<{ id: string; schulung_id: string; max_teilnehmer: number }>();
  if (!termin) return c.json({ error: "Nicht gefunden" }, 404);

  const frei = await freiePlaetze(c.env.DB, terminId, termin.max_teilnehmer);
  const unit = await unitPriceCents(c.env.DB, ctx.person, termin.schulung_id);

  // Eligible funktion filter for the course (empty = no restriction).
  const { results: eligible } = await c.env.DB.prepare(
    "SELECT funktion_id FROM schulung_funktion WHERE schulung_id = ?",
  )
    .bind(termin.schulung_id)
    .all<{ funktion_id: string }>();
  const eligibleSet = new Set(eligible.map((e) => e.funktion_id));

  // Already-registered persons on this session.
  const { results: registered } = await c.env.DB.prepare(
    "SELECT person_id FROM schulungsteilnehmer WHERE schulungstermin_id = ? AND person_id IS NOT NULL",
  )
    .bind(terminId)
    .all<{ person_id: string }>();
  const registeredSet = new Set(registered.map((r) => r.person_id));

  let relatedPersons: { id: string; name: string; funktion_id: string | null }[] = [];
  if (ctx.person.betrieb_id) {
    const { results } = await c.env.DB.prepare(
      "SELECT id, vorname, nachname, funktion_id FROM person WHERE betrieb_id = ?",
    )
      .bind(ctx.person.betrieb_id)
      .all<{ id: string; vorname: string; nachname: string; funktion_id: string | null }>();
    relatedPersons = results
      .filter((p) => !registeredSet.has(p.id))
      .filter((p) => eligibleSet.size === 0 || (p.funktion_id ? eligibleSet.has(p.funktion_id) : false))
      .map((p) => ({ id: p.id, name: `${p.vorname} ${p.nachname}`, funktion_id: p.funktion_id }));
  }

  const betriebeSet = await registrierteBetriebe(c.env.DB, terminId);

  return c.json({
    freie_plaetze: frei,
    einzelpreis_cents: unit,
    is_business: !!ctx.person.betrieb_id,
    can_book: !!ctx.person.can_book_schulungen && (!ctx.person.betrieb_id || ctx.isGeschaeftsfuehrer),
    betrieb_already_registered: ctx.person.betrieb_id ? betriebeSet.has(ctx.person.betrieb_id) : false,
    related_persons: relatedPersons,
    rechnungsadresse: ctx.betrieb
      ? {
          name: ctx.betrieb.name,
          strasse: ctx.betrieb.adresse,
          plz: ctx.betrieb.plz,
          ort: ctx.betrieb.ort,
        }
      : { name: `${ctx.person.vorname} ${ctx.person.nachname}`, strasse: ctx.person.adresse, plz: ctx.person.plz, ort: ctx.person.ort },
  });
});
