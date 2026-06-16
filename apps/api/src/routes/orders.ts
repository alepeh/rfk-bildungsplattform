import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { uuid } from "../crypto";
import { freiePlaetze, unitPriceCents, nowIso } from "../db";
import { requireUser, type AuthVariables } from "../auth";
import { sendMail, orderConfirmation, type VenueInfo } from "../email";

export const orders = new Hono<{ Bindings: Env; Variables: AuthVariables }>();

const Participant = z.object({
  person_id: z.string().nullable().optional(),
  vorname: z.string().max(150).optional(),
  nachname: z.string().max(150).optional(),
  email: z.string().email().nullable().optional(),
  verpflegung: z.enum(["Standard", "Vegetarisch"]).default("Standard"),
});

const OrderInput = z.object({
  schulungstermin_id: z.string(),
  anzahl: z.number().int().min(1).max(50),
  participants: z.array(Participant).min(1),
  rechnungsadresse: z.object({
    name: z.string().min(1),
    strasse: z.string().optional().nullable(),
    plz: z.string().optional().nullable(),
    ort: z.string().optional().nullable(),
  }),
  agb_akzeptiert: z.literal(true),
});

orders.post("/", requireUser, zValidator("json", OrderInput), async (c) => {
  const b = c.req.valid("json");
  const { current } = c.var;
  const db = c.env.DB;

  if (!current.person || !current.person.can_book_schulungen) {
    return c.json({ error: "Buchung nicht erlaubt" }, 403);
  }
  if (current.person.betrieb_id && !current.isGeschaeftsfuehrer) {
    return c.json({ error: "Nur der Geschäftsführer kann für den Betrieb buchen" }, 403);
  }
  if (b.participants.length !== b.anzahl) {
    return c.json({ error: "Anzahl der Teilnehmer stimmt nicht mit der Bestellmenge überein" }, 400);
  }

  const termin = await db
    .prepare("SELECT id, schulung_id, max_teilnehmer FROM schulungstermin WHERE id = ?")
    .bind(b.schulungstermin_id)
    .first<{ id: string; schulung_id: string; max_teilnehmer: number }>();
  if (!termin) return c.json({ error: "Schulungstermin nicht gefunden" }, 404);

  const frei = await freiePlaetze(db, termin.id, termin.max_teilnehmer);
  if (b.anzahl > frei) return c.json({ error: "Nicht genügend freie Plätze" }, 409);

  // Reject persons already registered on this session.
  const { results: registered } = await db
    .prepare("SELECT person_id FROM schulungsteilnehmer WHERE schulungstermin_id = ? AND person_id IS NOT NULL")
    .bind(termin.id)
    .all<{ person_id: string }>();
  const registeredSet = new Set(registered.map((r) => r.person_id));
  for (const p of b.participants) {
    if (p.person_id && registeredSet.has(p.person_id)) {
      return c.json({ error: "Eine Person ist bereits für diese Schulung angemeldet" }, 409);
    }
  }

  const unit = await unitPriceCents(db, current.person, termin.schulung_id);
  const total = unit * b.anzahl;
  const bestellungId = uuid();
  const now = nowIso();

  const stmts: D1PreparedStatement[] = [
    db
      .prepare(
        `INSERT INTO bestellung (id, person_id, schulungstermin_id, anzahl, einzelpreis, gesamtpreis,
            status, rechnungsadresse_name, rechnungsadresse_strasse, rechnungsadresse_plz,
            rechnungsadresse_ort, created_at, updated_at)
         VALUES (?,?,?,?,?,?, 'Bestellt', ?,?,?,?,?,?)`,
      )
      .bind(
        bestellungId, current.person.id, termin.id, b.anzahl, unit, total,
        b.rechnungsadresse.name, b.rechnungsadresse.strasse ?? null, b.rechnungsadresse.plz ?? null,
        b.rechnungsadresse.ort ?? null, now, now,
      ),
  ];
  for (const p of b.participants) {
    stmts.push(
      db
        .prepare(
          `INSERT INTO schulungsteilnehmer (id, schulungstermin_id, bestellung_id, person_id,
              vorname, nachname, email, verpflegung, status, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?, 'Angemeldet', ?,?)`,
        )
        .bind(
          uuid(), termin.id, bestellungId, p.person_id ?? null,
          p.vorname ?? null, p.nachname ?? null, p.email ?? null, p.verpflegung, now, now,
        ),
    );
  }
  await db.batch(stmts);

  // Confirmation email (failure does not roll back the order).
  const detail = await db
    .prepare(
      `SELECT s.name AS schulung_name, t.datum_von, t.dauer,
              o.name AS ort_name, o.adresse, o.plz, o.ort, o.kontakt, o.telefon
         FROM schulungstermin t JOIN schulung s ON s.id = t.schulung_id
         LEFT JOIN schulungsort o ON o.id = t.ort_id WHERE t.id = ?`,
    )
    .bind(termin.id)
    .first<{
      schulung_name: string;
      datum_von: string;
      dauer: string | null;
      ort_name: string | null;
      adresse: string | null;
      plz: string | null;
      ort: string | null;
      kontakt: string | null;
      telefon: string | null;
    }>();
  if (detail) {
    const venue: VenueInfo | null = detail.ort_name
      ? { name: detail.ort_name, adresse: detail.adresse, plz: detail.plz, ort: detail.ort, kontakt: detail.kontakt, telefon: detail.telefon }
      : null;
    const mail = orderConfirmation({
      bestellungId,
      schulungName: detail.schulung_name,
      datumVon: detail.datum_von,
      dauer: detail.dauer,
      anzahl: b.anzahl,
      gesamtpreisCents: total,
      ort: venue,
    });
    if (current.user.email) await sendMail(c.env, { to: current.user.email, ...mail });
    await sendMail(c.env, { to: c.env.ADMIN_EMAIL, ...mail });
  }

  return c.json({ ok: true, bestellung_id: bestellungId, gesamtpreis_cents: total }, 201);
});

// My orders (Geschäftsführer / individual buyer).
orders.get("/", requireUser, async (c) => {
  const personId = c.var.current.person?.id;
  if (!personId) return c.json({ items: [] });
  const { results } = await c.env.DB.prepare(
    `SELECT b.id, b.anzahl, b.einzelpreis, b.gesamtpreis, b.status, b.created_at,
            s.name AS schulung_name, t.datum_von
       FROM bestellung b
       JOIN schulungstermin t ON t.id = b.schulungstermin_id
       JOIN schulung s ON s.id = t.schulung_id
      WHERE b.person_id = ? ORDER BY b.created_at DESC`,
  )
    .bind(personId)
    .all();
  return c.json({ items: results });
});

// Completed courses for the signed-in person (status = Teilgenommen), with
// downloadable course materials.
orders.get("/meine-schulungen", requireUser, async (c) => {
  const personId = c.var.current.person?.id;
  if (!personId) return c.json({ items: [] });
  const { results } = await c.env.DB.prepare(
    `SELECT st.id AS teilnehmer_id, st.status, s.id AS schulung_id, s.name AS schulung_name,
            t.datum_von, o.name AS ort_name
       FROM schulungsteilnehmer st
       JOIN schulungstermin t ON t.id = st.schulungstermin_id
       JOIN schulung s ON s.id = t.schulung_id
       LEFT JOIN schulungsort o ON o.id = t.ort_id
      WHERE st.person_id = ? AND st.status = 'Teilgenommen'
      ORDER BY t.datum_von DESC`,
  )
    .bind(personId)
    .all<{ schulung_id: string; teilnehmer_id: string; status: string; schulung_name: string; datum_von: string; ort_name: string | null }>();

  const items = [];
  for (const r of results) {
    const { results: mats } = await c.env.DB.prepare(
      "SELECT id, name, filename FROM schulungsunterlage WHERE schulung_id = ?",
    )
      .bind(r.schulung_id)
      .all();
    items.push({ ...r, unterlagen: mats });
  }
  return c.json({ items });
});
