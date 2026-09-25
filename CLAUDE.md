# Columbus Districts — build context for Claude Code

This repo is the source of **columbusdistricts.com**, an independent civic reference site for
the nine Columbus City Council districts. It is built with Astro and has been **live on
Cloudflare Pages since Aug. 24, 2026**, replacing the old WordPress site. It is a **sister
project to CivicWorth** (parcel-resolved civic data), which supplies boundaries and data.

**Start here:** this file is the quick orientation. `columbusdistricts_implementation_brief.md`
is the original build plan (now shipped), `design-concepts/` holds the approved visual system
and page mockups, and `LAUNCH.md` is the launch record plus the remaining open items.

## Current state (important)
- **This repo is what's live.** Cloudflare Pages (project `columbusdistricts`) builds from this
  GitHub repo: `main` deploys to production at columbusdistricts.com, and other branches get
  preview URLs at `<branch>.columbusdistricts.pages.dev`. Verified 2026-09-25: all 18 live pages
  match a local build of `main` @ `dffd3f1`. The only differences are the analytics and Turnstile
  scripts (the Pages build adds them from env vars) and two Cloudflare edge rewrites: email
  obfuscation of `mailto:` links, and an auto-injected second Web Analytics beacon.
- **Treat every merge to `main` as a production change**, especially on `/2026-ballot/`, which
  covers a live political topic.
- **Cutover happened 2026-08-24:** nameservers moved from AWS Route 53 to Cloudflare. The bare
  apex is canonical and `www` 301s to it via a Cloudflare Redirect Rule. The WordPress site is
  retired. `DNS-ROLLBACK.local.md` is a break-glass reference only; never act on it without
  Tim's explicit, written authorization.
- The Aug 2026 redesign is built: all templates were rebuilt from `design-concepts/`. Keep new
  pages consistent with that system.

## The plan (phases) — shipped
All four phases shipped with the Aug. 24, 2026 launch (full detail in the brief). Open items
are tracked in `LAUNCH.md`.
- **Phase A — Content/data integrity:** council emails fixed, and the **2026 ballot
  explainer** is live at `/2026-ballot/`.
- **Phase B — CivicWorth build-time sync:** `scripts/sync_from_civicworth.py` pulls CivicWorth
  (Supabase), writes `src/data/districts/*.json` (boundaries, members, population, enrichment)
  and **re-derives demographics from real council polygons**.
- **Phase C — Host + forms:** on Cloudflare Pages at the domain root; forms live (see Forms).
- **Phase D — QA + launch:** QA passed and DNS was cut over 2026-08-24.

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
  - `design-concepts/ballot.html` → `src/pages/2026-ballot.astro`
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

## Data fixes (resolved at launch)
- **Council emails:** all nine `contactEmail` values now use the generic
  `ColumbusCouncil@columbus.gov` (the old values were copy-pasted aide addresses).
- **D2 population / D3 Asian:** fixed by the Phase B re-derivation (see above).
- **Crime:** `crimeRisk` is populated for all nine districts from the prior site's Applied
  Geographic Solutions figures (% vs. citywide average), rendered as below/above-city diverging
  bars. Swap in refreshed AGS numbers when Tim supplies them.
- `README.md` has been rewritten for this project.

## Analytics (live)
The site uses the same GA4 property the old WordPress site used (via Site Kit), so traffic
history continues through the relaunch and the fall 2026 ballot surge.
- **GA4:** `gtag.js` loads site-wide from `Layout.astro`, with the Measurement ID taken from the
  env var `PUBLIC_GA_MEASUREMENT_ID` (never hardcoded). **ID = `G-KEEV757MNS`**.
- **Cloudflare Web Analytics:** a cookieless beacon in `Layout.astro` (`PUBLIC_CF_BEACON_TOKEN`).
- **Privacy: analytics default on (Tim's decision, 2026-09-25).** Consent Mode defaults
  `analytics_storage` to `'granted'`, while `ad_storage`, `ad_user_data` and `ad_personalization`
  stay `'denied'`. There is no consent banner. Don't switch GA to default-denied or add a
  cookie gate without asking Tim.
- **Events:** `find_district_click`, `ballot_engagement`, `form_submit` and `outbound_click`
  (fired from `Layout.astro`, `index.astro` and `districts/[district].astro`).
- **Verified 2026-09-25:** pageviews and all four events arrive in GA4 Realtime from production.
  Still open (`LAUNCH.md` §4): check the Cloudflare Web Analytics dashboard, and GA's enhanced
  measurement double-counts `form_submit` (and adds a generic `click` for outbound links) until
  "Form interactions" is turned off in the GA data stream settings.

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
- Hosted on **Cloudflare Pages** (matching CivicWorth's Cloudflare stack) and built from GitHub
  (`thetimfulton/columbusdistricts`): `main` deploys to production, and other branches get
  preview deploys. Build command `npm run build`, output `dist`. `astro.config.mjs` has
  `base: '/'` and `site: 'https://columbusdistricts.com'`.
- `PUBLIC_*` env vars are baked in at build time, so redeploy after changing one in the Pages
  dashboard. A local `npm run build` won't include the analytics or Turnstile scripts unless
  those vars are set locally.
- **Forms** ("Suggest an edit", "Name the district") run through Cloudflare Pages Functions →
  Formspree (see Forms above). Netlify Forms don't work here.
- DNS lives on Cloudflare. Don't change nameservers or DNS records. `DNS-ROLLBACK.local.md` is
  break-glass only.

## Conventions
- All district content lives in `src/data/districts/district-N.json`; the demographics block
  uses a `snapshots` array + `current_vintage` pointer (do not flatten it — it's what powers
  the longitudinal Data page).
- Keep the site static (Astro → static HTML). The CivicWorth sync is build-time, not runtime.
- **No org attribution.** Do not attribute the site to The Confluence Cast or Columbus Underground
  anywhere — footer tagline, About column, body copy, or copyright. The site stands on its own as
  "Columbus Districts, an independent, nonpartisan civic resource." Copyright reads
  "© [year] Columbus Districts." (This was an explicit request — don't reintroduce these names.)
