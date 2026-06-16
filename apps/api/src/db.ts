// Typed D1 access helpers. Referential integrity is enforced here (D1 has no
// FK constraints). Row shapes mirror migrations/0001_init.sql.

export interface UserRow {
  id: string;
  email: string;
  username: string;
  password_hash: string;
  is_active: number;
  is_staff: number;
  is_superuser: number;
  created_at: string;
  updated_at: string;
}

export interface PersonRow {
  id: string;
  user_id: string | null;
  vorname: string;
  nachname: string;
  email: string | null;
  telefon: string | null;
  firmenname: string | null;
  firmenanschrift: string | null;
  adresse: string | null;
  plz: string | null;
  ort: string | null;
  dsv_akzeptiert: number;
  funktion_id: string | null;
  organisation_id: string | null;
  betrieb_id: string | null;
  is_activated: number;
  activation_requested_at: string | null;
  activated_at: string | null;
  activated_by_id: string | null;
  can_book_schulungen: number;
  created_at: string;
  updated_at: string;
}

export interface BetriebRow {
  id: string;
  name: string;
  kehrgebiet: string | null;
  adresse: string | null;
  plz: string | null;
  ort: string | null;
  telefon: string | null;
  email: string | null;
  geschaeftsfuehrer_id: string | null;
}

export interface CurrentUser {
  user: UserRow;
  person: PersonRow | null;
  betrieb: BetriebRow | null;
  isGeschaeftsfuehrer: boolean;
}

export async function getCurrentContext(db: D1Database, userId: string): Promise<CurrentUser | null> {
  const user = await db.prepare("SELECT * FROM users WHERE id = ?").bind(userId).first<UserRow>();
  if (!user) return null;
  const person = await db
    .prepare("SELECT * FROM person WHERE user_id = ?")
    .bind(userId)
    .first<PersonRow>();
  let betrieb: BetriebRow | null = null;
  let isGeschaeftsfuehrer = false;
  if (person?.betrieb_id) {
    betrieb = await db
      .prepare("SELECT * FROM betrieb WHERE id = ?")
      .bind(person.betrieb_id)
      .first<BetriebRow>();
    isGeschaeftsfuehrer = betrieb?.geschaeftsfuehrer_id === person.id;
  }
  return { user, person, betrieb, isGeschaeftsfuehrer };
}

// Free seats for a session (can be negative — matches legacy semantics).
export async function freiePlaetze(db: D1Database, terminId: string, max: number): Promise<number> {
  const row = await db
    .prepare("SELECT COUNT(*) AS n FROM schulungsteilnehmer WHERE schulungstermin_id = ?")
    .bind(terminId)
    .first<{ n: number }>();
  return max - (row?.n ?? 0);
}

// Distinct Betriebe already registered on a session (via linked Persons).
export async function registrierteBetriebe(db: D1Database, terminId: string): Promise<Set<string>> {
  const { results } = await db
    .prepare(
      `SELECT DISTINCT p.betrieb_id AS betrieb_id
         FROM schulungsteilnehmer st
         JOIN person p ON p.id = st.person_id
        WHERE st.schulungstermin_id = ? AND p.betrieb_id IS NOT NULL`,
    )
    .bind(terminId)
    .all<{ betrieb_id: string }>();
  return new Set(results.map((r) => r.betrieb_id));
}

// Pricing: discounted price applies only when the buyer's Person belongs to an
// Organisation with preisrabatt=1. Returns cents. (Faithful to legacy logic.)
export async function unitPriceCents(db: D1Database, person: PersonRow | null, schulungId: string): Promise<number> {
  const s = await db
    .prepare("SELECT preis_standard, preis_rabattiert FROM schulung WHERE id = ?")
    .bind(schulungId)
    .first<{ preis_standard: number; preis_rabattiert: number | null }>();
  if (!s) return 0;
  let discounted = false;
  if (person?.organisation_id) {
    const org = await db
      .prepare("SELECT preisrabatt FROM organisation WHERE id = ?")
      .bind(person.organisation_id)
      .first<{ preisrabatt: number }>();
    discounted = !!org?.preisrabatt;
  }
  return (discounted ? s.preis_rabattiert ?? 0 : s.preis_standard) ?? 0;
}

// Funktion IDs visible to a person (for document access). Empty allowed-set
// documents are public; this returns the person's funktion for matching.
export function nowIso(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
}
