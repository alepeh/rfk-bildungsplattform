import { Hono } from "hono";

// Public read-only reference data used by registration and admin forms.
export const reference = new Hono<{ Bindings: Env }>();

reference.get("/funktionen", async (c) => {
  const { results } = await c.env.DB.prepare(
    "SELECT id, name, sortierung FROM funktion ORDER BY sortierung, name",
  ).all();
  return c.json({ items: results });
});

reference.get("/organisationen", async (c) => {
  const { results } = await c.env.DB.prepare(
    "SELECT id, name, preisrabatt FROM organisation ORDER BY name",
  ).all();
  return c.json({ items: results });
});

reference.get("/schulungsorte", async (c) => {
  const { results } = await c.env.DB.prepare(
    "SELECT id, name, adresse, plz, ort FROM schulungsort ORDER BY name",
  ).all();
  return c.json({ items: results });
});

reference.get("/schulungsarten", async (c) => {
  const { results } = await c.env.DB.prepare("SELECT id, name FROM schulungsart ORDER BY name").all();
  return c.json({ items: results });
});
