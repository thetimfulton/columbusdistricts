# Columbus Districts — SEO & CivicWorth Cross-Promotion Recommendations

*Prepared August 25, 2026, from a review of the `columbusdistricts` Astro rebuild and the `civicworth` repo's own SEO/outreach docs. Updated August 26, 2026, after the site went live.*

## QA follow-up (Aug 26, 2026, evening)

Two items from the post-launch check below — both now fully resolved, in-repo and live in
Cloudflare:

**1. Canonical/redirect mismatch — fixed.**
The stale comment in [`Layout.astro`](src/components/Layout.astro:55) (which had described www
as canonical) is corrected — it now states the apex is canonical, www must 301 to it, and that
redirect belongs at the Cloudflare zone/redirect-rule level, not `public/_redirects` (which can't
do cross-host redirects; each custom domain otherwise serves the build independently). Build
re-run clean (20 pages); `dist/sitemap-0.xml` and the canonical tags both confirm the apex.

Live re-check at the time found the *actual* state differed from the original QA report: apex and
www were both serving 200 directly as two independent copies (no redirect either direction), not
an apex→www 301 — confirmed via the Cloudflare Pages API (`columbusdistricts` project, account
"Tim Fulton"), which showed both `columbusdistricts.com` and `www.columbusdistricts.com` as
`active` custom domains with no redirect configured between them. Pages custom domains have no
built-in "primary domain" concept — the fix has to be a zone-level redirect rule.

**Fixed live**, via the Cloudflare dashboard (Rules → Redirect Rules → "Redirect from WWW to
root" template): `https://www.*` → `https://${1}`, 301, query string preserved. Verified after
deploy: `http://` and `https://` on both `columbusdistricts.com` and `www.columbusdistricts.com`
all resolve to `https://columbusdistricts.com/`, with paths and query strings intact.

A "domain canonicalization" check with the verifying `curl` commands is now in
[`LAUNCH.md`](LAUNCH.md), section 7 (Cut over), checked off and re-checkable any time the Pages
project's domains or redirect rules are touched again.

**2. AI-crawler robots.txt block — turned off (Tim's call).**
Diffed the live `robots.txt` (both hosts) against [`public/robots.txt`](public/robots.txt) in this
repo: the repo file only has the plain `User-agent: * / Allow: /` + sitemap block; the
`# BEGIN Cloudflare Managed content` … `# END` section — which added `Content-Signal:
ai-train=no,use=reference` and `Disallow: /` for `GPTBot`, `ClaudeBot`, `Google-Extended`,
`Applebot-Extended`, `CCBot`, `Bytespider`, `Amazonbot`, and `meta-externalagent` — was injected at
the edge by Cloudflare's AI Crawl Control, not anything in this codebase. `Googlebot`/`Bingbot`
indexing was untouched throughout.

Tim decided: turn it off, so AI answer engines can cite the ballot explainer. Two separate
Cloudflare mechanisms were blocking AI crawlers and both are now disabled:
- **AI Crawl Control → Signals → "Managed robots.txt"** — turned off. This was generating the
  `Disallow` block and `Content-Signal` line in `robots.txt`.
- **AI Crawl Control → Security → "Block AI Bots"** — a separate, more aggressive WAF-level rule
  (found set to "Block only on pages with ads") that was actually blocking GPTBot, ClaudeBot,
  CCBot, Bytespider, Google-CloudVertexBot, FacebookBot, and others at the network level,
  independent of robots.txt. Switched to "Do not block (allow crawlers)" — without this, turning
  off the robots.txt block alone would have left AI crawlers still hard-blocked.

Verified live: `robots.txt` on both hosts now matches the repo file exactly, and no AI Crawl
Control block remains for any AI bot.

---

## Post-launch check (Aug 26, 2026)

The site is live at columbusdistricts.com and it's in good shape: the homepage, the `/2026-ballot/` explainer, and a district page (checked District Three) all render exactly as designed, GA4 and the Cloudflare Web Analytics beacon are both firing, and the "Name the Districts" form's Turnstile widget completed a live challenge successfully — Phase C's forms are genuinely working, not just wired up. The CivicWorth links are live too: the neighborhood chips, the parcel-lookup line on district pages, and the homepage hero note all resolve correctly.

One real, live issue turned up, and it's the exact one flagged above under "a stale comment that's worth fixing." Typing `columbusdistricts.com` (with or without `https://`) now 301s to `https://www.columbusdistricts.com/` — but every page's `<link rel="canonical">` and `og:url` still declare the bare apex (`https://columbusdistricts.com/...`) as canonical, and the submitted sitemap (`sitemap-0.xml`) lists all nineteen URLs on the bare apex too. So the redirect and the canonical tag now point in opposite directions: a crawler following the sitemap gets bounced from apex to www, then reads a canonical tag pointing right back to the apex URL it just left. That's a real conflict for Google to resolve on a brand-new domain it's about to crawl for the first time, and it's worth resolving before that first crawl rather than after — either flip the Cloudflare redirect to www → apex (matching what the code already declares), or flip `astro.config.mjs`'s `site` value and the canonical logic to www and rebuild. Either works; what matters is picking one and making the redirect and the canonical agree.

Separately, Cloudflare has added its own managed block to `robots.txt` — `Disallow: /` for `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`, `Bytespider`, `Amazonbot`, and `meta-externalagent`, plus `Content-Signal: ai-train=no`. Regular Googlebot and Bing indexing are untouched (the `User-agent: *` block still says `Allow: /`, and the sitemap line is intact), so classic search ranking isn't affected. But it does mean this content is opted out of Google's AI Overviews grounding, ChatGPT, Claude, and Common Crawl-derived training — worth a deliberate decision either way, since a nonpartisan, plain-language "what's on my ballot" explainer is exactly the kind of source an AI answer engine would otherwise want to cite.

Everything flagged before launch that hasn't changed — no on-site address→district lookup yet (the CTA still routes to the comparison table), no Zone In cross-link, no dated update-log section, CivicWorth still only referenced via text rather than a visual "Get Involved" card — is all still open and still worth doing; launch doesn't change any of that list.

## Where this starts from

This isn't a from-scratch SEO audit — the Astro rebuild already has an unusually solid foundation for a site this size. Canonical URLs, Open Graph and Twitter meta, JSON-LD (`WebSite`, `FAQPage` matched to visible FAQ copy, `Dataset`, `Article`, `BreadcrumbList`), an XML sitemap and robots.txt, query-tuned page titles (commit `47a3e0e`), and a `_redirects` file that carries every old WordPress URL pattern forward in both slash forms are all already done. CivicWorth is already cross-linked contextually in six or seven places — the homepage hero, the footer, the data-methodology page, and, on every district page, the neighborhood chips and a "look up your parcel" note (commit `6875fd1`, "Add contextual CivicWorth deep-links across the site"). What follows builds on that work rather than replacing it.

## The one thing that matters more than any of this

*Pre-launch section, kept for context but superseded by the QA sections above: the site went live on August 24, 2026, and the launch-day items are tracked in [`LAUNCH.md`](LAUNCH.md).*

The site is not live. `CLAUDE.md` and `LAUNCH.md` both describe the current WordPress site as still live, with the Astro rebuild sitting in Cloudflare-Pages-ready form waiting on Phase C (host + forms) and Phase D (QA + cutover). The election is November 3 — about ten weeks out. New pages take real time to get crawled, indexed, and to accumulate any ranking signal, and a brand-new civic-explainer page competing for "what's on the Columbus ballot" attention needs every week of runway it can get before early voting starts October 6. The highest-leverage SEO action available right now isn't a meta tag — it's finishing Phase C/D and cutting over as early as realistically possible rather than treating October as the deadline. The moment it's live, verify the domain in Google Search Console and Bing Webmaster Tools, submit the sitemap manually rather than waiting for organic discovery, and use "request indexing" on the homepage, `/2026-ballot/`, and `/all-districts/` specifically, since those three are the pages most likely to catch ballot-season search volume.

## A stale comment that's worth fixing before DNS cutover

Commit `81f9641` ("make the bare apex the canonical host, was www") switched `astro.config.mjs` and the sitemap over to the bare `columbusdistricts.com` apex. But the comment above the canonical-URL logic in `Layout.astro` (around line 55) still reads "always the www host... a Cloudflare dashboard rule to 301 apex → www is still needed" — that's backwards now. Since the config and sitemap both already treat the apex as canonical, the outstanding Cloudflare rule needs to redirect **www → apex**, not the other way around. It's a two-line fix, but it's exactly the kind of stale note that causes someone to wire up the wrong redirect at cutover time, which would leave the canonical tag and the actual serving host disagreeing — the sort of thing that makes Google quietly pick its own canonical and split whatever authority the domain earns between two hosts.

## The flagship idea: bring the address lookup on-site

Right now "find your district" — the homepage's primary CTA, the hero subcopy, and the first FAQ answer — all send the visitor out to the City of Columbus's own ArcGIS embed. That's very likely the single highest-intent query this whole property could own: "what council district am I in," "columbus city council district lookup," "find my columbus city council member." Handing that intent to a third party means the site never captures the visit that matters most.

CivicWorth's whole premise is parcel-level address resolution, and the nine district polygons are already bundled in this repo as `district-boundaries.json`. A small on-site search box — geocode the address (a free geocoder, or CivicWorth's own resolver), then a point-in-polygon check against the boundaries already on hand — could answer "You're in District 4, represented by [name]" directly on columbusdistricts.com, via a Cloudflare Pages Function alongside the two that already exist for the forms. That one feature does three things at once: it captures the top-intent query on-site instead of bouncing it to columbus.gov (longer dwell time, a real engagement signal, and a reason to come back during the next election); it turns the CivicWorth relationship from a text credit into an actual functional integration worth a real "Powered by CivicWorth" placement next to the tool, not a footer line; and — since CivicWorth's own README already describes a public API tier "with partner branding" — it's a legitimate product tie-in rather than just a backlink.

## Give Google (and reporters) something dated to come back to

Outside of `/2026-ballot/`, there's no recency-driven content on the site at all. A short update log — four to six posts between now and November 3 (ballot language gets certified, early voting opens, results get certified) — would do double duty: it gives Google fresh, dated, re-crawlable pages during the exact window search interest is highest, and it gives something concrete to pitch to local press and newsletters every week or two rather than one static page pitched once. It's also a natural, non-repetitive spot to reference CivicWorth's Zone In tool when it's actually relevant to what's being written about — see the next point.

## Close a link CivicWorth's own plan already calls for

CivicWorth's August 2026 marketing plan (`29_marketing_campaign_plan.md`, "Clock 2 — Zone In Phase 2") explicitly says the rebuilt columbusdistricts.com "should launch with its 2026 ballot explainer before November and cross-link CivicWorth parcel surfaces — two founder properties reinforcing each other's authority." As shipped, though, `/2026-ballot/` and the district pages link only to CivicWorth's homepage and its Columbus neighborhood hub — nothing points at Zone In specifically, even though Zone In Phase 2's public-comment window lands in the same stretch as this election. A single contextual line on the district pages or the ballot explainer ("your district's zoning is changing too — see what Zone In Phase 2 means for your block") would fulfill a cross-link that's already been planned, and gives CivicWorth a second, topically distinct entry point instead of routing every click to the same generic homepage link.

## Make the CivicWorth relationship easier to notice, not just present

The integration is genuinely well-placed contextually, but it's easy to skim past — a name-link in body text, one footer line. Three low-effort upgrades: give the "Get Involved" grid on each district page a fourth card (matching the existing three — attend a commission, contact your member, vote on the ballot measures) for "explore your parcel on CivicWorth," instead of the current small text note beneath the demographics section; add one short paragraph on the About and Data pages explaining what CivicWorth actually is, since right now a reader who's never heard of it just sees a bare name-link with no context; and tag the outbound CivicWorth links with UTM parameters that vary by placement (`utm_content=district-page-cta` vs. `footer` vs. `homepage-hero`, for instance). None of the current links are tagged, so inside CivicWorth's own GA4 every click from columbusdistricts.com looks identical regardless of which of the roughly six link placements it came from — tagging them is what would let Tim actually see which spot is pulling weight.

## The honest caveat, and where the real link-building opportunity is

Because both domains share an owner, the links from columbusdistricts.com to civicworth.com — however well-placed — aren't the kind of independent editorial signal that moves CivicWorth's own Authority Score. CivicWorth's own SEO baseline audit (`audits/2026-08-seo-baseline.md`) already names that as the binding constraint: Authority Score 2, zero editorial referring domains, with a target of five by mid-November. What actually helps is columbusdistricts.com earning attention on its own, and it has a genuinely good hook for that right now — a nonpartisan, plain-language explainer of a live, competitive ballot measure is exactly the kind of resource local reporters link for their own readers, and it's a far easier pitch than a commercial product. CivicWorth's own outreach checklist (`docs/link-outreach.md`) already lists the right Columbus targets — Columbus Underground, Axios Columbus, Matter News, the Columbus Dispatch, Columbus Monthly, WOSU, Columbus Business First, the Ohio Capital Journal, OSU's Knowlton School — and that exact list is an easier sell under the columbusdistricts.com banner than under CivicWorth's. Every link earned that way sits on a page that already links to CivicWorth in context, so the outreach doesn't have to choose between the two goals. Worth running this month, while the ballot news cycle is still active.

## Smaller structured-data and on-page items worth doing before launch

A few lower-effort additions: an `Organization` JSON-LD block (name, url, logo) alongside the `WebSite` schema that's already emitted site-wide — right now only `WebSite` is there, and `Organization` is normally what feeds a logo into knowledge-panel-style results. `Person`-flavored markup (or even just consistent `sameAs` linking to each member's official bio, which already exists as a plain link) for the nine actual named council members on their district pages — a low-effort semantic upgrade with a plausible payoff in "who is [name]" answer-box traffic. A unique share image per district — a crop of that district's map plus the member's name — instead of the single site-wide `og-default.png`; pages are noticeably more likely to get clicked from a social share during ballot season when the preview card is specific rather than generic, which otherwise this build already handles well. And a dedicated, indexable "Area Commissions" page listing all nineteen commissions with meeting info — right now each one only appears nested inside its district's page, and a single directory page would be genuinely useful on its own, plus a natural home for a link to CivicWorth's `/columbus/maps` civic-maps catalog. `robots.txt` currently allows everything; adding an explicit `Disallow: /api/` for the two form endpoints costs nothing once they're live and keeps crawler noise off them.

## Two smaller technical notes

Fonts load from Google Fonts with `preconnect`, which is good practice as far as it goes — but `CLAUDE.md` already flags self-hosting vs. linking as an open production decision, and self-hosting Newsreader and Public Sans would remove a third-party render-blocking origin from an otherwise genuinely fast static build. Separately, GA4 is configured to grant `analytics_storage` for every visitor by default, and `CLAUDE.md` itself flags "confirm the approach with Tim" as unresolved; independent of that legal question, a visible privacy notice linked in the footer is also a normal trust signal for a civic-information site and would close an item your own docs already call out as open.

## What not to touch

Worth saying plainly: the FAQ schema matched word-for-word to the visible FAQ copy, the query-tuned `fullTitle` overrides, the breadcrumb schema on district pages, the `LAST_REVIEWED`-driven freshness stamps, the exhaustive `_redirects` coverage of old WordPress URLs, and the contextual (rather than boilerplate) CivicWorth linking are all already doing the work a paid SEO audit would normally start by recommending. Everything above is additive.

## Rough priority order

| When | Action |
|---|---|
| This week | Fix the stale canonical/www comment in `Layout.astro` before wiring the Cloudflare redirect rule; finish Phase C/D (forms + analytics QA); verify GSC + Bing ownership is ready to claim the moment DNS cuts over. |
| Launch day | Submit sitemaps to both consoles; request indexing on `/`, `/2026-ballot/`, `/all-districts/`; start press outreach on the ballot explainer using CivicWorth's existing Columbus target list. |
| Next 2–4 weeks | On-site address→district lookup; elevate the CivicWorth placements (fourth "Get Involved" card, About/Data page context paragraph, UTM tagging); add the Zone In cross-link; add `Organization`/`Person` schema and per-district OG images; ship the short update-log section; add the Area Commissions directory page. |
| Nice to have | Self-host fonts; add a privacy notice page; `Disallow: /api/` in robots.txt; image sitemap for the district maps. |
