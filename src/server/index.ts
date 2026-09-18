import { fileURLToPath } from "node:url";
import path from "node:path";
import { createExpressMiddleware } from "@trpc/server/adapters/express";
import { fromNodeHeaders, toNodeHandler } from "better-auth/node";
import express from "express";
import { auth } from "./auth";
import { db } from "./db/client";
import { env } from "./env";
import { drizzleLinksRepo } from "./links-repo";
import { appRouter } from "./router";

const app = express();
const repo = drizzleLinksRepo(db);

// Better Auth must see the raw body, so it is mounted before any body parser.
app.all("/api/auth/{*path}", toNodeHandler(auth));

app.use(
  "/api/trpc",
  createExpressMiddleware({
    router: appRouter,
    createContext: async ({ req }) => {
      const session = await auth.api.getSession({ headers: fromNodeHeaders(req.headers) });
      return { userId: session?.user.id ?? null, repo };
    },
  }),
);

// In production, serve the built client. In dev, Vite serves it and proxies /api here.
const clientDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../client");
app.use(express.static(clientDir));
app.get("/{*path}", (_req, res) => res.sendFile(path.join(clientDir, "index.html")));

app.listen(env.PORT, () => {
  console.log(`API listening on http://localhost:${env.PORT}`);
});
