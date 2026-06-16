import { SELF } from "cloudflare:test";
import { expect, it, describe } from "vitest";

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
});
