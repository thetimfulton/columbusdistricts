#!/usr/bin/env python3
"""
Build Columbus City Council district demographic profiles by:
1. Reading block-group-to-district assignments from the Excel crosswalk
2. Querying Census ACS 5-year 2023 at block group level
3. Aggregating to council districts (1-9)

Outputs: district_profiles.csv
"""

import pandas as pd
import requests
import sys
import time

API_KEY = "83278fe88824c2df834d509a6a9563a29d6c0bef"
BASE_URL = "https://api.census.gov/data/2023/acs/acs5"

# ---------------------------------------------------------------------------
# 1. Read crosswalk: block-level rows → unique block group + district mapping
# ---------------------------------------------------------------------------
print("Reading crosswalk file...")
xw = pd.read_excel("CensusBlock2020_with_CouncilDistrict2023.xlsx")
xw["BLOCKGROUP"] = xw["BLOCKGROUP"].astype(str)

# A block group can span districts if its child blocks are split.
# We need to know the fraction of each block group in each district.
# Use block-level rows to compute shares.
xw["GEOID"] = xw["GEOID"].astype(str)
bg_district = (
    xw.groupby(["BLOCKGROUP", "DISTRICT"])
    .size()
    .reset_index(name="block_count")
)
bg_total = xw.groupby("BLOCKGROUP").size().reset_index(name="total_blocks")
bg_district = bg_district.merge(bg_total, on="BLOCKGROUP")
bg_district["share"] = bg_district["block_count"] / bg_district["total_blocks"]

print(f"  {xw['BLOCKGROUP'].nunique()} unique block groups across {sorted(xw['DISTRICT'].unique())} districts")

# Identify which counties we need to query
counties = sorted(bg_district["BLOCKGROUP"].str[2:5].unique())
print(f"  Counties to query: {counties}")

# ---------------------------------------------------------------------------
# 2. Define Census variables
# ---------------------------------------------------------------------------
# B01001: Sex by Age → total population
# B03002: Hispanic/Latino by Race
# B19013: Median Household Income
# B25064: Median Gross Rent
# B25077: Median Home Value
# B23025: Employment Status for Pop 16+
# B11001: Household Type

variables = {
    # Total population
    "B01001_001E": "total_population",

    # Race/ethnicity (B03002)
    "B03002_001E": "race_total",
    "B03002_003E": "nh_white",
    "B03002_004E": "nh_black",
    "B03002_005E": "nh_american_indian",
    "B03002_006E": "nh_asian",
    "B03002_012E": "hispanic",

    # Median household income
    "B19013_001E": "median_hh_income",

    # Median gross rent
    "B25064_001E": "median_gross_rent",

    # Median home value
    "B25077_001E": "median_home_value",

    # Employment status (pop 16+)
    "B23025_001E": "pop_16plus",
    "B23025_003E": "labor_force_civilian",
    "B23025_005E": "unemployed",

    # Household type
    "B11001_001E": "total_households",
    "B11001_002E": "family_households",
    "B11001_007E": "nonfamily_households",
}

var_list = list(variables.keys())

# ---------------------------------------------------------------------------
# 3. Query Census API by county
# ---------------------------------------------------------------------------
print("Querying Census ACS 2023 5-year API...")

all_frames = []
for county in counties:
    # Split vars into chunks (API limit ~50 vars per call)
    chunk_size = 40
    for i in range(0, len(var_list), chunk_size):
        chunk = var_list[i : i + chunk_size]
        params = {
            "get": ",".join(chunk),
            "for": "block group:*",
            "in": f"state:39 county:{county}",
            "key": API_KEY,
        }
        r = requests.get(BASE_URL, params=params)

        # Fall back to keyless if key is invalid
        if "Invalid Key" in r.text:
            del params["key"]
            r = requests.get(BASE_URL, params=params)

        if r.status_code != 200:
            print(f"  ERROR for county {county}: HTTP {r.status_code}")
            sys.exit(1)

        data = r.json()
        header = data[0]
        rows = data[1:]
        df_chunk = pd.DataFrame(rows, columns=header)

        # Build 12-digit GEOID: state(2) + county(3) + tract(6) + block_group(1)
        df_chunk["BLOCKGROUP"] = (
            df_chunk["state"] + df_chunk["county"] + df_chunk["tract"] + df_chunk["block group"]
        )

        # Keep only BLOCKGROUP + variable columns
        keep_cols = [c for c in chunk if c in df_chunk.columns] + ["BLOCKGROUP"]
        df_chunk = df_chunk[keep_cols]
        all_frames.append(df_chunk)

        time.sleep(0.3)  # polite rate limiting

    print(f"  County {county}: done")

# Merge all chunks on BLOCKGROUP
census = all_frames[0]
for df in all_frames[1:]:
    census = census.merge(df, on="BLOCKGROUP", how="outer")

# Rename columns
census.rename(columns=variables, inplace=True)

# Convert to numeric
numeric_cols = list(variables.values())
for col in numeric_cols:
    census[col] = pd.to_numeric(census[col], errors="coerce")

print(f"  Retrieved {len(census)} block groups from API")

# ---------------------------------------------------------------------------
# 4. Join to district crosswalk
# ---------------------------------------------------------------------------
merged = bg_district.merge(census, on="BLOCKGROUP", how="left")
print(f"  Matched {merged['total_population'].notna().sum()} of {len(merged)} BG-district rows")

# Apply share weights: for summable vars, multiply by the block-count share
summable = [
    "total_population",
    "race_total", "nh_white", "nh_black", "nh_american_indian", "nh_asian", "hispanic",
    "pop_16plus", "labor_force_civilian", "unemployed",
    "total_households", "family_households", "nonfamily_households",
]

median_vars = ["median_hh_income", "median_gross_rent", "median_home_value"]

for col in summable:
    merged[col + "_wtd"] = merged[col] * merged["share"]

# Weight for medians: population share
merged["pop_weight"] = merged["total_population"] * merged["share"]

# Census uses negative codes for missing/not computable medians — replace with NaN
for mv in median_vars:
    merged.loc[merged[mv] < 0, mv] = pd.NA

# ---------------------------------------------------------------------------
# 5. Aggregate by district
# ---------------------------------------------------------------------------
print("Aggregating to districts...")

agg_dict = {col + "_wtd": "sum" for col in summable}
agg_dict["pop_weight"] = "sum"

# For medians, compute weighted average (only where median is valid)
for mv in median_vars:
    merged[mv + "_num"] = merged[mv] * merged["pop_weight"]
    # Track the population weight only for block groups with valid median values
    merged[mv + "_pop_valid"] = merged["pop_weight"].where(merged[mv].notna(), 0)
    agg_dict[mv + "_num"] = "sum"
    agg_dict[mv + "_pop_valid"] = "sum"

district = merged.groupby("DISTRICT").agg(agg_dict).reset_index()

# Finalize summable columns
for col in summable:
    district[col] = district[col + "_wtd"].round(0).astype(int)
    district.drop(columns=[col + "_wtd"], inplace=True)

# Finalize median estimates (using only valid-median population weights)
for mv in median_vars:
    district[mv + "_est"] = (district[mv + "_num"] / district[mv + "_pop_valid"]).round(0).astype(int)
    district.drop(columns=[mv + "_num", mv + "_pop_valid"], inplace=True)

district.drop(columns=["pop_weight"], inplace=True)

# ---------------------------------------------------------------------------
# 6. Compute derived columns
# ---------------------------------------------------------------------------
district["pct_nh_white"] = (district["nh_white"] / district["total_population"] * 100).round(1)
district["pct_nh_black"] = (district["nh_black"] / district["total_population"] * 100).round(1)
district["pct_nh_asian"] = (district["nh_asian"] / district["total_population"] * 100).round(1)
district["pct_nh_american_indian"] = (district["nh_american_indian"] / district["total_population"] * 100).round(1)
district["pct_hispanic"] = (district["hispanic"] / district["total_population"] * 100).round(1)
district["pct_other"] = (100 - district["pct_nh_white"] - district["pct_nh_black"]
                         - district["pct_nh_asian"] - district["pct_nh_american_indian"]
                         - district["pct_hispanic"]).round(1)

district["unemployment_rate"] = (district["unemployed"] / district["labor_force_civilian"] * 100).round(1)
district["pct_family_households"] = (district["family_households"] / district["total_households"] * 100).round(1)

# ---------------------------------------------------------------------------
# 7. Arrange and output
# ---------------------------------------------------------------------------
output_cols = [
    "DISTRICT",
    "total_population",
    "total_households",
    "family_households",
    "nonfamily_households",
    "pct_family_households",
    "nh_white", "pct_nh_white",
    "nh_black", "pct_nh_black",
    "nh_asian", "pct_nh_asian",
    "nh_american_indian", "pct_nh_american_indian",
    "hispanic", "pct_hispanic",
    "pct_other",
    "median_hh_income_est",
    "median_gross_rent_est",
    "median_home_value_est",
    "pop_16plus",
    "labor_force_civilian",
    "unemployed",
    "unemployment_rate",
]

district = district[output_cols].sort_values("DISTRICT")

outfile = "district_profiles.csv"
district.to_csv(outfile, index=False)

print(f"\nWrote {outfile}")
print("\nNOTE: Columns ending in '_est' (median income, rent, home value) are")
print("population-weighted averages across block groups — approximations, not true medians.")
print()
print(district.to_string(index=False))
