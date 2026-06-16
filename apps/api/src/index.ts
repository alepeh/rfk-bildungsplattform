import { OpenAPIHono } from "@hono/zod-openapi";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { HTTPException } from "hono/http-exception";

import { health } from "./routes/health";
import { auth } from "./routes/auth";
import { catalog } from "./routes/catalog";
import { orders } from "./routes/orders";
import { mitarbeiter } from "./routes/mitarbeiter";
import { documents } from "./routes/documents";
import { reference } from "./routes/reference";
import { admin } from "./routes/admin";

const app = new OpenAPIHono<{ Bindings: Env }>();

app.use("*", logger());
app.use(
  "*",
  cors({
    origin: (origin, c) => origin ?? c.env.APP_URL,
    credentials: true,
  }),
);

app.get("/version", (c) => c.json({ commit: c.env.GIT_COMMIT ?? "dev" }));

app.route("/health", health);
app.route("/auth", auth);
app.route("/termine", catalog);
app.route("/bestellungen", orders);
app.route("/mitarbeiter", mitarbeiter);
app.route("/documents", documents);
app.route("/ref", reference);
app.route("/admin", admin);

// Uniform JSON error envelope.
app.onError((err, c) => {
  if (err instanceof HTTPException) {
    return c.json({ error: err.message }, err.status);
  }
  console.error("Unhandled error", err);
  return c.json({ error: "Interner Serverfehler" }, 500);
});

app.doc("/openapi.json", {
  openapi: "3.1.0",
  info: { title: "bildung-api", version: "0.1.0" },
});

export default app;
