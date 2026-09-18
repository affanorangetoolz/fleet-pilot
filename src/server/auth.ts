import { betterAuth } from "better-auth";
import { pool } from "./db/client";
import { env } from "./env";

// Better Auth talks to Postgres through the pg Pool directly and owns its own
// tables, so the Drizzle schema stays limited to `links`.
export const auth = betterAuth({
  database: pool,
  secret: env.BETTER_AUTH_SECRET,
  baseURL: env.BETTER_AUTH_URL,
  emailAndPassword: { enabled: true },
});
