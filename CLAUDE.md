# fleet-pilot — Agent Operating Rules

Stack (LOCKED — never propose alternatives):
React 19 + Vite + TypeScript + Tailwind + tRPC + Express + PostgreSQL + Drizzle
+ BullMQ + Redis + Better Auth + Cloudflare R2 + Fly.io

NEVER use: Next.js for apps, GraphQL, Redux, MongoDB, Firebase, AWS.

## pstack — every change
1. Smallest logical change. Two ideas in one diff = two PRs.
2. Subtract code before adding.
3. Map blast radius only when the change crosses a module boundary.
4. "Done" = a test that failed before and passes after, linked as an artifact. Never a vibes pass.

## Hard rules
- You may NOT edit: AGENTS.md, CLAUDE.md, CODEOWNERS, .coderabbit.yaml, fly.toml,
  .github/**, .claude/**, hooks/**, scripts/rates.json. Propose; the human merge desk applies.
- One product = one DB + one Redis namespace + one Fly app + one secret set.
  Never reference another fleet product. This product will be sold separately.
- Every PR links its brief (/docs/briefs/<slug>.md) and a test artifact.
- Meter every billable action (scripts/meter.py). Emit a RUN LEDGER before reporting done.
- Model routing: Haiku for search/mechanical, Sonnet default, Opus only for hard
  multi-file reasoning — then drop back down.

## Commands
install: pnpm i · dev: pnpm dev · test: pnpm test
typecheck: pnpm typecheck · lint: pnpm lint · migrate: pnpm db:migrate
