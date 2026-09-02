# Columbus Districts — build context for Claude Code

This repo is the Astro rebuild of **columbusdistricts.com**, an independent civic reference
site for the nine Columbus City Council districts. It is a **sister project to CivicWorth** (parcel-resolved civic data),
which supplies boundaries and data.

**Start here:** read `columbusdistricts_implementation_brief.md` (the full plan and
file-by-file task list) and open `design-concepts/` (the approved visual system and page
mockups). This file is the quick orientation.

## Current state (important)
- The **live site is still the old WordPress build** — the Astro rebuild here was built in
  April 2026 and never launched.
- It was wired to deploy to a **GitHub Pages subpath**, which is why it never went live and
  why the forms don't work. See Deploy below for the corrected target.
- The design has been **redesigned** (Aug 2026). The old `.astro` templates predate the new
  look; rebuild them from `design-concepts/` rather than restyling in place.

## The plan (phases)
- **Phase A — Content/data integrity** (no external deps): fix the 8 wrong council emails,
  refresh members/committees vs. the official directory, and add the new **2026 ballot
  explainer** page.
- **Phase B — CivicWorth build-time sync**: a script pulls CivicWorth (Supabase) and writes
  `src/data/districts/*.json` (boundaries, members, population, enrichment) and **re-derives
  demographics from real council polygons** — which fixes the D2 population and D3 Asian bugs.
- **Phase C — Host + forms**: move to **Cloudflare Pages**, fix the base URL, wire the forms.
- **Phase D — QA + launch**: port anything the old WordPress site still has, then cut over DNS.

Phases A and C are the fall-window sprint (the ballot measure is on the Nov 2026 ballot);
B and D make it durable. Full detail in the brief.

## Design system
- **Source of truth:** `design-concepts/design-system.css` (design tokens + component styles).
  Split into `src/styles/global.css` (tokens, base, header/footer, buttons) and per-component
  styles as you build each Astro component.
- **Type:** `Newsreader` (editorial serif — display/headings) + `Public Sans` (UI/body), via
  Google Fonts (the only CSP-allowed font host — keep for the artifact concepts; self-host or
  link for production as you prefer).
- **Palette:** warm paper ground, deep "Scioto" slate blue `#233B54`, Columbus-scarlet accent
  `#C13B2A`. Full light + dark themes via the `:root` / `prefers-color-scheme` / `[data-theme]`
  token pattern already in the CSS — preserve it.
- **Concept → Astro page mapping:**
  - `design-concepts/district-one-concept.html` → `src/pages/districts/[district].astro`
  - `design-concepts/home.html` → `src/pages/index.astro`
  - `design-concepts/ballot.html` → new `src/pages/2026-ballot.astro` (or `/how-it-works/` sibling)
  - `design-concepts/all-districts.html` → `src/pages/all-districts.astro`
  - `design-concepts/data.html` → `src/pages/data.astro`
  - `design-concepts/how-it-works.html` → `src/pages/how-it-works.astro`
  - Elections, About, Area Commissions, Name-the-Districts reuse these patterns (article layout,
    tables, cards) — not separately mocked.
- The interactive map (home + district pages) renders CivicWorth boundary paths as inline SVG,
  hover shows the member, numbered labels at district centroids. Keep it a build-time static SVG.

## CivicWorth data (the augmentation)
- Supabase project id: `cohdnvvhmrqaupamhnly`. Table `public.boundaries`
  (`boundary_type` enum: `council_district`, `area_commission`, `neighborhood`,
  `census_block_group`, `voting_precinct`, `zoning_district`, `library`, `rec_center`, …).
- Columbus council districts: `external_id = 'columbus-cd-{1..9}'`; `properties` jsonb has
  `districtNumber`, `councilmember`, `population2020`; `geometry` is `MultiPolygon`, SRID 4326.
- **Map fidelity lesson:** the D1 boundary is 2,849 vertices (real jagged annexed city limits,
  verified against the official City ArcGIS map). Render with
  `ST_SimplifyPreserveTopology(geometry, 0.00012)` or finer — **never** ~0.0009, which
  straightens the edges (that was a bug we already caught).
- Demographics re-derivation: assign `census_block_group` rows to a district by
  `ST_Contains`/area-weight against the real council polygon, then aggregate — this replaces
  the hand-built spreadsheet crosswalk and fixes D2 (shows 143,899 ACS pop; true ≈ 100,572)
  and the D3 Asian count.

## Known data bugs to fix
- **Council emails:** 8 of 9 `contactEmail` values in `src/data/districts/*.json` are wrong
  (aide addresses copy-pasted). Use the generic `ColumbusCouncil@columbus.gov` or verify each
  against the official directory.
- **D2 population / D3 Asian:** fixed by the Phase B re-derivation (see above).
- **Crime:** `crimeRisk` blocks are `null`. Tim is supplying refreshed Applied Geographic
  Solutions numbers (currently on the old live site, expressed as % vs. citywide average).
  Populate per district; render as the below/above-city diverging bars in the district concept.
- `README.md` is the default Astro starter — replace.

## Analytics (must be live before launch)
The current WordPress site runs **Google Analytics** (via Site Kit). Carry the same GA4 property
forward so traffic history is continuous through the relaunch — especially the fall 2026 ballot
surge. Analytics is not optional here; it's the reason to get the cutover timing right.
- **Primary — GA4:** load `gtag.js` site-wide from `Layout.astro`, Measurement ID from an env var
  `PUBLIC_GA_MEASUREMENT_ID` (never hardcoded). **ID = `G-KEEV757MNS`** (the existing property, so
  history stays continuous).
- **Also — Cloudflare Web Analytics:** free, cookieless, privacy-first, native to the Cloudflare
  Pages host; add its beacon in `Layout.astro`. Needs no cookie banner.
- **Privacy:** it's a civic site — keep it privacy-respecting. Cloudflare's beacon is cookieless.
  For GA, enable IP anonymization + Consent Mode (default denied) or gate the GA cookie behind a
  lightweight consent notice. Confirm the approach with Tim.
- **Events, not just pageviews:** track the civic actions that show the site working — "Find your
  district" clicks, address lookups, ballot-explainer engagement, "Suggest an edit" / "Name the
  district" submissions, and outbound clicks to columbus.gov / Franklin County BOE / voter reg.
- **QA before cutover:** confirm pageviews + each event fire (GA DebugView) and the Cloudflare
  beacon reports, on staging, BEFORE DNS cutover. Do not launch without analytics verified live.

## Forms (shipped — Pages Functions → Formspree)
Two forms: **Suggest an edit** (on every district page) and **Name the district**. They are live
and wired as follows — keep this pipeline, don't rebuild it:
- Each form POSTs to a **Cloudflare Pages Function**: `functions/api/suggest.ts` (`/api/suggest`)
  and `functions/api/name.ts` (`/api/name`), sharing `functions/api/_lib.ts`.
- The Function validates, checks the honeypot (`company`) and the Turnstile token, then delivers
  via **Formspree** (`submitToFormspree()` in `_lib.ts`) and 303-redirects to the thank-you page.
  Formspree emails **info@columbusdistricts.com** (a Google Workspace mailbox) and keeps a record.
- **Runtime env vars** (Cloudflare Pages → Settings → Environment variables, Production):
  `FORMSPREE_SUGGEST_ID`, `FORMSPREE_NAME_ID` (per-form; `FORMSPREE_FORM_ID` is the shared
  fallback), `TURNSTILE_SECRET_KEY`; plus `PUBLIC_TURNSTILE_SITE_KEY` at build time.
  If no Formspree id is set, `_lib.ts` logs and drops the submission while still showing the
  thank-you page — so verify the vars after any project re-creation.
- **Where to see submissions:** formspree.io → Forms → "Columbus Districts – Suggest an Edit" /
  "Columbus Districts – Name the District" → Submissions (check the Spam tab too), and the info@
  inbox. There is no KV/D1 copy.
- **Spam protection:** honeypot field + Cloudflare Turnstile. A public civic form gets bots.
- Progressive enhancement: the form posts normally and shows the thank-you page; JS optional.

## Deploy
- Target **Cloudflare Pages** (matches CivicWorth's Cloudflare stack). Set `astro.config.mjs`
  `base: '/'` and `site` to the production domain; remove the GitHub Pages subpath config and
  the `.github/workflows/deploy.yml` GH-Pages workflow.
- **Forms** ("Suggest an edit", "Name the district"): Netlify Forms do NOT work here. Both run
  through Cloudflare Pages Functions → Formspree (see Forms above).
- Do not cut over DNS until Phase D QA passes; back up the old WordPress site first.

## Conventions
- All district content lives in `src/data/districts/district-N.json`; the demographics block
  uses a `snapshots` array + `current_vintage` pointer (do not flatten it — it's what powers
  the longitudinal Data page).
- Keep the site static (Astro → static HTML). The CivicWorth sync is build-time, not runtime.
- **No org attribution.** Do not attribute the site to The Confluence Cast or Columbus Underground
  anywhere — footer tagline, About column, body copy, or copyright. The site stands on its own as
  "Columbus Districts, an independent, nonpartisan civic resource." Copyright reads
  "© [year] Columbus Districts." (This was an explicit request — don't reintroduce these names.)
