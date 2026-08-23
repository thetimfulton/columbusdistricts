# Columbus Districts — Implementation Brief

*Prepared in Cowork, August 2026, for the Claude Code build. Companion to `CLAUDE.md` and the
`design-concepts/` folder. This is the "what to build" list; `CLAUDE.md` is the orientation.*

## Goal

Take the approved design system and page concepts in `design-concepts/` and implement them as
the live Astro site, wire in CivicWorth data at build time, fix the known data bugs, move
hosting to Cloudflare Pages, and launch on `columbusdistricts.com` — in time for the fall 2026
council-structure ballot traffic.

Keep the existing architecture (Astro static, one template for the nine district pages, JSON
data files, the demographics `snapshots` schema). Rebuild the *presentation* from the concepts;
don't scrap the data model.

---

## Phase A — Content & data integrity

1. **Rebuild `src/styles/global.css`** from `design-concepts/design-system.css` (tokens, base,
   header, footer, buttons, theme system). Add the Google Fonts link (Newsreader + Public Sans).
2. **Rebuild the shared `Layout.astro`** (sticky header w/ nav + theme toggle, the "2026 ballot"
   ribbon, footer) to match the concepts.
3. **Fix `src/data/districts/*.json`:**
   - Replace the 8 wrong `contactEmail` values (currently aide addresses) with
     `ColumbusCouncil@columbus.gov` or directory-verified addresses.
   - Re-verify each `councilMember` name/committees vs. the official directory.
4. **Build the district page** (`src/pages/districts/[district].astro`) from
   `design-concepts/district-one-concept.html`: hero + inline SVG district map, civic-snapshot
   strip, council card, neighborhoods, POI, area commissions, demographics (change chips +
   "Compared to Columbus" rank/position strips + race bars w/ citywide ticks), **Public Safety**
   (crime vs-city diverging bars), Get Involved, Suggest an Edit.
5. **Build the 2026 ballot explainer** (`src/pages/2026-ballot.astro`) from
   `design-concepts/ballot.html`. Copy is drafted but **must be verified against the certified
   ballot language** before launch — it's a live political topic; keep it nonpartisan and dated.

## Phase B — CivicWorth build-time sync

Create `scripts/sync_from_civicworth.(ts|py)` that connects to the CivicWorth Supabase
(`cohdnvvhmrqaupamhnly`, session-pooler connection string in env) and writes into the district
JSON files:

- **Boundaries** → inline SVG path per district for the maps. Use
  `ST_AsGeoJSON(ST_SimplifyPreserveTopology(geometry, 0.00012))` (or finer). Project with a
  shared bbox so all nine align on one viewBox. (A reference implementation of this projection
  is in `design-concepts/` provenance — the concept maps were generated this way.)
- **Member + population** from `boundaries.properties` (`councilmember`, `population2020`).
- **Enrichment counts** (optional, for the civic-snapshot strip): block groups, voting
  precincts, libraries, rec centers via spatial predicates against the district polygon.
- **Demographics re-derivation** (the important fix): assign `census_block_group` rows to each
  district by `ST_Contains`/area-weight against the real council polygon and aggregate. This
  produces correct district totals and **fixes D2 (currently 143,899; true ≈ 100,572) and the
  D3 Asian count**, replacing the hand-built `CensusBlock2020_with_CouncilDistrict2023.xlsx`
  crosswalk. Preserve the `snapshots` structure (append vintages; keep `current_vintage`).

Run it as a build step / committed data refresh, not at runtime. Document env + cadence in
`scripts/README.md`.

## Phase B′ — Remaining pages (in-system)

- `index.astro` ← `home.html` (interactive nine-district map hero, district grid, ballot band).
- `all-districts.astro` ← `all-districts.html` (scrollable comparison table + Columbus row +
  superlatives; use 2020 population to avoid the ACS D2 artifact).
- `data.astro` ← `data.html` (dumbbell trend charts + change table + methodology).
- `how-it-works.astro` ← `how-it-works.html`.
- Elections / About / Area Commissions / Name-the-Districts: rebuild in-system from the shared
  components (article layout, tables, cards) — no separate mock needed.

## Phase C — Host & forms

- `astro.config.mjs`: `base: '/'`, `site: 'https://www.columbusdistricts.com'`. Remove the
  GitHub Pages subpath config and `.github/workflows/deploy.yml`.
- Deploy to **Cloudflare Pages**.
- **Wire the forms (they don't work yet).** Both "Suggest an Edit" and "Name the District" are
  static stubs. Add a Cloudflare Pages Function per form that validates and delivers to a monitored
  inbox (via MailChannels/Resend) — or a hosted form service if preferred — plus honeypot +
  Turnstile spam protection. See the Forms section in `CLAUDE.md`. Submissions email to
  `info@columbusdistricts.com` (confirmed). Netlify Forms will not work on this host.
- **Wire analytics (see the Analytics section in `CLAUDE.md`).** GA4 via env-var'd Measurement ID
  in `Layout.astro` + Cloudflare Web Analytics beacon, with the key civic events instrumented.
  Must be verified live on staging before DNS cutover so the fall ballot traffic is captured.
  Measurement ID `G-KEEV757MNS` (continue the existing Site Kit property), set as `PUBLIC_GA_MEASUREMENT_ID`.
- Replace the default `README.md`.

## Phase D — QA & launch

- Port any content on the current WordPress site not already in the JSON (so nothing is lost).
- Populate `crimeRisk` from Tim's refreshed AGS numbers.
- QA: all 9 district pages render from JSON; maps match official shapes; no 404s; both forms
  tested end-to-end (submission reaches the destination); **analytics verified live** (GA4
  pageviews + events in DebugView, Cloudflare beacon reporting); light/dark; mobile (tables
  scroll, no horizontal body scroll); ballot copy verified.
- Back up WordPress, cut over DNS, announce.

---

## No org attribution (explicit request)
The site must not reference **The Confluence Cast** or **Columbus Underground** anywhere — footer,
About, copy, or copyright. It stands as "Columbus Districts, an independent, nonpartisan civic
resource"; copyright reads "© [year] Columbus Districts." The concepts in `design-concepts/` are
already scrubbed — match them. Note the old `.astro` templates still in the repo (Layout/About)
carry these names; drop them when you rebuild from the concepts.

## Decisions already made (don't re-litigate)
- **Host:** Cloudflare Pages. **Integration:** build-time sync (site stays static). **Sequence:**
  full build before relaunch. **Crime:** kept (Tim refreshing numbers), shown as vs-city bars.
- **Design:** approved — warm paper / Scioto slate `#233B54` / Columbus scarlet `#C13B2A`;
  Newsreader + Public Sans; full light+dark; map-as-hero; demographics as data-viz with
  compare-to-city framing.

## Watch-outs
- District median income/rent/home-value run high (block-group-median averaging) — lean on
  **rank / relative position** for comparisons, not absolute citywide dollars, until true
  medians are sourced.
- Ballot page copy is time-sensitive and must be re-verified at launch.
- Keep the demographics `snapshots` array intact — it powers the Data page's longitudinal view.
