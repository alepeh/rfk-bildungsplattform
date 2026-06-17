import { SELF } from "cloudflare:test";
import { expect, it, describe } from "vitest";
import { attendanceSheetPdf, certificatePdf } from "../src/pdf";

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
