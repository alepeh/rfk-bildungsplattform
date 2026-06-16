import { defineConfig } from "@playwright/test";

// Preview port = hash-derived base+2 for project "bildung".
export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://localhost:45242" },
  webServer: {
    command: "npx vite preview --port 45242",
    port: 45242,
    reuseExistingServer: !process.env.CI,
  },
});
