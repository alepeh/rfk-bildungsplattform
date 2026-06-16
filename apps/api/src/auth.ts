// Auth middleware. Resolves the JWT into the current user + their Person and
// derived role flags, which routes read from c.var.

import { createMiddleware } from "hono/factory";
import { HTTPException } from "hono/http-exception";
import { verifyJwt } from "./crypto";
import { getCurrentContext, type CurrentUser } from "./db";

export type AuthVariables = { current: CurrentUser };

// Requires a valid token AND an activated account (mirrors the legacy
// @login_and_activation_required decorator).
export const requireUser = createMiddleware<{ Bindings: Env; Variables: AuthVariables }>(
  async (c, next) => {
    const current = await resolve(c.req.header("Authorization"), c.env);
    if (!current) throw new HTTPException(401, { message: "Nicht angemeldet" });
    if (!current.user.is_active || !current.person?.is_activated) {
      throw new HTTPException(403, { message: "Konto noch nicht aktiviert" });
    }
    c.set("current", current);
    await next();
  },
);

// Requires staff/superuser.
export const requireStaff = createMiddleware<{ Bindings: Env; Variables: AuthVariables }>(
  async (c, next) => {
    const current = await resolve(c.req.header("Authorization"), c.env);
    if (!current) throw new HTTPException(401, { message: "Nicht angemeldet" });
    if (!current.user.is_staff && !current.user.is_superuser) {
      throw new HTTPException(403, { message: "Keine Berechtigung" });
    }
    c.set("current", current);
    await next();
  },
);

async function resolve(authHeader: string | undefined, env: Env): Promise<CurrentUser | null> {
  if (!authHeader?.startsWith("Bearer ")) return null;
  const payload = await verifyJwt(authHeader.slice(7), env.JWT_SECRET);
  if (!payload) return null;
  return getCurrentContext(env.DB, payload.sub);
}
