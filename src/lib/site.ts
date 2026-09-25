/**
 * site.ts — small site-wide constants shared across pages.
 *
 * LAST_REVIEWED is the single source of truth for content-freshness stamps:
 * data-bearing pages render "Last reviewed: <date>" from it, wire it into their
 * JSON-LD dateModified, and the footer stamp derives from it too. Update this one
 * value whenever the data pages are re-verified against sources.
 */
export const SITE_NAME = "Columbus Districts";
export const SITE_URL = "https://columbusdistricts.com";

/** ISO 8601. When the site's data-bearing pages were last reviewed against sources. */
export const LAST_REVIEWED = "2026-09-02";

/** ISO 8601. First public launch — the datePublished baseline for page schemas. */
export const SITE_LAUNCHED = "2026-08-24";

/**
 * ISO 8601. When the /2026-ballot/ explainer was last re-verified against the Franklin County
 * Board of Elections' certified documents. Separate from LAST_REVIEWED so a ballot-page update
 * doesn't claim the district data pages were re-checked too.
 */
export const BALLOT_UPDATED = "2026-09-25";

/**
 * Tag an outbound link with UTM parameters so the official sources and news outlets we cite can
 * see columbusdistricts.com referrals. Keeps any existing query string and #fragment.
 *   utm("https://example.org/story", "issue8_notice") ->
 *   https://example.org/story?utm_source=columbusdistricts.com&utm_medium=referral&utm_campaign=2026_ballot&utm_content=issue8_notice
 */
export function utm(url: string, content?: string, campaign: string = "2026_ballot"): string {
  const u = new URL(url);
  u.searchParams.set("utm_source", "columbusdistricts.com");
  u.searchParams.set("utm_medium", "referral");
  u.searchParams.set("utm_campaign", campaign);
  if (content) u.searchParams.set("utm_content", content);
  return u.toString();
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

/** "2026-08-24" -> "August 24, 2026". Parses the ISO parts directly (no timezone drift). */
export function formatReviewDate(iso: string = LAST_REVIEWED): string {
  const [y, m, d] = iso.split("-").map(Number);
  return `${MONTHS[m - 1]} ${d}, ${y}`;
}

/** "2026-08-24" -> "August 2026". Used for the footer stamp. */
export function reviewMonthYear(iso: string = LAST_REVIEWED): string {
  const [y, m] = iso.split("-").map(Number);
  return `${MONTHS[m - 1]} ${y}`;
}
