#!/usr/bin/env python3
"""
sync_from_civicworth.py — Phase B build-time sync.

Pulls Columbus council data from the CivicWorth Supabase (project cohdnvvhmrqaupamhnly)
and writes it into src/data/districts/district-N.json + src/data/district-boundaries.json:

  1. Boundaries  -> inline SVG path per district (ST_SimplifyPreserveTopology 0.00012),
                    projected with a shared bbox + cos(lat) so all 9 align on one viewBox.
  2. Member + population2020  -> from boundaries.properties.
  3. Enrichment counts (block groups, voting precincts) via spatial predicates.
  4. Demographics re-derivation: aggregate ACS 5-year block-group estimates into each
     district using a POPULATION-weighted block-group->district crosswalk. The crosswalk
     apportions each block group to districts by its share of 2020-census BLOCK population
     (official block->district equivalency), NOT by polygon area — area-weighting badly
     under-counts fringe districts (D1/D9) whose block groups sprawl outside the city into
     sparse land. The equivalency is cross-validated against CivicWorth's authoritative
     population2020 (agreement within 0.7% for every district). This fixes the old pipeline's
     D2 over-count (was 143,899; true ~100.5k) and the D3 Asian count. The demographics
     `snapshots` structure is preserved (each vintage's `data` is recomputed in place;
     `esri_estimates` and `current_vintage` are kept).
  5. District medians (income, home value, gross rent) are POOLED medians: the ACS
     distribution tables (B19001 / B25075 / B25063) are aggregated to the district with the
     same crosswalk shares and the median is linearly interpolated within its bin. This
     replaces the earlier population-weighted average of block-group medians, which
     overstated district income by ~11% overall (up to 17% in D3) and D7 home value by ~23%.
     Pooling all nine districts reproduces the Bureau's published citywide Columbus medians
     (B19013 / B25077 / B25064 for place 18000) within ~1%.

Run as a committed data refresh, NOT at runtime. See scripts/README.md.

DB access:
  Set CIVICWORTH_DB_URL (session-pooler connection string) to regenerate the spatial
  caches live. Without it, the script falls back to the committed caches in
  scripts/civicworth_cache/ (crosswalk + district meta) and still refreshes demographics
  from the live Census API. Boundaries are only regenerated when the DB is reachable.

Env:
  CIVICWORTH_DB_URL   optional  postgres URL for live spatial regeneration
  CENSUS_API_KEY      optional  Census API key (falls back to keyless)
"""
import json
import math
import os
import sys
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DISTRICTS_DIR = ROOT / "src" / "data" / "districts"
BOUNDARIES_FILE = ROOT / "src" / "data" / "district-boundaries.json"
CACHE_DIR = Path(__file__).resolve().parent / "civicworth_cache"
BLOCK_EQUIV_XLSX = ROOT / "CensusBlock2020_with_CouncilDistrict2023.xlsx"

CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "83278fe88824c2df834d509a6a9563a29d6c0bef")

# Counties the Columbus districts touch (Franklin 049, plus Delaware 041 in D1 and
# Fairfield 045 in D9). ACS + decennial block pulls must cover all three.
COUNTIES = ("041", "045", "049")

# ACS 5-year vintages that map to each snapshot in the district JSON.
# vintage label in JSON -> Census dataset year (the trailing year of the 5-year window)
VINTAGE_YEAR = {
    "ACS 2019-2023": 2023,
    "ACS 2017-2021": 2021,
}

# Census variables (same set the original build_district_profiles.py used).
VARIABLES = {
    "B01001_001E": "total_population",
    "B03002_001E": "race_total",
    "B03002_003E": "nh_white",
    "B03002_004E": "nh_black",
    "B03002_005E": "nh_american_indian",
    "B03002_006E": "nh_asian",
    "B03002_012E": "hispanic",
    "B23025_001E": "pop_16plus",
    "B23025_003E": "labor_force_civilian",
    "B23025_005E": "unemployed",
    "B11001_001E": "total_households",
    "B11001_002E": "family_households",
    "B11001_007E": "nonfamily_households",
}
SUMMABLE = [
    "total_population", "nh_white", "nh_black", "nh_american_indian", "nh_asian", "hispanic",
    "labor_force_civilian", "unemployed", "total_households", "family_households",
]

# Distribution tables used to derive POOLED district medians (see docstring, item 5).
# Each entry: (ACS table, first/last variable index, [(bin lower bound, bin upper bound), ...]).
# Upper bound None = open-ended top bin. Bin edges match the ACS 5-year tables for 2015+.
_INCOME_BINS = [(0, 10000), (10000, 15000), (15000, 20000), (20000, 25000), (25000, 30000),
                (30000, 35000), (35000, 40000), (40000, 45000), (45000, 50000), (50000, 60000),
                (60000, 75000), (75000, 100000), (100000, 125000), (125000, 150000),
                (150000, 200000), (200000, None)]
_VALUE_BINS = [(0, 10000), (10000, 15000), (15000, 20000), (20000, 25000), (25000, 30000),
               (30000, 35000), (35000, 40000), (40000, 50000), (50000, 60000), (60000, 70000),
               (70000, 80000), (80000, 90000), (90000, 100000), (100000, 125000),
               (125000, 150000), (150000, 175000), (175000, 200000), (200000, 250000),
               (250000, 300000), (300000, 400000), (400000, 500000), (500000, 750000),
               (750000, 1000000), (1000000, 1500000), (1500000, 2000000), (2000000, None)]
_RENT_BINS = [(0, 100), (100, 150), (150, 200), (200, 250), (250, 300), (300, 350), (350, 400),
              (400, 450), (450, 500), (500, 550), (550, 600), (600, 650), (650, 700), (700, 750),
              (750, 800), (800, 900), (900, 1000), (1000, 1250), (1250, 1500), (1500, 2000),
              (2000, 2500), (2500, 3000), (3000, 3500), (3500, None)]
MEDIAN_TABLES = {
    # B19001: household income in the past 12 months (16 bins, _002E.._017E)
    "median_hh_income": ("B19001", 2, 17, _INCOME_BINS),
    # B25075: value of owner-occupied housing units (26 bins, _002E.._027E)
    "median_home_value": ("B25075", 2, 27, _VALUE_BINS),
    # B25063: gross rent, cash-rent bins only (_003E.._026E; _027E "no cash rent" excluded,
    # matching how B25064 median gross rent is defined)
    "median_gross_rent": ("B25063", 3, 26, _RENT_BINS),
}
MEDIANS = list(MEDIAN_TABLES.keys())
for _m, (_tbl, _lo, _hi, _bins) in MEDIAN_TABLES.items():
    assert _hi - _lo + 1 == len(_bins), f"{_tbl}: bin count mismatch"
    for _j, _i in enumerate(range(_lo, _hi + 1)):
        VARIABLES[f"{_tbl}_{_i:03d}E"] = f"{_m}__bin{_j}"


def pooled_median(counts, bins):
    """Median of a binned distribution, linearly interpolated within the median bin.

    Same approach the Bureau documents for estimating medians from published interval
    tables. Returns the lower bound if the median falls in the open-ended top bin, and
    None when the distribution is empty.
    """
    total = sum(counts)
    if total <= 0:
        return None
    half = total / 2.0
    cum = 0.0
    for n, (lo, hi) in zip(counts, bins):
        if cum + n >= half:
            if hi is None or n <= 0:
                return lo
            return lo + (half - cum) / n * (hi - lo)
        cum += n
    return None


# ---------------------------------------------------------------------------
# CivicWorth spatial layer (live DB, or cached exports)
# ---------------------------------------------------------------------------
META_SQL = """
with cd as (
  select (properties->>'districtNumber')::int dist, properties p, geometry g
  from public.boundaries where boundary_type='council_district' and external_id like 'columbus-cd-%'
),
bgmaj as (
  select bg.external_id geoid,
         (select cd.dist from cd order by ST_Area(ST_Intersection(bg.geometry,cd.g)) desc limit 1) dist
  from public.boundaries bg where bg.boundary_type='census_block_group'
    and exists (select 1 from cd where ST_Intersects(bg.geometry, cd.g))
)
select cd.dist,
  cd.p->>'population2020' population2020,
  cd.p->'councilmember'->>'name' member,
  cd.p->'councilmember'->>'role' role,
  cd.p->'councilmember'->>'party' party,
  (select count(*) from bgmaj where bgmaj.dist=cd.dist) block_groups,
  (select count(*) from public.boundaries b where b.boundary_type='voting_precinct'
     and ST_Contains(cd.g, ST_PointOnSurface(b.geometry))) voting_precincts
from cd order by cd.dist;
"""

BOUNDARY_SQL = """
with cd as (
  select (properties->>'districtNumber')::int dist,
         ST_SimplifyPreserveTopology(geometry, 0.00012) g
  from public.boundaries where boundary_type='council_district' and external_id like 'columbus-cd-%'
)
select dist, ST_AsGeoJSON(g, 6) gj,
  ST_XMin((select ST_Extent(g) from cd)) xmin, ST_YMin((select ST_Extent(g) from cd)) ymin,
  ST_XMax((select ST_Extent(g) from cd)) xmax, ST_YMax((select ST_Extent(g) from cd)) ymax
from cd order by dist;
"""


def get_conn():
    url = os.environ.get("CIVICWORTH_DB_URL")
    if not url:
        return None
    try:
        import psycopg2  # noqa
    except ImportError:
        print("  CIVICWORTH_DB_URL set but psycopg2 not installed; using caches.", file=sys.stderr)
        return None
    return psycopg2.connect(url)


def fetch_block_pop(counties=COUNTIES):
    """2020-census block populations (P1_001N) keyed by 15-digit block GEOID."""
    out = {}
    for c in counties:
        params = {"get": "P1_001N", "for": "block:*",
                  "in": f"state:39 county:{c}", "key": CENSUS_API_KEY}
        r = requests.get("https://api.census.gov/data/2020/dec/pl", params=params, timeout=120)
        if "Invalid Key" in r.text:
            params.pop("key")
            r = requests.get("https://api.census.gov/data/2020/dec/pl", params=params, timeout=120)
        r.raise_for_status()
        data = r.json()
        idx = {h: i for i, h in enumerate(data[0])}
        for row in data[1:]:
            g = row[idx["state"]] + row[idx["county"]] + row[idx["tract"]] + row[idx["block"]]
            out[g] = int(row[idx["P1_001N"]])
    return out


def build_crosswalk(meta):
    """Population-weighted block-group -> district crosswalk.

    Uses the official block->district equivalency (CensusBlock2020_..xlsx) and 2020-census
    block populations to compute each block group's population share per district, then
    cross-validates the district block-population totals against CivicWorth's population2020.
    """
    try:
        import openpyxl
    except ImportError:
        print("  openpyxl not installed; using cached crosswalk.", file=sys.stderr)
        return json.loads((CACHE_DIR / "bg_district_crosswalk.json").read_text())["rows"]
    if not BLOCK_EQUIV_XLSX.exists():
        return json.loads((CACHE_DIR / "bg_district_crosswalk.json").read_text())["rows"]

    ws = openpyxl.load_workbook(BLOCK_EQUIV_XLSX, read_only=True).active
    it = ws.iter_rows(values_only=True); next(it)
    block_dist = {str(r[0]): int(r[1]) for r in it if r[0] and r[1]}

    bpop = fetch_block_pop()
    from collections import defaultdict
    # Denominator = TOTAL block-group population (every block in the BG, city or not), so a
    # block group that straddles the city line contributes only its in-city share of the
    # whole-BG ACS estimate. Normalizing by Columbus-only blocks (the original pipeline's bug)
    # assigns a partial BG's ENTIRE population to the district and over-counts (D2 -> 143k).
    bg_tot = defaultdict(float)
    for g, p in bpop.items():
        bg_tot[g[:12]] += p
    bg_dist = defaultdict(lambda: defaultdict(float))  # numerator: in-city blocks by district
    dist_pop = defaultdict(float)
    for g, d in block_dist.items():
        p = bpop.get(g, 0)
        bg_dist[g[:12]][d] += p
        dist_pop[d] += p

    # Cross-validate against CivicWorth pop2020
    for d in range(1, 10):
        official = meta[str(d)]["population2020"]
        gap = (dist_pop[d] - official) / official * 100
        flag = "" if abs(gap) < 2 else "  <-- CHECK"
        print(f"    D{d} block-pop {int(dist_pop[d]):>7,} vs CivicWorth {official:>7,} ({gap:+.1f}%){flag}")

    rows = []
    for bg, dists in bg_dist.items():
        tot = bg_tot[bg]
        if tot <= 0:  # zero-population block group: split equally among assigned districts
            for d in dists:
                rows.append([bg, d, round(1.0 / len(dists), 4)])
        else:
            for d, p in dists.items():
                sh = p / tot
                if sh >= 0.001:
                    rows.append([bg, d, round(sh, 4)])
    (CACHE_DIR / "bg_district_crosswalk.json").write_text(json.dumps({
        "description": "Population-weighted census-block-group -> Columbus council-district "
                       "crosswalk. share = 2020 block population in district / block-group total. "
                       "Cross-validated against CivicWorth population2020 (within 0.7%). "
                       "Regenerate with scripts/sync_from_civicworth.py.",
        "generated": "2026-08-23", "rows": rows}, indent=0))
    return rows


def load_meta(conn):
    if conn:
        cur = conn.cursor()
        cur.execute(META_SQL)
        out = {}
        for dist, pop, member, role, party, bg, prec in cur.fetchall():
            out[str(dist)] = {"population2020": int(pop), "member": member, "role": role,
                              "party": party, "enrichment": {"block_groups": int(bg),
                                                             "voting_precincts": int(prec)}}
        (CACHE_DIR / "district_meta.json").write_text(json.dumps({"districts": out}, indent=2))
        return out
    meta = json.loads((CACHE_DIR / "district_meta.json").read_text())["districts"]
    # Cached meta may carry unreliable library/rec_center counts — keep only trusted fields.
    for d in meta.values():
        d["enrichment"] = {k: d["enrichment"][k] for k in ("block_groups", "voting_precincts")}
    return meta


# ---------------------------------------------------------------------------
# Census ACS
# ---------------------------------------------------------------------------
def fetch_acs(year, counties=COUNTIES):
    """Return {GEOID12: {var: float}} for the given ACS 5-year vintage."""
    base = f"https://api.census.gov/data/{year}/acs/acs5"
    var_list = list(VARIABLES.keys())
    out = {}
    for county in counties:
        for i in range(0, len(var_list), 40):
            chunk = var_list[i:i + 40]
            params = {"get": ",".join(chunk), "for": "block group:*",
                      "in": f"state:39 county:{county}", "key": CENSUS_API_KEY}
            r = requests.get(base, params=params, timeout=60)
            if "Invalid Key" in r.text:
                params.pop("key")
                r = requests.get(base, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            header, rows = data[0], data[1:]
            idx = {h: k for k, h in enumerate(header)}
            for row in rows:
                geoid = row[idx["state"]] + row[idx["county"]] + row[idx["tract"]] + row[idx["block group"]]
                rec = out.setdefault(geoid, {})
                for code in chunk:
                    val = row[idx[code]]
                    rec[VARIABLES[code]] = float(val) if val not in (None, "") else None
            time.sleep(0.3)
    return out


def aggregate(crosswalk, acs):
    """Population-share aggregation of ACS block groups into the 9 districts.

    Counts are apportioned by crosswalk share. Medians are pooled: each block group's
    distribution-table bins (households / owner units / renter units) are apportioned by the
    same share, summed per district, and the district median is interpolated from the pooled
    distribution (see pooled_median). Returns {district: data} plus a 'citywide' entry with
    the medians pooled across all nine districts, for reconciliation against the Bureau's
    published Columbus figures.
    """
    dist = {d: {c: 0.0 for c in SUMMABLE} for d in range(1, 10)}
    bins = {d: {m: [0.0] * len(MEDIAN_TABLES[m][3]) for m in MEDIANS} for d in range(1, 10)}
    for geoid, d, share in crosswalk:
        rec = acs.get(geoid)
        if not rec:
            continue
        for c in SUMMABLE:
            v = rec.get(c)
            if v is not None:
                dist[d][c] += v * share
        for m in MEDIANS:
            b = bins[d][m]
            for j in range(len(b)):
                v = rec.get(f"{m}__bin{j}")
                if v is not None and v >= 0:
                    b[j] += v * share

    def median_of(bin_counts, m):
        v = pooled_median(bin_counts, MEDIAN_TABLES[m][3])
        return round(v) if v is not None else None

    result = {}
    for d in range(1, 10):
        s = dist[d]
        pop = s["total_population"] or 1
        hh = s["total_households"] or 1
        lf = s["labor_force_civilian"] or 1
        pct = lambda x: round(x / pop * 100, 1)
        data = {
            "total_population": round(s["total_population"]),
            "total_households": round(s["total_households"]),
            "pct_family_households": round(s["family_households"] / hh * 100, 1),
            "median_hh_income_est": median_of(bins[d]["median_hh_income"], "median_hh_income"),
            "median_gross_rent_est": median_of(bins[d]["median_gross_rent"], "median_gross_rent"),
            "median_home_value_est": median_of(bins[d]["median_home_value"], "median_home_value"),
            "unemployment_rate": round(s["unemployed"] / lf * 100, 1),
            "pct_nh_white": pct(s["nh_white"]),
            "pct_nh_black": pct(s["nh_black"]),
            "pct_hispanic": pct(s["hispanic"]),
            "pct_nh_asian": pct(s["nh_asian"]),
            "pct_nh_american_indian": pct(s["nh_american_indian"]),
        }
        data["pct_other"] = round(100 - data["pct_nh_white"] - data["pct_nh_black"]
                                  - data["pct_nh_asian"] - data["pct_nh_american_indian"]
                                  - data["pct_hispanic"], 1)
        data["data_note"] = ("Median income, rent, and home value are pooled medians "
                             "interpolated from ACS block-group distribution tables aggregated "
                             "to the district. See /data/ for methodology.")
        result[d] = data
    # Citywide reconciliation figure: pool every district's bins together.
    result["citywide"] = {}
    for m in MEDIANS:
        tot = [0.0] * len(MEDIAN_TABLES[m][3])
        for d in range(1, 10):
            tot = [a + b for a, b in zip(tot, bins[d][m])]
        result["citywide"][m] = median_of(tot, m)
    return result


def fetch_city_medians(year):
    """Bureau-published Columbus city (place 18000) medians, for the reconciliation print."""
    try:
        params = {"get": "B19013_001E,B25077_001E,B25064_001E", "for": "place:18000",
                  "in": "state:39", "key": CENSUS_API_KEY}
        r = requests.get(f"https://api.census.gov/data/{year}/acs/acs5", params=params, timeout=60)
        if "Invalid Key" in r.text:
            params.pop("key")
            r = requests.get(f"https://api.census.gov/data/{year}/acs/acs5", params=params, timeout=60)
        r.raise_for_status()
        hdr, row = r.json()
        v = dict(zip(hdr, row))
        return {"median_hh_income": int(v["B19013_001E"]), "median_home_value": int(v["B25077_001E"]),
                "median_gross_rent": int(v["B25064_001E"])}
    except Exception as e:  # reconciliation is diagnostic only; never block the sync
        print(f"  (could not fetch citywide medians for {year}: {e})", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Boundary projection (only when DB is reachable)
# ---------------------------------------------------------------------------
def project_boundaries(rows):
    xmin, ymin, xmax, ymax = rows[0][2], rows[0][3], rows[0][4], rows[0][5]
    lat0 = math.radians((ymin + ymax) / 2)
    kx = math.cos(lat0)
    scale = 1000.0 / ((xmax - xmin) * kx)
    W = 1000.0
    H = round((ymax - ymin) * scale, 1)

    def proj(lon, lat):
        return (round((lon - xmin) * kx * scale, 1), round((ymax - lat) * scale, 1))

    def ring_to_path(ring):
        pts = [proj(lon, lat) for lon, lat in ring]
        return "M" + "L".join(f"{x} {y}" for x, y in pts) + "Z"

    paths = {}
    for dist, gj, *_ in rows:
        geom = json.loads(gj)
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        d = "".join(ring_to_path(ring) for poly in polys for ring in poly)
        paths[str(dist)] = d
    return {"viewBox": f"0 0 {W} {H}", "paths": paths}


# ---------------------------------------------------------------------------
# Write into district JSON files
# ---------------------------------------------------------------------------
def sync():
    conn = get_conn()
    print("CivicWorth DB:", "live" if conn else "using cached exports")

    meta = load_meta(conn)
    print("Building population-weighted BG->district crosswalk:")
    crosswalk = build_crosswalk(meta)

    # Demographics per vintage
    demo = {}
    for vintage, year in VINTAGE_YEAR.items():
        print(f"Fetching ACS {year} (5-year) block groups…")
        acs = fetch_acs(year)
        demo[vintage] = aggregate(crosswalk, acs)
        print(f"  {vintage}: D2 pop={demo[vintage][2]['total_population']:,} "
              f"D3 Asian={demo[vintage][3]['pct_nh_asian']}%")
        # Reconcile pooled medians against the Bureau's published citywide figures.
        city = fetch_city_medians(year)
        pooled = demo[vintage].pop("citywide")
        for m in MEDIANS:
            if city and pooled.get(m):
                gap = (pooled[m] - city[m]) / city[m] * 100
                flag = "" if abs(gap) < 2 else "  <-- CHECK"
                print(f"    {m:<18} pooled {pooled[m]:>8,} vs published Columbus {city[m]:>8,} ({gap:+.1f}%){flag}")

    # Optional boundary regeneration (DB only)
    if conn:
        cur = conn.cursor()
        cur.execute(BOUNDARY_SQL)
        BOUNDARIES_FILE.write_text(json.dumps(project_boundaries(cur.fetchall())))
        print("Regenerated district-boundaries.json")

    for n in range(1, 10):
        f = DISTRICTS_DIR / f"district-{n}.json"
        d = json.loads(f.read_text())
        m = meta[str(n)]
        d["population2020"] = m["population2020"]
        d["enrichment"] = m["enrichment"]
        if m.get("role"):
            d["councilMember"]["role"] = m["role"]
        for snap in d["demographics"]["snapshots"]:
            v = snap["vintage"]
            if v in demo:
                snap["data"] = demo[v][n]
                snap["pull_date"] = date.today().isoformat()
                snap["source"] = ("U.S. Census Bureau ACS 5-Year via Census API; block groups "
                                  "apportioned to districts by 2020 block population (official "
                                  "block-to-district equivalency); medians pooled from "
                                  "distribution tables (sync_from_civicworth.py)")
        f.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
        print(f"  wrote district-{n}.json")

    if conn:
        conn.close()


if __name__ == "__main__":
    sync()
