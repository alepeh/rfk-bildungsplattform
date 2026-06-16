# RFK Bildungsplattform

Bildungs- und Schulungsplattform der **Burgenländischen Rauchfangkehrer** — neu
aufgebaut auf dem Cloudflare-Stack (Workers · D1 · R2 · Email) nach den
[incunabula](https://github.com/alepeh/incunabula)-Konventionen.

> Die frühere Django-Anwendung liegt unverändert als funktionale Referenz unter
> [`legacy/`](legacy/). Dieser Rebuild lebt auf einem Feature-Branch; nichts wird
> nach `main` gemerged.

## Was die Plattform kann

- **Öffentlicher Schulungskatalog** mit Live-Platzverfügbarkeit und Detailseiten.
- **Vier-Schritt-Buchung** (Menge → Teilnehmer → Rechnung → Bestätigung) mit
  automatischer Bestellbestätigung per E-Mail.
- **Rollen**: Geschäftsführer buchen für ihren Betrieb und verwalten Mitarbeiter;
  Einzelpersonen/Partner buchen für sich oder externe Teilnehmer.
- **Preislogik**: vergünstigter Preis nur für Mitglieder einer Organisation mit
  Rabatt; Preise werden bei der Bestellung eingefroren.
- **Konto-Freischaltung** in zwei Stufen (Registrierung → Admin-Aktivierung).
- **Dokumente** nach Funktion gefiltert; **Schulungsunterlagen** für absolvierte Kurse.
- **Verwaltung**: Personen/Freischaltung, Schulungen & Termine, Teilnehmer mit
  Status, CSV-Export, Erinnerungs-Mails, Dokument-Upload und interner To-do-Tracker.

## Architektur

```
apps/
├── api/   bildung-api — Hono Worker · D1 (Datenbank) · R2 (Dateien) · Email
└── web/   bildung-web — React 19 + Vite SPA (Workers Static Assets)
architecture/   Domänenmodell, Guidelines, Rules, ADRs (typed YAML)
legacy/         Die alte Django-App (Referenz)
```

- **API** — TypeScript Hono auf `OpenAPIHono`; Auth via PBKDF2 + HS256-JWT (Web
  Crypto); Zod-validierte Eingaben; D1 mit TEXT-UUIDs, Cent-Beträgen und
  additiven Migrationen. Siehe [`architecture/guidelines.md`](architecture/guidelines.md).
- **Web** — React + react-router v7, eigenes Design-System in `src/styles.css`
  (Markenfarben Rot/Gelb/Anthrazit), API-Client mit Token-Persistenz.
- **Deploy-Tier T2** — GitHub Actions lädt Preview-Versionen je Branch hoch und
  deployt `main` nach Produktion (Migrationen zuerst).

## Lokale Entwicklung

Voraussetzungen: Node 22+.

```bash
make install        # Abhängigkeiten (npm workspaces)
make migrate seed   # lokale D1 anlegen + Beispieldaten
make dev            # API auf :45240, Web auf :45241
```

Admin-Login (nur lokal): **admin** / **admin12345**.

Weitere Targets: `make help`. Wichtige:

| Target | Zweck |
| --- | --- |
| `make typecheck` | Beide Apps typprüfen |
| `make test` | API-Unit-Tests (Vitest, Workers-Pool) |
| `make test-e2e` | Web-E2E (Playwright) |
| `make build` | Web-SPA bauen |
| `make reset-db` | Lokale D1 zurücksetzen + neu seeden |
| `make deploy` | Beide Apps nach Cloudflare deployen |

## Vor dem ersten Deploy

Einmalig die Cloudflare-Ressourcen anlegen und IDs eintragen:

```bash
cd apps/api
wrangler d1 create bildung-api-db          # UUID in wrangler.jsonc → database_id
wrangler r2 bucket create bildung-documents
wrangler secret put JWT_SECRET             # zufälliges Geheimnis
```

CI/CD-Secrets (Repo-Ebene): `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
Domains: `bildung.pehm.co.at` (Web) und `bildung-api.pehm.co.at` (API) werden beim
ersten Deploy automatisch angelegt.

## Tests

- `apps/api/tests/` — Worker-native Vitest gegen ein migriertes lokales D1.
- `apps/web/e2e/` — Playwright-Smoke-Tests gegen die gebaute SPA.

---

*Für Umwelt und Leben — WTG Burgenland.*
