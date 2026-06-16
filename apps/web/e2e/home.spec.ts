import { test, expect } from "@playwright/test";

test("home page renders the hero and nav", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: "Anmelden" })).toBeVisible();
});

test("can navigate to registration", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Registrieren" }).first().click();
  await expect(page.getByRole("heading", { name: "Konto erstellen" })).toBeVisible();
});
