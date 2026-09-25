# Launch checklist — Columbus Districts

**Launched 2026-08-24.** The Astro site is live on Cloudflare Pages at `columbusdistricts.com`;
DNS was cut over from the old WordPress site on 2026-08-24. This file is now the launch record
plus the remaining open items. Any box still unchecked below is open.

## 1. Cloudflare Pages project
- [x] Connect the Git repo to Cloudflare Pages. Build command `npm run build`, output dir `dist`.
      (`main` → production; branches get previews at `<branch>.columbusdistricts.pages.dev`.)
- [x] Confirm the `functions/` directory deploys as Pages Functions (`/api/suggest`, `/api/name`).
      (Verified live 2026-09-25: an empty POST to `/api/suggest` gets the Function's 400.)
- [x] Note the staging URL: `columbusdistricts.pages.dev`.

## 2. Environment variables (Pages → Settings → Environment variables)
See [`.env.example`](.env.example). Set for **Production** (and Preview if you stage there):
- [x] `PUBLIC_GA_MEASUREMENT_ID = G-KEEV757MNS` (the existing GA4 property)
- [x] `PUBLIC_CF_BEACON_TOKEN` (from Cloudflare Web Analytics)
- [x] `PUBLIC_TURNSTILE_SITE_KEY` + `TURNSTILE_SECRET_KEY` (Turnstile widget)
- [x] `FORMSPREE_FORM_ID` (or `FORMSPREE_SUGGEST_ID` / `FORMSPREE_NAME_ID`) — per-form ids set
      (values live in the Pages dashboard, not in this repo)
- [x] In Formspree, set the destination inbox to **info@columbusdistricts.com** and confirm it
      (both forms: Workflow → Email action enabled → info@columbusdistricts.com)
      (All Production variables above verified present in the Pages dashboard 2026-09-02.)

> `PUBLIC_*` vars are baked in at build time — **re-deploy** after setting them.

## 3. Forms — verify on staging
- [x] Submit **Suggest an edit** on a district page → lands on the thank-you page → email arrives at info@
- [x] Submit **Name the district** → thank-you page → email arrives
- [x] Turnstile widget renders and blocks a submission with no/failed challenge
      (Verified live 2026-09-25: a POST with no Turnstile token is rejected with 400.)
- [x] Honeypot: a bot-style submit (hidden `company` filled) is silently accepted, no email
      (Verified live 2026-09-25: it 303s to the thank-you page before any Formspree call.)

> **Where submissions land (checked 2026-09-02):** page form → Pages Function (`/api/suggest`,
> `/api/name`) → Formspree → email to info@columbusdistricts.com (a Google Workspace mailbox —
> Cloudflare Email Routing is not used on this zone). Cloudflare Pages → `columbusdistricts` →
> Production variables hold both Formspree ids plus the Turnstile keys; both Formspree forms show
> the Aug 24 test submissions with success status and have the Email action enabled → info@.
> To review submissions: formspree.io → Forms → either "Columbus Districts – …" form →
> Submissions (check the **Spam** tab too — one Aug 24 test landed there). Inbox arrival at
> info@ was not re-verified from here; glance at that mailbox once to close the loop.

## 4. Analytics — verify on production (open — captures the fall ballot surge)
The GA4 tag (`G-KEEV757MNS`) and the Cloudflare beacon are both present on live pages (checked
2026-09-25). What's left is confirming the data arrives:
- [ ] GA4 **DebugView** / Realtime shows pageviews from columbusdistricts.com
- [ ] Events fire: `find_district_click`, `ballot_engagement`, `form_submit`, `outbound_click`
- [ ] Cloudflare Web Analytics shows the production beacon reporting
- [x] Decide whether to add a cookie/privacy notice. **Decided (Tim, 2026-09-25): no notice.**
      Analytics default on (`analytics_storage` granted; ad signals denied).

## 5. Content / data
- [x] Populate `crimeRisk` in `src/data/districts/*.json` (% vs. citywide average per category)
      and confirm the Public Safety bars render. Done with the prior site's AGS figures
      (`f2a8411`). Swap in refreshed AGS numbers when available.
- [x] Verify the **2026 ballot** copy against the certified ballot language; remove the draft banner.
      (2026-09-25: the Franklin County BOE has certified the measures as **Issue 8** (by petition)
      and **Issue 9** (by Council). Ballot language checked verbatim against the BOE notices of
      election (Sept. 14), draft banner removed, outbound links UTM-tagged. Went live 2026-09-25
      via PR #10.)
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
- [ ] Back up the current WordPress site (files + database). **Not confirmed.** Do this before
      the old AWS/WordPress hosting is shut down or lapses.
- [x] Add `columbusdistricts.com` (+ `www`) as a custom domain in Cloudflare Pages
- [x] Update DNS to point at Cloudflare Pages (nameservers moved to Cloudflare 2026-08-24)
- [x] **Domain canonicalization** — `astro.config.mjs`'s `site` (bare apex, no `www`) is the
      canonical host. Both custom domains on a Cloudflare Pages project serve the build
      independently by default, so the redirect between them has to be set explicitly at the
      Pages custom-domain / zone redirect-rule level — re-check this any time the project's
      domains are added, removed, or re-verified, not just at initial cutover:
      - [x] `curl -IL http://columbusdistricts.com` lands on `https://columbusdistricts.com/` (200)
      - [x] `curl -IL https://columbusdistricts.com` returns 200 directly (no redirect)
      - [x] `curl -IL http://www.columbusdistricts.com` and `curl -IL https://www.columbusdistricts.com`
            both 301 to `https://columbusdistricts.com/` — not the other way around
      - [x] `<link rel="canonical">` / `og:url` on a live page and the sitemap (`sitemap-0.xml`)
            agree with the host that actually serves (apex)
      (Verified 2026-08-26 evening. Fixed via a Cloudflare Redirect Rule — Rules → Redirect
      Rules → "Redirect from WWW to root" template, `https://www.*` → `https://${1}`, 301,
      query string preserved — since Pages custom domains have no built-in "primary domain"
      concept; apex and www otherwise serve the build independently. Re-check this box if the
      Pages project's domains are ever re-added or the redirect rule is touched.)
- [ ] Confirm a live pageview in GA (the tag is on live pages; see §4)
- [ ] Announce
