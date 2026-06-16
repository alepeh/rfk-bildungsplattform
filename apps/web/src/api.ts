// Typed API client for the bildung-api Worker.
const API_BASE = import.meta.env.VITE_API_URL ?? "";

let token: string | null = localStorage.getItem("bildung_token");

export function setToken(t: string | null) {
  token = t;
  if (t) localStorage.setItem("bildung_token", t);
  else localStorage.removeItem("bildung_token");
}
export function getToken() {
  return token;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (res.status === 204) return undefined as T;
  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : await res.text();
  if (!res.ok) {
    const msg = isJson && data?.error ? data.error : `Fehler ${res.status}`;
    throw new ApiError(res.status, msg);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, form: FormData) => request<T>(path, { method: "POST", body: form }),
};

export function downloadUrl(path: string): string {
  // Token-bearing downloads use fetch + blob (see useDownload); this is the base.
  return `${API_BASE}${path}`;
}

export async function downloadFile(path: string, filename: string) {
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) throw new ApiError(res.status, "Download fehlgeschlagen");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Shared domain types ──────────────────────────────────────────────
export interface Me {
  id: string;
  username: string;
  email: string;
  is_staff: boolean;
  person: {
    id: string;
    vorname: string;
    nachname: string;
    email: string | null;
    funktion_id: string | null;
    organisation_id: string | null;
    betrieb_id: string | null;
    can_book_schulungen: boolean;
  } | null;
  betrieb: { id: string; name: string } | null;
  is_geschaeftsfuehrer: boolean;
}

export interface Termin {
  id: string;
  datum_von: string;
  datum_bis: string;
  dauer: string | null;
  buchbar: boolean;
  max_teilnehmer: number;
  freie_plaetze: number;
  schulung: {
    id: string;
    name: string;
    beschreibung: string;
    art: string | null;
    preis_standard_cents: number;
    preis_rabattiert_cents: number | null;
  };
  ort: { name: string; adresse: string | null; plz: string | null; ort: string | null } | null;
  funktionen: string[];
}

export interface BookingContext {
  freie_plaetze: number;
  einzelpreis_cents: number;
  is_business: boolean;
  can_book: boolean;
  betrieb_already_registered: boolean;
  related_persons: { id: string; name: string; funktion_id: string | null }[];
  rechnungsadresse: { name: string; strasse: string | null; plz: string | null; ort: string | null };
}
