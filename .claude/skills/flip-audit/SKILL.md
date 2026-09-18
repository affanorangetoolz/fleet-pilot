---
name: flip-audit
description: Broker's exit-readiness audit for a micro-SaaS product being prepared for sale on Flippa, Acquire.com or a private deal — pre-empting buyer technical due diligence, producing the handover pack, and flagging what will cut the multiple. Use whenever a product is being listed, prepped to sell, valued, or when someone asks whether a product is clean enough to hand to a buyer, or asks what buyers will find.
---

# Flip Audit (Broker)

Buyers hire auditors. Assume everything you leave broken will be found, priced, and deducted.

## The findings that show up on day zero
Audit for these explicitly — they are the most common critical findings on AI-built SaaS bought from marketplaces:
- [ ] **Row-level / object-level authorization** — can user A fetch user B's records by changing an ID? Test every tRPC procedure that takes an ID.
- [ ] **Secrets in the frontend bundle or git history.** Scan the whole history, not just HEAD.
- [ ] **Known-CVE dependencies.** `pnpm audit`, fix or document.
- [ ] **Seller credential retention.** Every key the seller holds must be rotatable and listed. This is the finding buyers hate most.
- [ ] **Webhook signature verification** on Stripe and every inbound hook.
- [ ] **Rate limiting** on auth and any expensive endpoint.
- [ ] **Backups** — do they exist, and has a restore ever been tested?

## Owner-dependency audit (this is what moves the multiple)
- Can a competent stranger clone, `cp .env.example .env`, migrate, and boot? Time it. If it takes over an hour, fix it.
- Does the product depend on any shared internal package? **Vendor it in before sale.** A buyer must inherit zero dependency on your other ventures.
- One product = one repo + one database + one Fly app + one secret set. Any entanglement with another fleet product is deal friction and invites a holdback.
- Is there a runbook for every recurring operational task?
- Does anything route through Affan personally — a personal domain, a personal Stripe, a personal inbox?

## Valuation context (set expectations honestly)
Small SaaS trades on a profit multiple that rises sharply with size and falls with risk. Sub-$100K deals clear far lower multiples than $1M+ ones. Clean code has no published premium of its own — it moves the number by removing the buyer's perceived risk and key-person dependency. Churn reduction and owner-independence are the documented levers. Say this plainly rather than promising a multiple.

## Handover pack
```
/handover/
  README.md            boot from zero, tested, timed
  ARCHITECTURE.md      what talks to what
  RUNBOOKS/            every recurring op task
  CREDENTIALS.md       every key, where it lives, rotation steps (NO SECRETS IN FILE)
  METRICS.md           MRR, churn, cohorts, traffic sources, honest
  KNOWN-ISSUES.md      disclose everything; undisclosed findings kill deals
```

## Output
Report findings by severity with a fix estimate each, plus a verdict: **LIST NOW / FIX FIRST / NOT SALEABLE**. File issues only on Affan's explicit yes. Never sign off a product whose credentials have not been rotated.
