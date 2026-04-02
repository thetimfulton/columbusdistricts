#!/usr/bin/env python3
"""
Backfill ACS 2017-2021 5-Year data into district JSON files.
Uses the same crosswalk and methodology as build_district_profiles.py.
"""

import json
import os
import pandas as pd
import requests
import sys
import time

API_KEY = "83278fe88824c2df834d509a6a9563a29d6c0bef"
BASE_URL = "https://api.census.gov/data/2021/acs/acs5"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# ---------------------------------------------------------------------------
# 1. Read crosswalk
# ---------------------------------------------------------------------------
print("Reading crosswalk file...")
xw = pd.read_excel(os.path.join(PROJECT_DIR, "CensusBlock2020_with_CouncilDistrict2023.xlsx"))
xw["BLOCKGROUP"] = xw["BLOCKGROUP"].astype(str)
xw["GEOID"] = xw["GEOID"].astype(str)

bg_district = (
    xw.groupby(["BLOCKGROUP", "DISTRICT"])
    .size()
    .reset_index(name="block_count")
)
bg_total = xw.groupby("BLOCKGROUP").size().reset_index(name="total_blocks")
bg_district = bg_district.merge(bg_total, on="BLOCKGROUP")
bg_district["share"] = bg_district["block_count"] / bg_district["total_blocks"]

counties = sorted(bg_district["BLOCKGROUP"].str[2:5].unique())
print(f"  Counties to query: {counties}")

# ---------------------------------------------------------------------------
# 2. Define Census variables (same as build_district_profiles.py)
# ---------------------------------------------------------------------------
variables = {
    "B01001_001E": "total_population",
    "B03002_001E": "race_total",
    "B03002_003E": "nh_white",
    "B03002_004E": "nh_black",
    "B03002_005E": "nh_american_indian",
    "B03002_006E": "nh_asian",
    "B03002_012E": "hispanic",
    "B19013_001E": "median_hh_income",
    "B25064_001E": "median_gross_rent",
    "B25077_001E": "median_home_value",
    "B23025_001E": "pop_16plus",
    "B23025_003E": "labor_force_civilian",
    "B23025_005E": "unemployed",
    "B11001_001E": "total_households",
    "B11001_002E": "family_households",
    "B11001_007E": "nonfamily_households",
}

var_list = list(variables.keys())

# ---------------------------------------------------------------------------
# 3. Query Census API
# ---------------------------------------------------------------------------
print("Querying Census ACS 2021 5-year API...")

all_frames = []
for county in counties:
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
        df_chunk["BLOCKGROUP"] = (
            df_chunk["state"] + df_chunk["county"] + df_chunk["tract"] + df_chunk["block group"]
        )
        keep_cols = [c for c in chunk if c in df_chunk.columns] + ["BLOCKGROUP"]
        df_chunk = df_chunk[keep_cols]
        all_frames.append(df_chunk)
        time.sleep(0.3)

    print(f"  County {county}: done")

census = all_frames[0]
for df in all_frames[1:]:
    census = census.merge(df, on="BLOCKGROUP", how="outer")

census.rename(columns=variables, inplace=True)
numeric_cols = list(variables.values())
for col in numeric_cols:
    census[col] = pd.to_numeric(census[col], errors="coerce")

print(f"  Retrieved {len(census)} block groups from API")

# ---------------------------------------------------------------------------
# 4. Join and aggregate
# ---------------------------------------------------------------------------
merged = bg_district.merge(census, on="BLOCKGROUP", how="left")

summable = [
    "total_population", "race_total", "nh_white", "nh_black",
    "nh_american_indian", "nh_asian", "hispanic",
    "pop_16plus", "labor_force_civilian", "unemployed",
    "total_households", "family_households", "nonfamily_households",
]
median_vars = ["median_hh_income", "median_gross_rent", "median_home_value"]

for col in summable:
    merged[col + "_wtd"] = merged[col] * merged["share"]

merged["pop_weight"] = merged["total_population"] * merged["share"]

for mv in median_vars:
    merged.loc[merged[mv] < 0, mv] = pd.NA

agg_dict = {col + "_wtd": "sum" for col in summable}
agg_dict["pop_weight"] = "sum"

for mv in median_vars:
    merged[mv + "_num"] = merged[mv] * merged["pop_weight"]
    merged[mv + "_pop_valid"] = merged["pop_weight"].where(merged[mv].notna(), 0)
    agg_dict[mv + "_num"] = "sum"
    agg_dict[mv + "_pop_valid"] = "sum"

district = merged.groupby("DISTRICT").agg(agg_dict).reset_index()

for col in summable:
    district[col] = district[col + "_wtd"].round(0).astype(int)
    district.drop(columns=[col + "_wtd"], inplace=True)

for mv in median_vars:
    district[mv + "_est"] = (district[mv + "_num"] / district[mv + "_pop_valid"]).round(0).astype(int)
    district.drop(columns=[mv + "_num", mv + "_pop_valid"], inplace=True)

district.drop(columns=["pop_weight"], inplace=True)

# Derived columns
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

print("\nACS 2017-2021 results:")
print(district[["DISTRICT", "total_population", "median_hh_income_est"]].to_string(index=False))

# ---------------------------------------------------------------------------
# 5. Update district JSON files
# ---------------------------------------------------------------------------
print("\nUpdating district JSON files...")
data_dir = os.path.join(PROJECT_DIR, "src", "data", "districts")

for _, row in district.iterrows():
    dist_num = int(row["DISTRICT"])
    json_path = os.path.join(data_dir, f"district-{dist_num}.json")

    with open(json_path, "r") as f:
        dj = json.load(f)

    # Find the ACS 2017-2021 snapshot
    for snap in dj["demographics"]["snapshots"]:
        if snap["vintage"] == "ACS 2017-2021":
            snap["pull_date"] = "2026-04-02"
            snap["source"] = "U.S. Census Bureau ACS 5-Year via Census API (backfill_2021.py)"
            snap["data"] = {
                "total_population": int(row["total_population"]),
                "total_households": int(row["total_households"]),
                "pct_family_households": float(row["pct_family_households"]),
                "median_hh_income_est": int(row["median_hh_income_est"]),
                "median_gross_rent_est": int(row["median_gross_rent_est"]),
                "median_home_value_est": int(row["median_home_value_est"]),
                "unemployment_rate": float(row["unemployment_rate"]),
                "pct_nh_white": float(row["pct_nh_white"]),
                "pct_nh_black": float(row["pct_nh_black"]),
                "pct_hispanic": float(row["pct_hispanic"]),
                "pct_nh_asian": float(row["pct_nh_asian"]),
                "pct_nh_american_indian": float(row["pct_nh_american_indian"]),
                "pct_other": float(row["pct_other"]),
                "data_note": "Median income, rent, and home value are population-weighted averages of block-group medians \u2014 approximations, not true district medians. See /data/ for methodology."
            }
            break

    with open(json_path, "w") as f:
        json.dump(dj, f, indent=2, ensure_ascii=False)

    print(f"  Updated district-{dist_num}.json")

print("\nDone.")
