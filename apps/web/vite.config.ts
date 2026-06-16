import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Port = hash-derived base+1 for project "bildung" (see Makefile).
// API base comes from VITE_API_URL (.env.development / .env.production).
export default defineConfig({
  plugins: [react()],
  server: { port: 45241 },
});
