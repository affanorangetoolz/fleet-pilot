# Brief: Link expiry
Status: PARKED 2026-09-18 — no user demand. Reopen when a named user asks for time-limited links.
Product: fleet-pilot
Problem: Owners sometimes share links that should only work for a while (a promo, an
event, a one-off file). Today a link lives until the owner deletes it by hand. Nobody has
asked for this yet — it is Affan's own hunch, not a reported pain — so per the kill
criteria it is parked rather than built.
Prerequisite: [link-redirect](link-redirect.md). Expiry has no visible effect until short
links actually redirect.

## Decisions already made (grilled 2026-09-18)
- Why: **temporary sharing** — the owner decides per link. Rejected: one fixed lifetime for
  all links, cleanup/slug reuse, paid-plan lever.
- Who: **nobody yet** → parked.
- Lifetime UI: **one preset dropdown at creation — Never / 1 hour / 1 day / 7 days / 30 days,
  default Never.** Set once at creation. Rejected: custom date picker, date-only picker.

## Leaning, not yet confirmed (confirm when reopened)
- Visitor on an expired link: `410 Gone` using the same minimal page as the redirect
  brief's 404.
- Expired rows: kept and labelled "Expired" in the owner's list; checked at redirect time.
  No scheduled sweep, so no Redis/BullMQ (not in this app today).
- Existing links: `expiresAt = NULL` (never expire).
- Renewal: none in v1; recreate the link.

## Shape if reopened
Smallest valuable version: nullable `expires_at` column on `links`; preset dropdown on
the create form; redirect route returns 410 when `expires_at <= now()`; list shows an
"Expired" label.
Out of scope: click-count caps, custom dates, renewal/revival, scheduled deletion,
per-plan limits.
Success metric: TBD with the user who asks — e.g. share of new links created with a
non-Never lifetime. Acceptance test: a link whose `expires_at` is in the past returns 410.
Surfaces touched: schema (new column + migration), create-link UI, redirect route.
Flip impact: neutral if the lazy check is kept; negative if a Redis sweep is added.
Estimated gates risk: med — schema change.
