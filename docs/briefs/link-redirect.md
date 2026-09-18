# Brief: Short links actually redirect
Status: APPROVED 2026-09-18
Product: fleet-pilot
Problem: A signed-in user can create a short link today, but anyone who opens it just gets
the app shell — there is no server route that looks up the slug and sends the visitor to
the target URL (`src/server/index.ts` catch-all serves `index.html` for every path). The
product's one job, resolving a short link, does not work. Found while grilling
[link-expiry](link-expiry.md).
Smallest valuable version: an Express route for `GET /<slug>` that looks the slug up and
responds `302` with `Location: <url>`; an unknown or deleted slug gets a small
server-rendered "link not found" page with status `404`. Needs one new repo read
(`findBySlug`). `/` and static assets keep serving the app exactly as today.
Out of scope:
- Link expiry (parked — see link-expiry.md)
- Click counting, analytics, referrer logging
- Custom/vanity slugs, slug length changes
- `301` permanent redirects (rejected: browsers cache them, so deletes would never take effect)
- Rate limiting / abuse scanning of target URLs
- Branded or styled error pages beyond a minimal 404
Success metric: an integration test that fails on `main` today and passes after —
`GET /<slug of a created link>` → `302` with `Location` equal to its URL;
`GET /<unknown slug>` → `404`; `GET /<slug of a deleted link>` → `404`; `GET /` still
serves the app. In prod: a link created on the dashboard opens its target when pasted
into a fresh browser.
Surfaces touched: public API (new unauthenticated route). No schema, auth or billing change.
Flip impact: removes a blocker — a buyer would find the core feature missing. Adds no
dependency or ops burden.
Estimated gates risk: med — new unauthenticated public route. Notes for Factory Floor:
the route must sit after `express.static` and before the SPA catch-all, and only match
paths that look like a slug so asset paths are unaffected. In dev, Vite (port 5173) only
proxies `/api`, so redirects are exercised against Express on :3000 — the test should hit
the Express app, not the Vite dev server.
