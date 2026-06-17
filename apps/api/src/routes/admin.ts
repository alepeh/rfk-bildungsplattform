import { Hono } from "hono";
import { z } from "zod";
import { uuid } from "../crypto";
import { nowIso } from "../db";
import { requireStaff, type AuthVariables } from "../auth";
import { sendMail, reminderEmail, activationEmail, certificateReadyEmail, type VenueInfo } from "../email";
import { attendanceSheetPdf, type AttendanceRow } from "../pdf";

function germanDate(iso: string): string {
  return new Date(iso).toLocaleDateString("de-AT", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    timeZone: "Europe/Vienna",
  });
}

export const admin = new Hono<{ Bindings: Env; Variables: AuthVariables }>();
admin.use("*", requireStaff);

// ── Generic, allowlisted CRUD ────────────────────────────────────────
// Only the columns named here are ever written — keeps dynamic SQL safe.
type Col = { name: string; type: "text" | "int" };
interface Resource {
  table: string;
  cols: Col[];
  order?: string;
}
const RESOURCES: Record<string, Resource> = {
  schulungsarten: { table: "schulungsart", cols: [{ name: "name", type: "text" }], order: "name" },
  funktionen: {
    table: "funktion",
    cols: [{ name: "name", type: "text" }, { name: "sortierung", type: "int" }],
    order: "sortierung, name",
  },
  organisationen: {
    table: "organisation",
    cols: [{ name: "name", type: "text" }, { name: "preisrabatt", type: "int" }],
    order: "name",
  },
  schulungsorte: {
    table: "schulungsort",
    cols: ["name", "adresse", "plz", "ort", "kontakt", "telefon", "email", "hinweise"].map((name) => ({ name, type: "text" as const })),
    order: "name",
  },
  betriebe: {
    table: "betrieb",
    cols: [
      ...["name", "kehrgebiet", "adresse", "plz", "ort", "telefon", "email", "geschaeftsfuehrer_id"].map(
        (name) => ({ name, type: "text" as const }),
      ),
    ],
    order: "name",
  },
  schulungen: {
    table: "schulung",
    cols: [
      { name: "name", type: "text" },
      { name: "beschreibung", type: "text" },
      { name: "art_id", type: "text" },
      { name: "preis_standard", type: "int" },
      { name: "preis_rabattiert", type: "int" },
    ],
    order: "name",
  },
  schulungstermine: {
    table: "schulungstermin",
    cols: [
      { name: "schulung_id", type: "text" },
      { name: "ort_id", type: "text" },
      { name: "datum_von", type: "text" },
      { name: "datum_bis", type: "text" },
      { name: "dauer", type: "text" },
      { name: "max_teilnehmer", type: "int" },
      { name: "min_teilnehmer", type: "int" },
      { name: "buchbar", type: "int" },
    ],
    order: "datum_von DESC",
  },
};

function coerce(col: Col, v: unknown): unknown {
  if (v === undefined || v === null || v === "") return null;
  return col.type === "int" ? Number(v) : String(v);
}

for (const [slug, r] of Object.entries(RESOURCES)) {
  admin.get(`/${slug}`, async (c) => {
    const { results } = await c.env.DB.prepare(
      `SELECT * FROM ${r.table}${r.order ? ` ORDER BY ${r.order}` : ""}`,
    ).all();
    return c.json({ items: results });
  });

  admin.post(`/${slug}`, async (c) => {
    const body = (await c.req.json()) as Record<string, unknown>;
    const id = uuid();
    const now = nowIso();
    const names = r.cols.map((col) => col.name);
    const values = r.cols.map((col) => coerce(col, body[col.name]));
    const placeholders = names.map(() => "?").join(",");
    await c.env.DB.prepare(
      `INSERT INTO ${r.table} (id, ${names.join(",")}, created_at, updated_at) VALUES (?, ${placeholders}, ?, ?)`,
    )
      .bind(id, ...values, now, now)
      .run();
    return c.json({ id }, 201);
  });

  admin.put(`/${slug}/:id`, async (c) => {
    const body = (await c.req.json()) as Record<string, unknown>;
    const present = r.cols.filter((col) => col.name in body);
    if (present.length === 0) return c.json({ error: "Keine Felder" }, 400);
    const setClause = present.map((col) => `${col.name} = ?`).join(", ");
    const values = present.map((col) => coerce(col, body[col.name]));
    await c.env.DB.prepare(`UPDATE ${r.table} SET ${setClause}, updated_at = ? WHERE id = ?`)
      .bind(...values, nowIso(), c.req.param("id"))
      .run();
    return c.json({ ok: true });
  });

  admin.delete(`/${slug}/:id`, async (c) => {
    await c.env.DB.prepare(`DELETE FROM ${r.table} WHERE id = ?`).bind(c.req.param("id")).run();
    return c.json({ ok: true });
  });
}

// ── Course eligibility (schulung_funktion) ───────────────────────────
admin.put("/schulungen/:id/funktionen", async (c) => {
  const id = c.req.param("id");
  const body = z.object({ funktion_ids: z.array(z.string()) }).parse(await c.req.json());
  const stmts: D1PreparedStatement[] = [
    c.env.DB.prepare("DELETE FROM schulung_funktion WHERE schulung_id = ?").bind(id),
    ...body.funktion_ids.map((fid) =>
      c.env.DB.prepare("INSERT INTO schulung_funktion (schulung_id, funktion_id) VALUES (?, ?)").bind(id, fid),
    ),
  ];
  await c.env.DB.batch(stmts);
  return c.json({ ok: true });
});

// ── People & activation ──────────────────────────────────────────────
admin.get("/personen", async (c) => {
  const activated = c.req.query("activated");
  const q = c.req.query("q");
  const where: string[] = [];
  const binds: unknown[] = [];
  if (activated === "0" || activated === "1") {
    where.push("p.is_activated = ?");
    binds.push(Number(activated));
  }
  if (q) {
    where.push("(p.vorname LIKE ? OR p.nachname LIKE ? OR p.email LIKE ?)");
    binds.push(`%${q}%`, `%${q}%`, `%${q}%`);
  }
  const { results } = await c.env.DB.prepare(
    `SELECT p.id, p.vorname, p.nachname, p.email, p.telefon, p.is_activated, p.can_book_schulungen,
            p.activation_requested_at, p.funktion_id, p.organisation_id, p.betrieb_id,
            f.name AS funktion_name, b.name AS betrieb_name, u.username, u.id AS user_id
       FROM person p
       LEFT JOIN funktion f ON f.id = p.funktion_id
       LEFT JOIN betrieb b ON b.id = p.betrieb_id
       LEFT JOIN users u ON u.id = p.user_id
       ${where.length ? `WHERE ${where.join(" AND ")}` : ""}
       ORDER BY p.nachname, p.vorname`,
  )
    .bind(...binds)
    .all();
  return c.json({ items: results });
});

admin.post("/personen/:id/activate", async (c) => {
  const id = c.req.param("id");
  const p = await c.env.DB.prepare("SELECT id, user_id, email FROM person WHERE id = ?")
    .bind(id)
    .first<{ id: string; user_id: string | null; email: string | null }>();
  if (!p) return c.json({ error: "Nicht gefunden" }, 404);
  const now = nowIso();
  const stmts: D1PreparedStatement[] = [
    c.env.DB.prepare("UPDATE person SET is_activated = 1, activated_at = ?, activated_by_id = ?, updated_at = ? WHERE id = ?")
      .bind(now, c.var.current.user.id, now, id),
  ];
  if (p.user_id) {
    stmts.push(c.env.DB.prepare("UPDATE users SET is_active = 1, updated_at = ? WHERE id = ?").bind(now, p.user_id));
  }
  await c.env.DB.batch(stmts);
  if (p.email) await sendMail(c.env, { to: p.email, ...activationEmail(c.env.APP_URL) });
  return c.json({ ok: true });
});

admin.post("/personen/:id/deactivate", async (c) => {
  const id = c.req.param("id");
  const p = await c.env.DB.prepare("SELECT user_id FROM person WHERE id = ?").bind(id).first<{ user_id: string | null }>();
  const now = nowIso();
  const stmts: D1PreparedStatement[] = [
    c.env.DB.prepare("UPDATE person SET is_activated = 0, updated_at = ? WHERE id = ?").bind(now, id),
  ];
  if (p?.user_id) stmts.push(c.env.DB.prepare("UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?").bind(now, p.user_id));
  await c.env.DB.batch(stmts);
  return c.json({ ok: true });
});

admin.patch("/personen/:id", async (c) => {
  const body = z
    .object({
      can_book_schulungen: z.boolean().optional(),
      funktion_id: z.string().nullable().optional(),
      organisation_id: z.string().nullable().optional(),
      betrieb_id: z.string().nullable().optional(),
    })
    .parse(await c.req.json());
  const sets: string[] = [];
  const binds: unknown[] = [];
  for (const [k, v] of Object.entries(body)) {
    sets.push(`${k} = ?`);
    binds.push(typeof v === "boolean" ? (v ? 1 : 0) : v);
  }
  if (!sets.length) return c.json({ error: "Keine Felder" }, 400);
  await c.env.DB.prepare(`UPDATE person SET ${sets.join(", ")}, updated_at = ? WHERE id = ?`)
    .bind(...binds, nowIso(), c.req.param("id"))
    .run();
  return c.json({ ok: true });
});

// ── Participants of a session ────────────────────────────────────────
admin.get("/schulungstermine/:id/teilnehmer", async (c) => {
  const { results } = await c.env.DB.prepare(
    `SELECT st.id, st.status, st.verpflegung,
            COALESCE(p.vorname, st.vorname) AS vorname,
            COALESCE(p.nachname, st.nachname) AS nachname,
            COALESCE(p.email, st.email) AS email,
            COALESCE(p.telefon, '') AS telefon,
            b.name AS betrieb_name, p.dsv_akzeptiert
       FROM schulungsteilnehmer st
       LEFT JOIN person p ON p.id = st.person_id
       LEFT JOIN betrieb b ON b.id = p.betrieb_id
      WHERE st.schulungstermin_id = ? ORDER BY nachname, vorname`,
  )
    .bind(c.req.param("id"))
    .all();
  return c.json({ items: results });
});

admin.patch("/teilnehmer/:id", async (c) => {
  const body = z
    .object({
      status: z.enum(["Angemeldet", "Teilgenommen", "Entschuldigt", "Unentschuldigt"]).optional(),
      verpflegung: z.enum(["Standard", "Vegetarisch"]).optional(),
    })
    .parse(await c.req.json());
  const sets: string[] = [];
  const binds: unknown[] = [];
  if (body.status) {
    sets.push("status = ?");
    binds.push(body.status);
  }
  if (body.verpflegung) {
    sets.push("verpflegung = ?");
    binds.push(body.verpflegung);
  }
  if (!sets.length) return c.json({ error: "Keine Felder" }, 400);
  const teilnehmerId = c.req.param("id");
  await c.env.DB.prepare(`UPDATE schulungsteilnehmer SET ${sets.join(", ")}, updated_at = ? WHERE id = ?`)
    .bind(...binds, nowIso(), teilnehmerId)
    .run();

  // On completion, notify the participant that their certificate is ready.
  if (body.status === "Teilgenommen") {
    const row = await c.env.DB.prepare(
      `SELECT COALESCE(p.email, st.email) AS email, s.name AS schulung_name
         FROM schulungsteilnehmer st
         JOIN schulungstermin t ON t.id = st.schulungstermin_id
         JOIN schulung s ON s.id = t.schulung_id
         LEFT JOIN person p ON p.id = st.person_id
        WHERE st.id = ?`,
    )
      .bind(teilnehmerId)
      .first<{ email: string | null; schulung_name: string }>();
    if (row?.email) {
      await sendMail(c.env, {
        to: row.email,
        ...certificateReadyEmail({ schulungName: row.schulung_name, appUrl: c.env.APP_URL }),
      });
    }
  }
  return c.json({ ok: true });
});

// CSV attendance export: Person, Betrieb, Email, Telefon, DSV.
admin.get("/schulungstermine/:id/export.csv", async (c) => {
  const { results } = await c.env.DB.prepare(
    `SELECT COALESCE(p.vorname, st.vorname) AS vorname,
            COALESCE(p.nachname, st.nachname) AS nachname,
            b.name AS betrieb_name,
            COALESCE(p.email, st.email) AS email,
            COALESCE(p.telefon, '') AS telefon,
            p.dsv_akzeptiert AS dsv
       FROM schulungsteilnehmer st
       LEFT JOIN person p ON p.id = st.person_id
       LEFT JOIN betrieb b ON b.id = p.betrieb_id
      WHERE st.schulungstermin_id = ? ORDER BY nachname, vorname`,
  )
    .bind(c.req.param("id"))
    .all<{ vorname: string | null; nachname: string | null; betrieb_name: string | null; email: string | null; telefon: string | null; dsv: number | null }>();
  const esc = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const header = ["Person", "Betrieb", "Email", "Telefon", "DSV akzeptiert"];
  const rows = results.map((r) =>
    [
      `${r.vorname ?? ""} ${r.nachname ?? ""}`.trim(),
      r.betrieb_name ?? "",
      r.email ?? "",
      r.telefon ?? "",
      r.dsv ? "Ja" : "Nein",
    ]
      .map(esc)
      .join(";"),
  );
  const csv = "﻿" + [header.map(esc).join(";"), ...rows].join("\r\n");
  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="teilnehmer-${c.req.param("id").slice(0, 8)}.csv"`,
    },
  });
});

// Attendance sheet PDF (landscape A4) — the port of the legacy ReportLab sheet.
admin.get("/schulungstermine/:id/teilnehmer.pdf", async (c) => {
  const id = c.req.param("id");
  const head = await c.env.DB.prepare(
    `SELECT s.name AS schulung_name, t.datum_von, o.name AS ort_name
       FROM schulungstermin t JOIN schulung s ON s.id = t.schulung_id
       LEFT JOIN schulungsort o ON o.id = t.ort_id WHERE t.id = ?`,
  )
    .bind(id)
    .first<{ schulung_name: string; datum_von: string; ort_name: string | null }>();
  if (!head) return c.json({ error: "Nicht gefunden" }, 404);

  const { results } = await c.env.DB.prepare(
    `SELECT COALESCE(p.vorname, st.vorname) AS vorname,
            COALESCE(p.nachname, st.nachname) AS nachname,
            b.name AS betrieb_name,
            COALESCE(p.email, st.email) AS email,
            COALESCE(p.telefon, '') AS telefon,
            p.dsv_akzeptiert AS dsv
       FROM schulungsteilnehmer st
       LEFT JOIN person p ON p.id = st.person_id
       LEFT JOIN betrieb b ON b.id = p.betrieb_id
      WHERE st.schulungstermin_id = ? ORDER BY nachname, vorname`,
  )
    .bind(id)
    .all<{ vorname: string | null; nachname: string | null; betrieb_name: string | null; email: string | null; telefon: string | null; dsv: number | null }>();

  const rows: AttendanceRow[] = results.map((r) => ({
    name: `${r.vorname ?? ""} ${r.nachname ?? ""}`.trim(),
    betrieb: r.betrieb_name ?? "",
    email: r.email ?? "",
    telefon: r.telefon ?? "",
    dsv: !!r.dsv,
  }));

  const pdf = await attendanceSheetPdf({
    schulungName: head.schulung_name,
    datum: germanDate(head.datum_von),
    ort: head.ort_name,
    rows,
  });
  return new Response(pdf as unknown as BodyInit, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": `attachment; filename="teilnehmerliste-${id.slice(0, 8)}.pdf"`,
    },
  });
});

// Send a reminder email to every participant of a session that has an address.
admin.post("/schulungstermine/:id/reminder", async (c) => {
  const id = c.req.param("id");
  const detail = await c.env.DB.prepare(
    `SELECT s.name AS schulung_name, t.datum_von, t.dauer,
            o.name AS ort_name, o.adresse, o.plz, o.ort, o.kontakt, o.telefon
       FROM schulungstermin t JOIN schulung s ON s.id = t.schulung_id
       LEFT JOIN schulungsort o ON o.id = t.ort_id WHERE t.id = ?`,
  )
    .bind(id)
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
  if (!detail) return c.json({ error: "Nicht gefunden" }, 404);

  const { results } = await c.env.DB.prepare(
    `SELECT COALESCE(p.email, st.email) AS email FROM schulungsteilnehmer st
       LEFT JOIN person p ON p.id = st.person_id WHERE st.schulungstermin_id = ?`,
  )
    .bind(id)
    .all<{ email: string | null }>();
  const venue: VenueInfo | null = detail.ort_name
    ? { name: detail.ort_name, adresse: detail.adresse, plz: detail.plz, ort: detail.ort, kontakt: detail.kontakt, telefon: detail.telefon }
    : null;
  const mail = reminderEmail({ schulungName: detail.schulung_name, datumVon: detail.datum_von, dauer: detail.dauer, ort: venue });
  let sent = 0;
  for (const r of results) {
    if (r.email) {
      const ok = await sendMail(c.env, { to: r.email, ...mail });
      if (ok) sent++;
    }
  }
  return c.json({ ok: true, sent });
});

// ── Documents (R2 upload + metadata) ─────────────────────────────────
admin.get("/documents", async (c) => {
  const { results } = await c.env.DB.prepare(
    `SELECT d.id, d.name, d.description, d.filename, d.size, d.created_at,
            (SELECT GROUP_CONCAT(funktion_id) FROM document_funktion WHERE document_id = d.id) AS funktion_ids
       FROM document d ORDER BY d.name`,
  ).all();
  return c.json({ items: results });
});

admin.post("/documents", async (c) => {
  const form = await c.req.formData();
  const file = form.get("file");
  const name = String(form.get("name") ?? "");
  const description = form.get("description") ? String(form.get("description")) : null;
  const funktionIds = form.getAll("funktion_ids").map(String).filter(Boolean);
  if (!(file instanceof File) || !name) return c.json({ error: "Datei und Name erforderlich" }, 400);

  const id = uuid();
  const key = `documents/${id}/${file.name}`;
  await c.env.DOCUMENTS.put(key, await file.arrayBuffer(), {
    httpMetadata: { contentType: file.type || "application/octet-stream" },
  });
  const now = nowIso();
  const stmts: D1PreparedStatement[] = [
    c.env.DB.prepare(
      "INSERT INTO document (id, name, description, r2_key, filename, content_type, size, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
    ).bind(id, name, description, key, file.name, file.type || null, file.size, now, now),
    ...funktionIds.map((fid) =>
      c.env.DB.prepare("INSERT INTO document_funktion (document_id, funktion_id) VALUES (?, ?)").bind(id, fid),
    ),
  ];
  await c.env.DB.batch(stmts);
  return c.json({ id }, 201);
});

admin.delete("/documents/:id", async (c) => {
  const id = c.req.param("id");
  const doc = await c.env.DB.prepare("SELECT r2_key FROM document WHERE id = ?").bind(id).first<{ r2_key: string }>();
  if (doc) await c.env.DOCUMENTS.delete(doc.r2_key);
  await c.env.DB.batch([
    c.env.DB.prepare("DELETE FROM document_funktion WHERE document_id = ?").bind(id),
    c.env.DB.prepare("DELETE FROM document WHERE id = ?").bind(id),
  ]);
  return c.json({ ok: true });
});

// Course material upload.
admin.post("/schulungen/:id/unterlagen", async (c) => {
  const schulungId = c.req.param("id");
  const form = await c.req.formData();
  const file = form.get("file");
  const name = String(form.get("name") ?? "");
  if (!(file instanceof File) || !name) return c.json({ error: "Datei und Name erforderlich" }, 400);
  const id = uuid();
  const key = `unterlagen/${schulungId}/${id}/${file.name}`;
  await c.env.DOCUMENTS.put(key, await file.arrayBuffer(), {
    httpMetadata: { contentType: file.type || "application/octet-stream" },
  });
  const now = nowIso();
  await c.env.DB.prepare(
    "INSERT INTO schulungsunterlage (id, schulung_id, name, description, r2_key, filename, content_type, size, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
  )
    .bind(id, schulungId, name, form.get("description") ? String(form.get("description")) : null, key, file.name, file.type || null, file.size, now, now)
    .run();
  return c.json({ id }, 201);
});

// ── Internal todo tracker ────────────────────────────────────────────
admin.get("/todos", async (c) => {
  const { results } = await c.env.DB.prepare("SELECT * FROM todo ORDER BY erledigt, updated_at DESC").all();
  return c.json({ items: results });
});

admin.post("/todos", async (c) => {
  const b = z
    .object({
      typ: z.enum(["Fehler", "Erweiterung"]),
      prioritaet: z.enum(["Niedrig", "Mittel", "Hoch"]).default("Niedrig"),
      name: z.string().min(1),
      beschreibung: z.string().default(""),
    })
    .parse(await c.req.json());
  const id = uuid();
  const now = nowIso();
  await c.env.DB.prepare(
    "INSERT INTO todo (id, typ, prioritaet, name, beschreibung, erledigt, created_at, updated_at) VALUES (?,?,?,?,?,0,?,?)",
  )
    .bind(id, b.typ, b.prioritaet, b.name, b.beschreibung, now, now)
    .run();
  return c.json({ id }, 201);
});

admin.patch("/todos/:id", async (c) => {
  const b = z
    .object({
      prioritaet: z.enum(["Niedrig", "Mittel", "Hoch"]).optional(),
      erledigt: z.boolean().optional(),
      beschreibung: z.string().optional(),
    })
    .parse(await c.req.json());
  const sets: string[] = [];
  const binds: unknown[] = [];
  for (const [k, v] of Object.entries(b)) {
    sets.push(`${k} = ?`);
    binds.push(typeof v === "boolean" ? (v ? 1 : 0) : v);
  }
  if (!sets.length) return c.json({ error: "Keine Felder" }, 400);
  await c.env.DB.prepare(`UPDATE todo SET ${sets.join(", ")}, updated_at = ? WHERE id = ?`)
    .bind(...binds, nowIso(), c.req.param("id"))
    .run();
  return c.json({ ok: true });
});
