---
name: fleet-ledger
description: The mandatory cost accounting for every bot run in the micro-SaaS fleet, plus Purser's fleet-wide spend control. Use this on EVERY completed job to produce the RUN LEDGER showing exact hard cash cost excluding already-paid subscriptions, and use it whenever anyone asks what something cost, what the fleet is spending, why spend jumped, which product is losing money, or to check a budget cap. Every bot must emit a ledger before reporting done.
---

# Fleet Ledger (Purser) — and the mandatory RUN LEDGER

## The rule every bot obeys
**No job reports "done" without a RUN LEDGER.** Firstmate refuses to relay a completed job that lacks one.

## Two ledgers, never mixed

**CASH** — real money a vendor bills *because this job ran*. This is what Affan asked for.
Counted: GitHub Actions minutes (private repos), Fly.io build + machine seconds + egress, R2 operations, external/paid API calls, Anthropic **API-key** spend (Batch jobs, CI headless on API billing), overflow agent credits (Codex, Copilot, Devin ACUs).
**Not counted:** Claude Max, CodeRabbit, GitHub Team, Cursor, or any other seat you pay monthly regardless. Those are sunk. Including them would inflate every job with money you already spent.

**SHADOW** — token value consumed inside a subscription. **$0 cash.** Priced at published API rates purely so a runaway loop is visible before it eats the plan. Never present shadow as cost; present it as burn.

## How a bot meters
Log the event *when it happens*, not from memory at the end:
```bash
export FLEET_JOB_ID=issue-42 FLEET_BOT=floor
python3 scripts/meter.py actions_run 18234567890
python3 scripts/meter.py fly_build 38
python3 scripts/meter.py fly_machine 120 --meta size=shared_cpu_1x_256mb
python3 scripts/meter.py api_call 2 --meta provider=serp_search
python3 scripts/meter.py anthropic_api 48000 --meta model=claude-sonnet-5 kind=in batch=1
```
Unmetered spend is a process failure. If you cannot meter something, log it as `manual` with a reason — visible and ugly, which is the point.

## How a bot closes out
```bash
python3 scripts/run_ledger.py $FLEET_JOB_ID --append-fleet
```
Paste the output verbatim into your handoff. Do not summarize it, round it, or retype it.

```
──────────────────────────────────────────────────────────────
 RUN LEDGER · issue-42 · 2026-09-18 11:04 UTC
──────────────────────────────────────────────────────────────
 CASH BILLED BY THIS RUN  (excludes subscriptions already paid)
   GitHub Actions     4.2 Ubuntu-min              $  0.0252
   Fly.io build       38 builder-s                $  0.0001
   External APIs      2 calls (serp_search)       $  0.0060
   -------------------------------------------------------
   TOTAL CASH                                     $  0.0313

 SUBSCRIPTION-COVERED  ($0 cash — burn tracking only)
   claude-sonnet-5    412k in / 18k out / 1.2M cache-read  ~$1.34 equiv
   claude-haiku-4-5    88k in /  3k out                    ~$0.10 equiv
   ~equivalent if metered                         $     1.44
──────────────────────────────────────────────────────────────
```

## Budget enforcement
Caps live in `scripts/rates.json` under `budgets` — the single source of truth. Never quote a price from memory; read the file.

| Trip | Action |
|---|---|
| Cash over **soft** cap | Report it and explain in one line why this job was expensive |
| Cash over **hard** cap | **Stop.** Do not continue. Escalate to Affan with the ledger |
| Shadow over hard cap | Almost always an agent loop. Halt, ledger, report. **Do not retry** |
| Fleet month cash cap | Purser trips the kill-switch: pause Factory Floor, notify, no new jobs |

The `token-budget.py` PostToolUse hook enforces the shadow cap mechanically — a bot cannot talk its way past it.

## Purser's standing jobs

**Weekly fleet read** from `.fleet/fleet-costs.csv`:
- cash + shadow per product, per bot, week over week
- cost per shipped PR — **if this is trending up, routing or caching is broken; say so loudly**
- idle infra: any product whose Fly/DB cost exceeds its MRR goes on the kill-list
- the three most expensive jobs, with a one-line cause each

**Quarterly:** re-verify every price in `rates.json` against vendor pricing pages. These change often, and a stale rate table quietly makes every ledger wrong. Propose the update as a PR — the rates file is CODEOWNERS-protected, so the human merge desk applies it.

## What Purser may not do
Change product code. Approve its own budget increase. Edit `rates.json` directly. Present shadow cost as cash — that inflates the fleet's apparent burn and leads to bad decisions.
