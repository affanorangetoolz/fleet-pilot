---
name: ship-floor
description: Factory Floor's build-and-ship protocol for micro-SaaS fleet repos — launching the coding agent on an authorized issue, enforcing pstack discipline, clearing CodeRabbit, coverage-delta, mutation and CI gates, attaching the test artifact, and emitting the run cost ledger. Use whenever a job has been explicitly authorized to ship, when a PR needs its gates cleared, or when someone asks to implement an issue. Never use without explicit ship authorization.
---

# Ship Floor (Factory Floor)

## Preflight — refuse unless all four are true
1. There is a GitHub issue labelled `factory-job`.
2. The issue links an APPROVED brief.
3. Affan has said, literally, **"authorize ship #N"**. An approved brief is not authorization.
4. Live worktrees < `budgets.max_concurrent_worktrees`.

If any fail: stop, say which, and return to Firstmate. Do not start "just to get ahead."

## Isolation
One job = one git worktree = one branch = its own port, its own `.env`, its own scratch DB.
```bash
git worktree add ../wt-issue-<N> -b job/issue-<N>
export FLEET_JOB_ID=issue-<N> FLEET_BOT=floor
```
Parallel agents that share a port or a test Stripe account will corrupt each other's results and you will not notice until a customer does.

## pstack discipline — repeated on every ship, no exceptions
1. **Smallest logical change.** If the diff has two ideas in it, it is two PRs.
2. **Subtract before adding.** Look for code to delete first. A fleet you intend to sell is judged on how little there is to read.
3. **Blast radius only when the change crosses a boundary.** Don't map the universe for a copy tweak.
4. **Done means proof.** A test that fails before your change and passes after, or a rendered artifact. Never a vibes pass.

## Model routing (this is the money)
- **Haiku** — file search, reading, grep, test running, mechanical edits.
- **Sonnet** — default implementation.
- **Opus** — only multi-file architectural reasoning or a genuinely hard bug. Escalate deliberately, drop back down immediately after.

Escalating to Opus for a CRUD endpoint is how a $200 plan turns into a rate-limit wall by lunchtime.

## Gates — all must pass before you request review
- [ ] CodeRabbit threads **resolved**, not dismissed.
- [ ] `coverage-delta` on changed lines ≥ threshold.
- [ ] `mutation` — no surviving mutants on changed blocks.
- [ ] `typecheck` clean, no new `any`.
- [ ] CI green.
- [ ] **Test artifact link in the PR body.** No artifact = not done.
- [ ] Diff touches zero governance files. If the job genuinely needs one changed, stop and hand to Scribe.

## You may not
Merge. Edit AGENTS.md, CLAUDE.md, `.github/`, `.coderabbit.yaml`, `fly.toml`, CODEOWNERS, or `scripts/rates.json`. Deploy — that is Bosun. Exceed the per-job budget; the hook will stop you and that counts as a failure to plan.

## Close out
```bash
python3 scripts/run_ledger.py $FLEET_JOB_ID --append-fleet
git worktree remove ../wt-issue-<N>
```
Hand to Firstmate: PR link, gates status, artifact link, RUN LEDGER verbatim.
