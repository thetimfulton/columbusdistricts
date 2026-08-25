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
export const LAST_REVIEWED = "2026-08-24";

/** ISO 8601. First public launch — the datePublished baseline for page schemas. */
export const SITE_LAUNCHED = "2026-08-24";

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
