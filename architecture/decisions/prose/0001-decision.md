# Decision

Adopt the incunabula Cloudflare stack as the foundation for the rebuilt
Bildungsplattform, with a clear API/SPA split:

- **`apps/api`** — a TypeScript **Hono** Worker backed by **D1** (the primary
  relational store) and **R2** (document + course-material blobs). Auth is
  PBKDF2 password hashing plus HS256 JWTs, both via Web Crypto. Transactional
  email uses the native **Cloudflare Email Service** binding. The full legacy
  domain — people, businesses, courses, sessions, orders, participants,
  documents, the internal todo tracker — is reproduced table-for-table.

- **`apps/web`** — a **React 19 + Vite** SPA served from a Worker via the
  `assets` binding, talking to the API over HTTPS. The design is modernised
  around the brand (red/yellow/ink): a translucent sticky nav, hero, course
  cards with live seat availability, and a four-step checkout wizard.

- **Deploy tier T2**: GitHub Actions uploads a preview version on every branch
  push and deploys to production on `main`, applying D1 migrations first.

The legacy Django application is moved under `legacy/` unchanged, serving as the
authoritative behavioural reference during and after the migration. Nothing is
merged to `main` as part of this work — it lives on the rebuild feature branch.

## Alternatives considered

- **Incremental strangler migration** (keep Django, peel off endpoints): rejected —
  the platform is small enough that a clean rebuild is faster and leaves no
  hybrid infrastructure to operate.
- **Workers + Pages (separate Pages project)**: rejected in favour of Workers
  Static Assets, the current incunabula default (one `wrangler deploy` idiom).
