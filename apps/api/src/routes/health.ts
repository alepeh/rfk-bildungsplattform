import { Hono } from "hono";

export const health = new Hono<{ Bindings: Env }>();

health.get("/", (c) => c.json({ status: "ok" }));
