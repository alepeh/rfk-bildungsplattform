// Password hashing (PBKDF2) and HS256 JWT — Web Crypto only, no Node polyfills.

const PBKDF2_ITERATIONS = 100_000;

function toB64url(bytes: Uint8Array): string {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromB64url(s: string): Uint8Array {
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/");
  const pad = b64.length % 4 === 0 ? "" : "=".repeat(4 - (b64.length % 4));
  return Uint8Array.from(atob(b64 + pad), (c) => c.charCodeAt(0));
}

// ── Passwords ────────────────────────────────────────────────────────
// Stored format: pbkdf2$<iterations>$<saltB64url>$<hashB64url>
export async function hashPassword(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const hash = await derive(password, salt, PBKDF2_ITERATIONS);
  return `pbkdf2$${PBKDF2_ITERATIONS}$${toB64url(salt)}$${toB64url(hash)}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const parts = stored.split("$");
  if (parts.length !== 4 || parts[0] !== "pbkdf2") return false;
  const iterations = Number(parts[1]);
  const salt = fromB64url(parts[2]);
  const expected = fromB64url(parts[3]);
  const actual = await derive(password, salt, iterations);
  return timingSafeEqual(actual, expected);
}

async function derive(password: string, salt: Uint8Array, iterations: number): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveBits"],
  );
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt, iterations, hash: "SHA-256" },
    key,
    256,
  );
  return new Uint8Array(bits);
}

function timingSafeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i]! ^ b[i]!;
  return diff === 0;
}

// ── JWT (HS256) ──────────────────────────────────────────────────────
export interface JwtPayload {
  sub: string; // user id
  username: string;
  is_staff: boolean;
  exp: number;
}

async function hmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
}

export async function signJwt(
  payload: Omit<JwtPayload, "exp">,
  secret: string,
  ttlSeconds = 60 * 60 * 24 * 7,
): Promise<string> {
  const header = { alg: "HS256", typ: "JWT" };
  const full: JwtPayload = { ...payload, exp: Math.floor(Date.now() / 1000) + ttlSeconds };
  const headerB64 = toB64url(new TextEncoder().encode(JSON.stringify(header)));
  const payloadB64 = toB64url(new TextEncoder().encode(JSON.stringify(full)));
  const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
  const sig = await crypto.subtle.sign("HMAC", await hmacKey(secret), data);
  return `${headerB64}.${payloadB64}.${toB64url(new Uint8Array(sig))}`;
}

export async function verifyJwt(token: string, secret: string): Promise<JwtPayload | null> {
  const [headerB64, payloadB64, sigB64] = token.split(".");
  if (!headerB64 || !payloadB64 || !sigB64) return null;
  const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
  const ok = await crypto.subtle.verify("HMAC", await hmacKey(secret), fromB64url(sigB64), data);
  if (!ok) return null;
  const payload = JSON.parse(new TextDecoder().decode(fromB64url(payloadB64))) as JwtPayload;
  if (payload.exp && Date.now() / 1000 > payload.exp) return null;
  return payload;
}

export function uuid(): string {
  return crypto.randomUUID();
}
