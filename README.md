# fleet-pilot

A deliberately minimal throwaway app: sign in, create a short link, list your own links, delete one.

Stack: React 19 · Vite · TypeScript · Tailwind · tRPC · Express · PostgreSQL · Drizzle · Better Auth.

## Boot from zero

Prerequisites: Node **22.11+**, pnpm **10** (`corepack enable` gives you the pinned version), and a PostgreSQL 14+ server you can reach.

```sh
git clone https://github.com/affanorangetoolz/fleet-pilot.git
cd fleet-pilot
pnpm install

cp .env.example .env
# edit .env: set DATABASE_URL, and set BETTER_AUTH_SECRET to the output of:
openssl rand -base64 32

createdb fleet_pilot        # or create the database any other way
pnpm db:migrate             # Better Auth tables, then the `links` table
pnpm dev                    # API on :3000, web on :5173
```

Open http://localhost:5173, choose **Create an account**, then add links.

## Scripts

| Script | What it does |
| --- | --- |
| `pnpm dev` | Express API (tsx watch, port 3000) + Vite dev server (port 5173, proxies `/api`) |
| `pnpm build` | Client to `dist/client`, server bundle to `dist/server/index.js` |
| `pnpm start` | Runs the production build; Express serves the client too. Set `BETTER_AUTH_URL=http://localhost:3000` first. |
| `pnpm db:migrate` | Creates Better Auth's tables, then `drizzle-kit push` for `links` |
| `pnpm test` | Vitest. No database needed; the data layer is an in-memory fake. |
| `pnpm lint` | ESLint |
| `pnpm typecheck` | `tsc --noEmit` |

## Layout

```
src/server/
  index.ts        Express: /api/auth/* (Better Auth), /api/trpc, static client
  router.ts       tRPC links.list / links.create / links.delete
  trpc.ts         context + protectedProcedure
  links-repo.ts   LinksRepo interface + Drizzle implementation
  auth.ts         Better Auth (email + password)
  db/schema.ts    the one Drizzle table: links
  db/migrate.ts   Better Auth table migration
src/client/       React UI, tRPC + Better Auth clients
```

Better Auth uses the `pg` pool directly and owns its tables (`user`, `session`, `account`, `verification`), so the Drizzle schema has only `links`.
