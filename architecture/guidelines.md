# Engineering guidelines — bildung

Conventions for the Cloudflare-stack rebuild of the RFK Bildungsplattform.

## Language & naming

- **Domain vocabulary stays German** (Schulung, Betrieb, Funktion, …). Auth/infra
  terms stay English (users, token, migration).
- Files: `snake_case.sql`, `kebab-case` routes, `PascalCase` React components and
  Zod schemas, `camelCase` functions/vars.
- SQL tables/columns: `snake_case`, singular table names (`person`, `bestellung`).

## D1 / persistence

- TEXT UUID primary keys (R-001). ISO-8601 UTC TEXT timestamps. Enums as TEXT + CHECK.
- **No foreign-key constraints** (R-002) — relationships are indexed columns; integrity is
  enforced in `apps/api/src/db.ts` and handlers.
- Money in integer cents (R-003).
- Migrations are sequential `NNNN_*.sql` and **always additive**. A breaking change
  needs a new migration + an ADR.

## API (apps/api)

- Hono on `OpenAPIHono`; `/openapi.json` and `/version` always exposed.
- Request bodies validated with Zod (`@hono/zod-validator`). Generic admin CRUD writes
  only allowlisted columns — never interpolate caller-supplied column names.
- Auth: `requireUser` (activated account) and `requireStaff` middleware set `c.var.current`.
- Errors return `{ error: string }` with an appropriate status; `app.onError` is the catch-all.
- Email via `env.EMAIL.send()`; failures are logged, never fatal to the request.

## Web (apps/web)

- React 19 + react-router v7 (`from "react-router"`). API base from `VITE_API_URL`.
- One file per route under `src/routes/`; admin under `src/routes/admin/`.
- Data via `useResource` (unmount-safe). Money via `eur()`, dates via `lib.ts` helpers.
- Styling: the design tokens + component classes in `src/styles.css` only. No CSS framework.
- Token persisted in `localStorage`; re-validated against `/auth/me` on load.

## What NOT to do

- Don't add `nodejs_compat` or `@cloudflare/workers-types` (use generated types).
- Don't call one Worker from another over HTTP — use a service binding.
- Don't recompute order prices after purchase (I-005).
- Don't bypass the activation gate or the duplicate-enrolment check.
