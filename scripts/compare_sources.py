#!/usr/bin/env python3
"""
Compare ACS 2023 5-year estimates (from build_district_profiles.py)
against Esri estimates (from Comparisons.xlsx → Columbus Districts sheet).

Outputs:
  - district_comparison.md   — markdown comparison table with variance flags
  - district_data.json       — JSON formatted for columbusdistricts.com
"""

import pandas as pd
import json
import math

# ---------------------------------------------------------------------------
# 1. Load both sources
# ---------------------------------------------------------------------------
acs = pd.read_csv("district_profiles.csv")

esri_raw = pd.read_excel("Comparisons.xlsx", sheet_name="Columbus Districts")

# Pivot Esri data: rows are variables, district columns are 1-9
# Build a dict of {variable_name: {district: value}}
esri = {}
for _, row in esri_raw.iterrows():
    name = row["NAME"]
    label = row["LABEL"]
    vals = {}
    for d in range(1, 10):
        vals[d] = row[d]
    esri[name] = {"label": label, "values": vals}

# ---------------------------------------------------------------------------
# 2. Define variable mappings: ACS column → Esri NAME
# ---------------------------------------------------------------------------
# We compare variables that exist in both sources.

comparisons = [
    # (display_label, acs_column, esri_name, type)
    # type: "count" for summable counts, "pct" for percentages, "median" for medians, "rate" for rates
    ("Total Population",        "total_population",    "POPCY",        "count"),
    ("Total Households",        "total_households",    "HHDCY",        "count"),
    ("NH White",                "nh_white",            "RCHCYWHNHS",   "count"),
    ("NH Black",                "nh_black",            "RCHCYBLNHS",   "count"),
    ("NH Asian",                "nh_asian",            "RCHCYASNHS",   "count"),
    ("NH American Indian",      "nh_american_indian",  "RCHCYAMNHS",   "count"),
    ("Hispanic",                "hispanic",            "HISCYHISP",    "count"),
    ("% NH White",              "pct_nh_white",        None,           "pct"),
    ("% NH Black",              "pct_nh_black",        None,           "pct"),
    ("% NH Asian",              "pct_nh_asian",        None,           "pct"),
    ("% Hispanic",              "pct_hispanic",        None,           "pct"),
    ("Median HH Income",        "median_hh_income_est","INCCYMEDHH",  "median"),
    ("Median Gross Rent",       "median_gross_rent_est","RNTEXMED",    "median"),
    ("Median Home Value",       "median_home_value_est","HOOEXMED",    "median"),
    ("Unemployment Rate",       "unemployment_rate",   "UNECYRATE",    "rate"),
    ("Family Households",       "family_households",   None,           "count"),
    ("Nonfamily Households",    "nonfamily_households",None,           "count"),
    ("% Family Households",     "pct_family_households",None,          "pct"),
]

# Compute Esri percentages for race so we can compare
# We'll add these as derived values
def esri_pct(name, total_name):
    """Return dict {district: pct} from esri counts."""
    result = {}
    for d in range(1, 10):
        total = esri[total_name]["values"][d]
        val = esri[name]["values"][d]
        if total and total > 0:
            result[d] = round(val / total * 100, 1)
        else:
            result[d] = None
    return result

esri_pct_white = esri_pct("RCHCYWHNHS", "POPCY")
esri_pct_black = esri_pct("RCHCYBLNHS", "POPCY")
esri_pct_asian = esri_pct("RCHCYASNHS", "POPCY")
esri_pct_hispanic = esri_pct("HISCYHISP", "POPCY")

# Esri family HH % (need to derive from Esri family makeup percentages)
# PCT_0020 through PCT_0025 are % of family households by type, but HHDCY is total HH
# We don't have a direct family_households count from Esri,
# so we'll skip comparisons where Esri doesn't have the variable.

# ---------------------------------------------------------------------------
# 3. Build comparison rows
# ---------------------------------------------------------------------------
FLAG_THRESHOLD = 5.0  # percent variance to flag

def pct_variance(acs_val, esri_val):
    """Compute % difference: (ACS - Esri) / Esri * 100."""
    if esri_val is None or acs_val is None:
        return None
    if esri_val == 0:
        return None if acs_val == 0 else float('inf')
    return (acs_val - esri_val) / abs(esri_val) * 100

def fmt_num(val, var_type):
    """Format a number for display."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "—"
    if var_type == "count":
        return f"{int(round(val)):,}"
    elif var_type == "median":
        return f"${int(round(val)):,}"
    elif var_type in ("pct", "rate"):
        return f"{val:.1f}%"
    return str(val)

rows = []

for label, acs_col, esri_name, var_type in comparisons:
    for d in range(1, 10):
        acs_val = acs.loc[acs["DISTRICT"] == d, acs_col].values[0]

        # Get Esri value
        esri_val = None
        if esri_name and esri_name in esri:
            esri_val = esri[esri_name]["values"][d]
        elif label == "% NH White":
            esri_val = esri_pct_white[d]
        elif label == "% NH Black":
            esri_val = esri_pct_black[d]
        elif label == "% NH Asian":
            esri_val = esri_pct_asian[d]
        elif label == "% Hispanic":
            esri_val = esri_pct_hispanic[d]

        variance = pct_variance(acs_val, esri_val)
        flag = ""
        if variance is not None and abs(variance) > FLAG_THRESHOLD:
            flag = " ⚠️"

        rows.append({
            "variable": label,
            "district": d,
            "acs_val": acs_val,
            "esri_val": esri_val,
            "variance_pct": variance,
            "flag": flag,
            "var_type": var_type,
        })

df = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# 4. Output markdown comparison tables — one per variable
# ---------------------------------------------------------------------------
print("Writing district_comparison.md ...")

lines = []
lines.append("# Columbus Council District Data Comparison")
lines.append("")
lines.append("**ACS 2023 5-Year Estimates** vs. **Esri Current-Year Estimates**")
lines.append("")
lines.append("> Variances >5% flagged with ⚠️. ACS median values are population-weighted")
lines.append("> block-group averages (approximations, not true medians).")
lines.append("")

# Group by variable
for label, acs_col, esri_name, var_type in comparisons:
    sub = df[df["variable"] == label]
    if sub["esri_val"].isna().all() and esri_name is None and label not in (
        "% NH White", "% NH Black", "% NH Asian", "% Hispanic"
    ):
        # ACS-only variable — no Esri comparison available
        lines.append(f"## {label}")
        lines.append("")
        lines.append("*No Esri equivalent — ACS only*")
        lines.append("")
        lines.append("| District | ACS 2023 |")
        lines.append("|:--------:|---------:|")
        for _, r in sub.iterrows():
            lines.append(f"| {r['district']} | {fmt_num(r['acs_val'], var_type)} |")
        lines.append("")
        continue

    lines.append(f"## {label}")
    lines.append("")
    lines.append("| District | ACS 2023 | Esri Est. | Variance |")
    lines.append("|:--------:|---------:|----------:|---------:|")
    for _, r in sub.iterrows():
        acs_str = fmt_num(r["acs_val"], var_type)
        esri_str = fmt_num(r["esri_val"], var_type)
        if r["variance_pct"] is not None:
            var_str = f"{r['variance_pct']:+.1f}%{r['flag']}"
        else:
            var_str = "—"
        lines.append(f"| {r['district']} | {acs_str} | {esri_str} | {var_str} |")
    lines.append("")

# Add summary of flagged items
flagged = df[df["flag"] != ""]
lines.append("## Noteworthy Variances (>5%)")
lines.append("")
if len(flagged) == 0:
    lines.append("No variances exceed 5%.")
else:
    lines.append(f"**{len(flagged)} comparisons** exceed the 5% variance threshold:")
    lines.append("")
    lines.append("| Variable | District | ACS 2023 | Esri Est. | Variance |")
    lines.append("|----------|:--------:|---------:|----------:|---------:|")
    for _, r in flagged.sort_values("variance_pct", key=abs, ascending=False).iterrows():
        acs_str = fmt_num(r["acs_val"], r["var_type"])
        esri_str = fmt_num(r["esri_val"], r["var_type"])
        var_str = f"{r['variance_pct']:+.1f}%"
        lines.append(f"| {r['variable']} | {r['district']} | {acs_str} | {esri_str} | {var_str} |")
    lines.append("")

md_text = "\n".join(lines)
with open("district_comparison.md", "w") as f:
    f.write(md_text)

# ---------------------------------------------------------------------------
# 5. Output JSON for columbusdistricts.com
# ---------------------------------------------------------------------------
print("Writing district_data.json ...")

districts_json = []
for d in range(1, 10):
    d_acs = acs[acs["DISTRICT"] == d].iloc[0]

    # Esri values for this district
    def ev(name):
        return esri[name]["values"][d] if name in esri else None

    district_obj = {
        "district": int(d),
        "demographics": {
            "population": {
                "acs_2023": int(d_acs["total_population"]),
                "esri_estimate": int(ev("POPCY")),
                "source_note": "ACS = Census ACS 2023 5-Year; Esri = Esri current-year estimate"
            },
            "race_ethnicity": {
                "nh_white": {
                    "count_acs": int(d_acs["nh_white"]),
                    "count_esri": int(ev("RCHCYWHNHS")),
                    "pct_acs": round(float(d_acs["pct_nh_white"]), 1),
                    "pct_esri": esri_pct_white[d],
                },
                "nh_black": {
                    "count_acs": int(d_acs["nh_black"]),
                    "count_esri": int(ev("RCHCYBLNHS")),
                    "pct_acs": round(float(d_acs["pct_nh_black"]), 1),
                    "pct_esri": esri_pct_black[d],
                },
                "nh_asian": {
                    "count_acs": int(d_acs["nh_asian"]),
                    "count_esri": int(ev("RCHCYASNHS")),
                    "pct_acs": round(float(d_acs["pct_nh_asian"]), 1),
                    "pct_esri": esri_pct_asian[d],
                },
                "nh_american_indian": {
                    "count_acs": int(d_acs["nh_american_indian"]),
                    "count_esri": int(ev("RCHCYAMNHS")),
                    "pct_acs": round(float(d_acs["pct_nh_american_indian"]), 1),
                },
                "hispanic": {
                    "count_acs": int(d_acs["hispanic"]),
                    "count_esri": int(ev("HISCYHISP")),
                    "pct_acs": round(float(d_acs["pct_hispanic"]), 1),
                    "pct_esri": esri_pct_hispanic[d],
                },
            },
            "households": {
                "total_acs": int(d_acs["total_households"]),
                "total_esri": int(ev("HHDCY")),
                "family_acs": int(d_acs["family_households"]),
                "nonfamily_acs": int(d_acs["nonfamily_households"]),
                "pct_family_acs": round(float(d_acs["pct_family_households"]), 1),
            },
        },
        "economics": {
            "median_household_income": {
                "acs_2023_est": int(d_acs["median_hh_income_est"]),
                "esri_estimate": int(ev("INCCYMEDHH")),
                "note": "ACS value is population-weighted average of block-group medians"
            },
            "median_gross_rent": {
                "acs_2023_est": int(d_acs["median_gross_rent_est"]),
                "esri_estimate": int(ev("RNTEXMED")),
                "note": "ACS value is population-weighted average of block-group medians"
            },
            "median_home_value": {
                "acs_2023_est": int(d_acs["median_home_value_est"]),
                "esri_estimate": int(ev("HOOEXMED")),
                "note": "ACS value is population-weighted average of block-group medians"
            },
            "unemployment_rate": {
                "acs_2023": round(float(d_acs["unemployment_rate"]), 1),
                "esri_estimate": round(float(ev("UNECYRATE")), 1),
            },
        },
        "variances": {},
    }

    # Compute and attach variances for this district
    var_entries = {}
    for label, acs_col, esri_name, var_type in comparisons:
        acs_val = d_acs[acs_col]
        esri_val = None
        if esri_name and esri_name in esri:
            esri_val = esri[esri_name]["values"][d]
        elif label == "% NH White":
            esri_val = esri_pct_white[d]
        elif label == "% NH Black":
            esri_val = esri_pct_black[d]
        elif label == "% NH Asian":
            esri_val = esri_pct_asian[d]
        elif label == "% Hispanic":
            esri_val = esri_pct_hispanic[d]

        if esri_val is not None and esri_val != 0:
            v = round((acs_val - esri_val) / abs(esri_val) * 100, 1)
            if abs(v) > FLAG_THRESHOLD:
                var_entries[label] = {
                    "variance_pct": v,
                    "acs": round(float(acs_val), 1),
                    "esri": round(float(esri_val), 1),
                    "flagged": True,
                }

    district_obj["variances"] = var_entries if var_entries else "none >5%"

    districts_json.append(district_obj)

with open("district_data.json", "w") as f:
    json.dump(districts_json, f, indent=2)

print("Done.")
print()

# Print a summary of flagged variances
print("=== FLAGGED VARIANCES (>5%) ===")
print()
for label, acs_col, esri_name, var_type in comparisons:
    sub = df[(df["variable"] == label) & (df["flag"] != "")]
    if len(sub) > 0:
        print(f"  {label}:")
        for _, r in sub.iterrows():
            print(f"    D{r['district']}: ACS={fmt_num(r['acs_val'], var_type)}"
                  f"  Esri={fmt_num(r['esri_val'], var_type)}"
                  f"  ({r['variance_pct']:+.1f}%)")
        print()
