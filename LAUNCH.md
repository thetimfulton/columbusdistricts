# Launch checklist — Columbus Districts

Pre-cutover steps for the Astro rebuild → Cloudflare Pages → `columbusdistricts.com`.
Do NOT cut over DNS until every **Verify on staging** box passes.

## 1. Cloudflare Pages project
- [ ] Connect the Git repo to Cloudflare Pages. Build command `npm run build`, output dir `dist`.
- [ ] Confirm the `functions/` directory deploys as Pages Functions (`/api/suggest`, `/api/name`).
- [ ] Note the staging URL (`*.pages.dev`) for the checks below.

## 2. Environment variables (Pages → Settings → Environment variables)
See [`.env.example`](.env.example). Set for **Production** (and Preview if you stage there):
- [ ] `PUBLIC_GA_MEASUREMENT_ID = G-KEEV757MNS` (the existing GA4 property)
- [ ] `PUBLIC_CF_BEACON_TOKEN` (from Cloudflare Web Analytics)
- [ ] `PUBLIC_TURNSTILE_SITE_KEY` + `TURNSTILE_SECRET_KEY` (Turnstile widget)
- [ ] `FORMSPREE_FORM_ID` (or `FORMSPREE_SUGGEST_ID` / `FORMSPREE_NAME_ID`)
- [ ] In Formspree, set the destination inbox to **info@columbusdistricts.com** and confirm it

> `PUBLIC_*` vars are baked in at build time — **re-deploy** after setting them.

## 3. Forms — verify on staging
- [ ] Submit **Suggest an edit** on a district page → lands on the thank-you page → email arrives at info@
- [ ] Submit **Name the district** → thank-you page → email arrives
- [ ] Turnstile widget renders and blocks a submission with no/failed challenge
- [ ] Honeypot: a bot-style submit (hidden `company` filled) is silently accepted, no email

## 4. Analytics — verify LIVE on staging (before cutover — captures the fall ballot surge)
- [ ] GA4 **DebugView** shows pageviews from the staging site
- [ ] Events fire: `find_district_click`, `ballot_engagement`, `form_submit`, `outbound_click`
- [ ] Cloudflare Web Analytics shows the staging beacon reporting
- [ ] (Optional) decide whether to add a cookie/privacy notice — GA now tracks all visitors

## 5. Content / data
- [ ] Populate `crimeRisk` in `src/data/districts/*.json` from the refreshed AGS numbers
      (% vs. citywide average per category), re-build, confirm the Public Safety bars render
- [ ] Verify the **2026 ballot** copy against the certified ballot language; remove the draft banner
- [ ] Port any content still only on the live WordPress site
- [ ] Re-run `scripts/sync_from_civicworth.py` if CivicWorth data or membership changed

## 6. Final QA (done for the current build — re-check after content/env changes)
- [x] All 9 district pages render from JSON, every section present
- [x] Maps render at full CivicWorth fidelity (D1 = 2,849-vertex boundary)
- [x] No broken internal links / 404s
- [x] Both forms tested end-to-end (validation, honeypot, redirect)
- [x] Light + dark themes
- [x] Mobile: no horizontal body scroll; wide tables scroll internally; hamburger nav works
- [x] Data sanity: race shares sum to 100%, D2 population + D3 Asian corrected, no null fields
- [x] No "The Confluence Cast" / "Columbus Underground" anywhere

## 7. Cut over
- [ ] Back up the current WordPress site (files + database)
- [ ] Add `columbusdistricts.com` (+ `www`) as a custom domain in Cloudflare Pages
- [ ] Update DNS to point at Cloudflare Pages
- [ ] Confirm HTTPS, the apex/www redirect, and a live pageview in GA
- [ ] Announce
