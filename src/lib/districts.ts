/**
 * districts.ts — shared district data access + demographics derivations.
 *
 * Phase A note: the "Compared to Columbus" citywide baseline is derived here as a
 * population-weighted average across the nine district snapshots (a documented
 * approximation, consistent with how the district figures were built). Phase B's
 * CivicWorth sync will re-derive demographics from real council polygons and can
 * replace this baseline with an authoritative citywide figure.
 */
import d1 from "../data/districts/district-1.json";
import d2 from "../data/districts/district-2.json";
import d3 from "../data/districts/district-3.json";
import d4 from "../data/districts/district-4.json";
import d5 from "../data/districts/district-5.json";
import d6 from "../data/districts/district-6.json";
import d7 from "../data/districts/district-7.json";
import d8 from "../data/districts/district-8.json";
import d9 from "../data/districts/district-9.json";

export const districts: any[] = [d1, d2, d3, d4, d5, d6, d7, d8, d9];

/** The snapshot matching current_vintage (fallback: last snapshot). */
export function currentSnapshot(d: any) {
  const snaps = d.demographics.snapshots;
  return snaps.find((s: any) => s.vintage === d.demographics.current_vintage) ?? snaps[snaps.length - 1];
}

/** The most recent snapshot that is NOT the current vintage (for change chips). */
export function priorSnapshot(d: any) {
  const curV = d.demographics.current_vintage;
  const others = d.demographics.snapshots.filter((s: any) => s.vintage !== curV);
  return others.length ? others[others.length - 1] : null;
}

/** Population-weighted citywide average of a numeric field across all 9 districts. */
export function citywide(key: string): number | null {
  let num = 0;
  let den = 0;
  for (const d of districts) {
    const c = currentSnapshot(d).data;
    const w = c.total_population || 0;
    const v = c[key];
    if (typeof v === "number" && w > 0) {
      num += v * w;
      den += w;
    }
  }
  return den ? num / den : null;
}

/** Sum of a numeric field across all 9 districts. */
export function citywideSum(key: string): number {
  return districts.reduce((acc, d) => acc + (currentSnapshot(d).data[key] || 0), 0);
}

export interface MetricComparison {
  value: number;
  min: number;
  max: number;
  pos: number; // 0-100 position within [min,max]
  cityValue: number | null;
  cityPos: number; // 0-100 position of city average within [min,max]
  rankDesc: number; // 1 = highest
  rankAsc: number; // 1 = lowest
  count: number;
  pctVsCity: number | null; // signed % difference vs city
}

/** Compare one district's current value for `key` against the other 8 + citywide. */
export function compareMetric(district: any, key: string): MetricComparison {
  const vals = districts
    .map((d) => currentSnapshot(d).data[key])
    .filter((v) => typeof v === "number") as number[];
  const value = currentSnapshot(district).data[key];
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const span = max - min;
  const cityValue = citywide(key);
  const norm = (v: number) => (span > 0 ? ((v - min) / span) * 100 : 50);
  const sortedDesc = [...vals].sort((a, b) => b - a);
  const rankDesc = sortedDesc.indexOf(value) + 1;
  return {
    value,
    min,
    max,
    pos: norm(value),
    cityValue,
    cityPos: cityValue != null ? norm(cityValue) : 50,
    rankDesc,
    rankAsc: vals.length - rankDesc + 1,
    count: vals.length,
    pctVsCity: cityValue ? ((value - cityValue) / cityValue) * 100 : null,
  };
}

/** Ordinal helper: 1 -> "1st", 2 -> "2nd", ... */
export function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}
