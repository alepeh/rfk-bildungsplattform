import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { uuid } from "../crypto";
import { nowIso } from "../db";
import { requireUser, type AuthVariables } from "../auth";

export const mitarbeiter = new Hono<{ Bindings: Env; Variables: AuthVariables }>();

// Only the Geschäftsführer of a Betrieb manages employees.
mitarbeiter.use("*", requireUser, async (c, next) => {
  if (!c.var.current.isGeschaeftsfuehrer || !c.var.current.betrieb) {
    return c.json({ error: "Nur Geschäftsführer können Mitarbeiter verwalten" }, 403);
  }
  await next();
});

mitarbeiter.get("/", async (c) => {
  const betriebId = c.var.current.betrieb!.id;
  const gfId = c.var.current.person!.id;
  const { results } = await c.env.DB.prepare(
    `SELECT p.id, p.vorname, p.nachname, p.email, p.telefon, p.funktion_id, f.name AS funktion_name,
            (p.user_id IS NOT NULL) AS has_login
       FROM person p LEFT JOIN funktion f ON f.id = p.funktion_id
      WHERE p.betrieb_id = ? ORDER BY p.nachname, p.vorname`,
  )
    .bind(betriebId)
    .all();
  return c.json({ items: results, geschaeftsfuehrer_id: gfId });
});

const EmployeeInput = z.object({
  vorname: z.string().min(1).max(150),
  nachname: z.string().min(1).max(150),
  email: z.string().email().nullable().optional(),
  telefon: z.string().max(30).nullable().optional(),
  funktion_id: z.string().nullable().optional(),
});

mitarbeiter.post("/", zValidator("json", EmployeeInput), async (c) => {
  const b = c.req.valid("json");
  const id = uuid();
  const now = nowIso();
  await c.env.DB.prepare(
    `INSERT INTO person (id, vorname, nachname, email, telefon, funktion_id, betrieb_id,
        is_activated, can_book_schulungen, created_at, updated_at)
     VALUES (?,?,?,?,?,?,?,0,1,?,?)`,
  )
    .bind(id, b.vorname, b.nachname, b.email ?? null, b.telefon ?? null, b.funktion_id ?? null, c.var.current.betrieb!.id, now, now)
    .run();
  return c.json({ id }, 201);
});

mitarbeiter.put("/:id", zValidator("json", EmployeeInput), async (c) => {
  const b = c.req.valid("json");
  const id = c.req.param("id");
  const owned = await c.env.DB.prepare("SELECT id, betrieb_id FROM person WHERE id = ?")
    .bind(id)
    .first<{ id: string; betrieb_id: string | null }>();
  if (!owned || owned.betrieb_id !== c.var.current.betrieb!.id) {
    return c.json({ error: "Nicht gefunden" }, 404);
  }
  await c.env.DB.prepare(
    "UPDATE person SET vorname=?, nachname=?, email=?, telefon=?, funktion_id=?, updated_at=? WHERE id=?",
  )
    .bind(b.vorname, b.nachname, b.email ?? null, b.telefon ?? null, b.funktion_id ?? null, nowIso(), id)
    .run();
  return c.json({ ok: true });
});

mitarbeiter.delete("/:id", async (c) => {
  const id = c.req.param("id");
  // Never delete the Geschäftsführer; only employees without enrolments.
  if (id === c.var.current.person!.id) return c.json({ error: "Geschäftsführer kann nicht entfernt werden" }, 400);
  const owned = await c.env.DB.prepare("SELECT id, betrieb_id FROM person WHERE id = ?")
    .bind(id)
    .first<{ betrieb_id: string | null }>();
  if (!owned || owned.betrieb_id !== c.var.current.betrieb!.id) return c.json({ error: "Nicht gefunden" }, 404);
  const enrol = await c.env.DB.prepare(
    "SELECT COUNT(*) AS n FROM schulungsteilnehmer WHERE person_id = ?",
  )
    .bind(id)
    .first<{ n: number }>();
  if ((enrol?.n ?? 0) > 0) return c.json({ error: "Mitarbeiter hat Anmeldungen und kann nicht entfernt werden" }, 409);
  await c.env.DB.prepare("DELETE FROM person WHERE id = ?").bind(id).run();
  return c.json({ ok: true });
});
