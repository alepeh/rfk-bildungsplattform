import { SELF, env } from "cloudflare:test";
import { expect, it, describe } from "vitest";
import { attendanceSheetPdf, certificatePdf } from "../src/pdf";
import { hashPassword, sha256Hex, uuid } from "../src/crypto";

function isPdf(bytes: Uint8Array): boolean {
  return bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46; // %PDF
}

describe("bildung-api", () => {
  it("GET /health returns ok", async () => {
    const res = await SELF.fetch("https://test/health");
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ status: "ok" });
  });

  it("GET /version reports a commit", async () => {
    const res = await SELF.fetch("https://test/version");
    expect(res.status).toBe(200);
    const body = (await res.json()) as { commit: string };
    expect(typeof body.commit).toBe("string");
  });

  it("protected routes reject anonymous requests", async () => {
    const res = await SELF.fetch("https://test/admin/personen");
    expect(res.status).toBe(401);
  });

  it("login rejects bad credentials", async () => {
    const res = await SELF.fetch("https://test/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "nobody", password: "wrong" }),
    });
    expect(res.status).toBe(401);
  });

  it("attendance-sheet PDF download requires staff", async () => {
    const res = await SELF.fetch("https://test/admin/schulungstermine/x/teilnehmer.pdf");
    expect(res.status).toBe(401);
  });
});

describe("password reset", () => {
  it("forgot-password returns 200 for an unknown email (no enumeration)", async () => {
    const res = await SELF.fetch("https://test/auth/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "nobody@example.com" }),
    });
    expect(res.status).toBe(200);
  });

  it("reset-password rejects an invalid token", async () => {
    const res = await SELF.fetch("https://test/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: "does-not-exist", new_password: "newpassword1" }),
    });
    expect(res.status).toBe(400);
  });

  it("resets the password and lets the user log in with it", async () => {
    const userId = uuid();
    const future = new Date(Date.now() + 600_000).toISOString().replace(/\.\d{3}Z$/, "Z");
    await env.DB.prepare(
      "INSERT INTO users (id, email, username, password_hash, is_active) VALUES (?,?,?,?,1)",
    )
      .bind(userId, "reset@example.com", "resetuser", await hashPassword("oldpassword1"), )
      .run();
    await env.DB.prepare(
      "INSERT INTO person (id, user_id, vorname, nachname, is_activated) VALUES (?,?,?,?,1)",
    )
      .bind(uuid(), userId, "Reset", "User")
      .run();
    await env.DB.prepare(
      "INSERT INTO password_reset (id, user_id, token_hash, expires_at) VALUES (?,?,?,?)",
    )
      .bind(uuid(), userId, await sha256Hex("valid-token"), future)
      .run();

    const reset = await SELF.fetch("https://test/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: "valid-token", new_password: "brandnew123" }),
    });
    expect(reset.status).toBe(200);

    // The token is now single-use.
    const reuse = await SELF.fetch("https://test/auth/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: "valid-token", new_password: "another123" }),
    });
    expect(reuse.status).toBe(400);

    const login = await SELF.fetch("https://test/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "resetuser", password: "brandnew123" }),
    });
    expect(login.status).toBe(200);
  });
});

describe("pdf", () => {
  it("renders a valid attendance sheet", async () => {
    const bytes = await attendanceSheetPdf({
      schulungName: "Test-Schulung",
      datum: "15. September 2026",
      ort: "WIFI Eisenstadt",
      rows: [
        { name: "Max Muster", betrieb: "Muster GmbH", email: "max@example.com", telefon: "123", dsv: true },
        { name: "Eva Probe", betrieb: "", email: "", telefon: "", dsv: false },
      ],
    });
    expect(isPdf(bytes)).toBe(true);
    expect(bytes.length).toBeGreaterThan(500);
  });

  it("renders a valid certificate", async () => {
    const bytes = await certificatePdf({
      participantName: "Max Muster",
      schulungName: "Sicherheitsunterweisung",
      datum: "15. September 2026",
      ort: "WIFI Eisenstadt",
      dauer: "1 Tag",
    });
    expect(isPdf(bytes)).toBe(true);
  });
});
