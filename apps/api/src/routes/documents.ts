import { Hono } from "hono";
import { requireUser, type AuthVariables } from "../auth";

export const documents = new Hono<{ Bindings: Env; Variables: AuthVariables }>();

// List documents visible to the signed-in user: public (no allowed_funktionen)
// OR matching the user's funktion.
documents.get("/", requireUser, async (c) => {
  const funktionId = c.var.current.person?.funktion_id ?? null;
  const { results } = await c.env.DB.prepare(
    `SELECT d.id, d.name, d.description, d.filename, d.size, d.created_at
       FROM document d
      WHERE NOT EXISTS (SELECT 1 FROM document_funktion df WHERE df.document_id = d.id)
         OR EXISTS (SELECT 1 FROM document_funktion df WHERE df.document_id = d.id AND df.funktion_id = ?)
      ORDER BY d.name`,
  )
    .bind(funktionId)
    .all();
  return c.json({ items: results });
});

// Stream a document from R2 after re-checking access.
documents.get("/:id/download", requireUser, async (c) => {
  const id = c.req.param("id");
  const doc = await c.env.DB.prepare("SELECT r2_key, filename, content_type FROM document WHERE id = ?")
    .bind(id)
    .first<{ r2_key: string; filename: string; content_type: string | null }>();
  if (!doc) return c.json({ error: "Nicht gefunden" }, 404);

  const funktionId = c.var.current.person?.funktion_id ?? null;
  const allowed = await c.env.DB.prepare(
    `SELECT (NOT EXISTS (SELECT 1 FROM document_funktion WHERE document_id = ?))
          OR EXISTS (SELECT 1 FROM document_funktion WHERE document_id = ? AND funktion_id = ?) AS ok`,
  )
    .bind(id, id, funktionId)
    .first<{ ok: number }>();
  if (!allowed?.ok) return c.json({ error: "Kein Zugriff" }, 403);

  return streamR2(c.env.DOCUMENTS, doc.r2_key, doc.filename, doc.content_type);
});

// Course material — available to participants who completed the course.
documents.get("/unterlagen/:id/download", requireUser, async (c) => {
  const id = c.req.param("id");
  const mat = await c.env.DB.prepare(
    "SELECT r2_key, filename, content_type, schulung_id FROM schulungsunterlage WHERE id = ?",
  )
    .bind(id)
    .first<{ r2_key: string; filename: string; content_type: string | null; schulung_id: string }>();
  if (!mat) return c.json({ error: "Nicht gefunden" }, 404);

  const personId = c.var.current.person?.id;
  const ok = await c.env.DB.prepare(
    `SELECT COUNT(*) AS n FROM schulungsteilnehmer st
       JOIN schulungstermin t ON t.id = st.schulungstermin_id
      WHERE st.person_id = ? AND st.status = 'Teilgenommen' AND t.schulung_id = ?`,
  )
    .bind(personId, mat.schulung_id)
    .first<{ n: number }>();
  if (!c.var.current.user.is_staff && (ok?.n ?? 0) === 0) return c.json({ error: "Kein Zugriff" }, 403);

  return streamR2(c.env.DOCUMENTS, mat.r2_key, mat.filename, mat.content_type);
});

async function streamR2(bucket: R2Bucket, key: string, filename: string, contentType: string | null): Promise<Response> {
  const obj = await bucket.get(key);
  if (!obj) return new Response("Datei nicht gefunden", { status: 404 });
  const headers = new Headers();
  headers.set("Content-Type", contentType ?? obj.httpMetadata?.contentType ?? "application/octet-stream");
  headers.set("Content-Disposition", `attachment; filename="${encodeURIComponent(filename)}"`);
  return new Response(obj.body, { headers });
}
