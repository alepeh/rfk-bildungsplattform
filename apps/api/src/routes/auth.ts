import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { z } from "zod";
import { hashPassword, verifyPassword, signJwt, uuid, randomToken, sha256Hex } from "../crypto";
import { getCurrentContext, nowIso, type UserRow } from "../db";
import { requireUser, type AuthVariables } from "../auth";
import { sendMail, adminRegistrationNotice, activationEmail, passwordResetEmail } from "../email";

const RESET_TTL_MS = 60 * 60 * 1000; // 1 hour

export const auth = new Hono<{ Bindings: Env; Variables: AuthVariables }>();

const RegisterInput = z.object({
  vorname: z.string().min(1).max(150),
  nachname: z.string().min(1).max(150),
  email: z.string().email(),
  username: z.string().min(3).max(150),
  password: z.string().min(8).max(200),
  telefon: z.string().max(30).optional(),
  firmenname: z.string().max(200).optional(),
  firmenanschrift: z.string().max(200).optional(),
  adresse: z.string().max(200).optional(),
  plz: z.string().max(20).optional(),
  ort: z.string().max(100).optional(),
  funktion_id: z.string().optional(),
  organisation_id: z.string().optional(),
  dsv_akzeptiert: z.literal(true),
});

auth.post("/register", zValidator("json", RegisterInput), async (c) => {
  const b = c.req.valid("json");
  const db = c.env.DB;

  const dupe = await db
    .prepare("SELECT id FROM users WHERE username = ? OR email = ?")
    .bind(b.username, b.email)
    .first();
  if (dupe) return c.json({ error: "Benutzername oder E-Mail bereits vergeben" }, 409);

  const userId = uuid();
  const personId = uuid();
  const now = nowIso();
  const pw = await hashPassword(b.password);

  await db.batch([
    db
      .prepare(
        "INSERT INTO users (id, email, username, password_hash, is_active, created_at, updated_at) VALUES (?,?,?,?,0,?,?)",
      )
      .bind(userId, b.email, b.username, pw, now, now),
    db
      .prepare(
        `INSERT INTO person (id, user_id, vorname, nachname, email, telefon, firmenname, firmenanschrift,
            adresse, plz, ort, dsv_akzeptiert, funktion_id, organisation_id, is_activated,
            activation_requested_at, can_book_schulungen, created_at, updated_at)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,1,?,?,0,?,1,?,?)`,
      )
      .bind(
        personId, userId, b.vorname, b.nachname, b.email, b.telefon ?? null, b.firmenname ?? null,
        b.firmenanschrift ?? null, b.adresse ?? null, b.plz ?? null, b.ort ?? null,
        b.funktion_id ?? null, b.organisation_id ?? null, now, now, now,
      ),
  ]);

  const notice = adminRegistrationNotice(
    { name: `${b.vorname} ${b.nachname}`, email: b.email, username: b.username, dsv: true },
    c.env.APP_URL,
  );
  await sendMail(c.env, { to: c.env.ADMIN_EMAIL, ...notice });

  return c.json({ ok: true, message: "Registrierung erhalten. Ihr Konto wird freigeschaltet." }, 201);
});

const LoginInput = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
});

auth.post("/login", zValidator("json", LoginInput), async (c) => {
  const { username, password } = c.req.valid("json");
  const user = await c.env.DB.prepare("SELECT * FROM users WHERE username = ? OR email = ?")
    .bind(username, username)
    .first<UserRow>();
  if (!user || !(await verifyPassword(password, user.password_hash))) {
    return c.json({ error: "Benutzername oder Passwort ist falsch" }, 401);
  }
  const ctx = await getCurrentContext(c.env.DB, user.id);
  if (!user.is_active || !ctx?.person?.is_activated) {
    return c.json({ error: "Ihr Konto wurde noch nicht freigeschaltet." }, 403);
  }
  const token = await signJwt(
    { sub: user.id, username: user.username, is_staff: !!(user.is_staff || user.is_superuser) },
    c.env.JWT_SECRET,
  );
  return c.json({ token, user: shapeMe(ctx) });
});

auth.get("/me", requireUser, (c) => c.json(shapeMe(c.var.current)));

// Request a reset link. Always returns 200 to avoid leaking which emails exist.
const ForgotInput = z.object({ email: z.string().email() });

auth.post("/forgot-password", zValidator("json", ForgotInput), async (c) => {
  const { email } = c.req.valid("json");
  const user = await c.env.DB.prepare("SELECT id FROM users WHERE email = ?").bind(email).first<{ id: string }>();
  if (user) {
    const token = randomToken();
    const tokenHash = await sha256Hex(token);
    const expiresAt = new Date(Date.now() + RESET_TTL_MS).toISOString().replace(/\.\d{3}Z$/, "Z");
    await c.env.DB.batch([
      // Invalidate any prior unused tokens for this user.
      c.env.DB.prepare("UPDATE password_reset SET used_at = ? WHERE user_id = ? AND used_at IS NULL").bind(nowIso(), user.id),
      c.env.DB.prepare(
        "INSERT INTO password_reset (id, user_id, token_hash, expires_at) VALUES (?,?,?,?)",
      ).bind(uuid(), user.id, tokenHash, expiresAt),
    ]);
    await sendMail(c.env, { to: email, ...passwordResetEmail({ appUrl: c.env.APP_URL, token }) });
  }
  return c.json({ ok: true });
});

// Consume a reset token and set a new password.
const ResetInput = z.object({
  token: z.string().min(1),
  new_password: z.string().min(8).max(200),
});

auth.post("/reset-password", zValidator("json", ResetInput), async (c) => {
  const { token, new_password } = c.req.valid("json");
  const tokenHash = await sha256Hex(token);
  const row = await c.env.DB.prepare(
    "SELECT id, user_id, expires_at, used_at FROM password_reset WHERE token_hash = ?",
  )
    .bind(tokenHash)
    .first<{ id: string; user_id: string; expires_at: string; used_at: string | null }>();
  if (!row || row.used_at || new Date(row.expires_at).getTime() < Date.now()) {
    return c.json({ error: "Der Link ist ungültig oder abgelaufen. Bitte fordern Sie einen neuen an." }, 400);
  }
  const now = nowIso();
  await c.env.DB.batch([
    c.env.DB.prepare("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?").bind(
      await hashPassword(new_password),
      now,
      row.user_id,
    ),
    c.env.DB.prepare("UPDATE password_reset SET used_at = ? WHERE id = ?").bind(now, row.id),
  ]);
  return c.json({ ok: true });
});

const PasswordInput = z.object({
  current_password: z.string().min(1),
  new_password: z.string().min(8).max(200),
});

auth.post("/change-password", requireUser, zValidator("json", PasswordInput), async (c) => {
  const { current_password, new_password } = c.req.valid("json");
  const user = c.var.current.user;
  if (!(await verifyPassword(current_password, user.password_hash))) {
    return c.json({ error: "Aktuelles Passwort ist falsch" }, 400);
  }
  await c.env.DB.prepare("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?")
    .bind(await hashPassword(new_password), nowIso(), user.id)
    .run();
  return c.json({ ok: true });
});

// Shared shape returned to the SPA for the signed-in user.
function shapeMe(ctx: NonNullable<Awaited<ReturnType<typeof getCurrentContext>>>) {
  return {
    id: ctx.user.id,
    username: ctx.user.username,
    email: ctx.user.email,
    is_staff: !!(ctx.user.is_staff || ctx.user.is_superuser),
    person: ctx.person
      ? {
          id: ctx.person.id,
          vorname: ctx.person.vorname,
          nachname: ctx.person.nachname,
          email: ctx.person.email,
          funktion_id: ctx.person.funktion_id,
          organisation_id: ctx.person.organisation_id,
          betrieb_id: ctx.person.betrieb_id,
          can_book_schulungen: !!ctx.person.can_book_schulungen,
        }
      : null,
    betrieb: ctx.betrieb ? { id: ctx.betrieb.id, name: ctx.betrieb.name } : null,
    is_geschaeftsfuehrer: ctx.isGeschaeftsfuehrer,
  };
}

// Exported for admin route reuse (activation email).
export async function activateAndNotify(env: Env, userEmail: string): Promise<void> {
  const mail = activationEmail(env.APP_URL);
  await sendMail(env, { to: userEmail, ...mail });
}
