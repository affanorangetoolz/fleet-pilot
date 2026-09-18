// Creates Better Auth's tables. The `links` table is created by `drizzle-kit push`,
// which `pnpm db:migrate` runs right after this script.
import { getMigrations } from "better-auth/db/migration";
import { auth } from "../auth";
import { pool } from "./client";

const { runMigrations } = await getMigrations(auth.options);
await runMigrations();
await pool.end();
console.log("Better Auth tables are up to date.");
