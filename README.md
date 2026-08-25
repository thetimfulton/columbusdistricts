# Columbus Districts

An independent, nonpartisan civic reference site for the nine Columbus City Council
residential districts — who represents each district, how they compare, election history,
and a plain-language explainer of the 2026 council-structure ballot measure.

Built with **Astro** (static output), data augmented at build time from **CivicWorth**
(Supabase/PostGIS), hosted on **Cloudflare Pages**.

## Develop

```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # static site -> dist/
npm run preview    # serve the built site
```

## Architecture

- **Static Astro.** All nine district pages render from `src/data/districts/district-N.json`
  via `src/pages/districts/[district].astro`. Presentation follows the approved design system
  in `design-concepts/` (tokens in `src/styles/global.css`; type: Newsreader + Public Sans).
- **District data model.** Each district JSON carries a `demographics.snapshots[]` array with a
  `current_vintage` pointer (longitudinal ACS vintages — do not flatten it), plus
  `population2020`, `enrichment` (block groups, voting precincts), council member, neighborhoods,
  points of interest, area commissions, and `crimeRisk`.
- **Maps** are inline SVG rendered from `src/data/district-boundaries.json` (full-fidelity
  CivicWorth council boundaries on a shared viewBox), built once at build time.

## Build-time data sync

`scripts/sync_from_civicworth.py` pulls boundaries, member/population, enrichment counts, and
re-derives district demographics from ACS block groups against the real council polygons. Run it
as a **committed data refresh**, not at runtime. See [`scripts/README.md`](scripts/README.md) for
the method (it fixes the D2 population and D3 Asian bugs), env, and December cadence.

## Deploy — Cloudflare Pages

- **Build command:** `npm run build` · **Output directory:** `dist`
- `astro.config.mjs` is set for the domain root (`base: '/'`,
  `site: 'https://columbusdistricts.com'`). The old GitHub Pages workflow and `netlify.toml`
  have been removed.
- The `functions/` directory is deployed alongside the static assets as **Pages Functions**
  (the two form endpoints below). No Astro adapter is needed — the site is fully static.

### Environment variables

Set these in the Cloudflare Pages dashboard (Settings → Environment variables). See
[`.env.example`](.env.example) for the full list. `PUBLIC_*` vars are baked into the build;
the rest are read by the Pages Functions at runtime.

| Variable | Purpose |
|---|---|
| `PUBLIC_GA_MEASUREMENT_ID` | GA4 Measurement ID (`G-KEEV757MNS` — the existing property) |
| `PUBLIC_CF_BEACON_TOKEN` | Cloudflare Web Analytics beacon token |
| `PUBLIC_TURNSTILE_SITE_KEY` | Turnstile widget site key (public) |
| `TURNSTILE_SECRET_KEY` | Turnstile secret (server-side verification) |
| `FORMSPREE_FORM_ID` | Formspree form id submissions are delivered to |
| `FORMSPREE_SUGGEST_ID` / `FORMSPREE_NAME_ID` | Optional per-form Formspree ids (separate inboxes) |

## Forms

Two forms — **Suggest an edit** (every district page) and **Name the district** — post to
Cloudflare Pages Functions:

- `POST /api/suggest` → `functions/api/suggest.ts`
- `POST /api/name` → `functions/api/name.ts`

Each validates input, checks a **honeypot** field and (when configured) a **Turnstile** token,
delivers the submission via **Formspree** (which emails the monitored inbox and keeps a record),
and 303-redirects to the thank-you page. The forms post normally, so they work without client JS
(progressive enhancement); Turnstile is the only JS-dependent piece and is skipped when
unconfigured. Set the Formspree form's destination to `info@columbusdistricts.com` in the
Formspree dashboard.

## Analytics

- **GA4** loads site-wide from `Layout.astro` using `PUBLIC_GA_MEASUREMENT_ID`, tracking **every
  visitor** (`analytics_storage` granted); advertising signals stay off. GA4 does not store or
  expose raw IP addresses. Because GA sets analytics cookies, a brief cookie/privacy notice may be
  worth adding for compliance, but tracking is not gated on consent.
- **Cloudflare Web Analytics** (cookieless) loads when `PUBLIC_CF_BEACON_TOKEN` is set.
- **Civic events** are tracked via delegation in `Layout.astro`: `find_district_click`,
  `ballot_engagement`, `form_submit`, and `outbound_click` (to columbus.gov / Franklin County BOE /
  Ohio SoS). Verify pageviews + events in GA DebugView and confirm the Cloudflare beacon reports on
  staging **before** DNS cutover.

## Not affiliated

Columbus Districts is an independent, nonpartisan civic resource. It is not affiliated with the
City of Columbus, Columbus City Council, or any political campaign.
