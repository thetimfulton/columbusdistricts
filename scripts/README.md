# Columbus Districts Data Pipeline

Scripts for pulling, aggregating, and comparing demographic data for the nine Columbus City Council residential districts.

## Scripts

### `build_district_profiles.py`

Pulls ACS 5-Year estimates at the block-group level from the Census Bureau API, then aggregates them to council districts using a block-group-to-district crosswalk.

**Inputs:**
- `CensusBlock2020_with_CouncilDistrict2023.xlsx` — Block-level crosswalk mapping Census blocks/block groups to council districts. Must be in the working directory.
- Census API key (hardcoded in script as `API_KEY`; replace with your own key from [api.census.gov](https://api.census.gov/data/key_signup.html) if needed).

**Output:**
- `district_profiles.csv` — One row per district with population, household, racial/ethnic composition, income, rent, home value, and unemployment figures.

**How to run:**
```bash
python build_district_profiles.py
```

**Notes:**
- The `BASE_URL` variable controls which ACS vintage is queried (currently `https://api.census.gov/data/2023/acs/acs5`). To pull a new vintage, update the year in this URL (e.g., change `2023` to `2024`).
- Aggregation uses block-group share weighting: when a block group spans multiple districts, the script computes each district's share based on the number of child blocks assigned to that district.

### `compare_sources.py`

Compares the ACS estimates produced by `build_district_profiles.py` against Esri current-year demographic estimates, flagging significant variances.

**Inputs:**
- `district_profiles.csv` — Output from `build_district_profiles.py`. Must be in the working directory.
- `Comparisons.xlsx` — Esri current-year estimates export. Must be in the working directory with a sheet named "Columbus Districts."

**Outputs:**
- `district_comparison.md` — Markdown table showing ACS vs. Esri values for each variable and district, with variance percentages and flags for discrepancies exceeding thresholds.
- `district_data.json` — Structured JSON with demographics, economics, and variance data per district, formatted for use on columbusdistricts.com.

**How to run:**
```bash
python compare_sources.py
```

## When to Re-Run

Re-run this pipeline each December after the Census Bureau releases a new ACS 5-Year vintage. The typical schedule:

1. **December:** Census Bureau publishes the new ACS 5-Year release (e.g., ACS 2020-2024 expected December 2026).
2. **Same time:** Pull a fresh Esri export — update `Comparisons.xlsx` with current Esri estimates. Record the pull date.
3. Update the vintage year in `build_district_profiles.py` (the `BASE_URL` variable).
4. Run `build_district_profiles.py` to produce a new `district_profiles.csv`.
5. Run `compare_sources.py` to produce updated `district_comparison.md` and `district_data.json`.
6. Review `district_comparison.md` for new or resolved variance flags.
7. Add a new snapshot to each district JSON file in `/src/data/districts/`; update `current_vintage`.
8. Commit and push — site rebuilds automatically via Netlify.

## Esri Input Notes

`Comparisons.xlsx` must be a fresh export taken at the same time as the ACS pull. Esri current-year estimates update on their own schedule (typically mid-year), so the pull date matters. To obtain a fresh export:

- Source: Esri Demographics data via ArcGIS Business Analyst or Community Analyst
- Export the "Columbus Districts" comparison report covering the nine council district geographies
- Save as `Comparisons.xlsx` in the working directory

Do not reuse an old `Comparisons.xlsx` when running a new ACS vintage — the Esri numbers will have changed.

## Dependencies

```
pip install pandas requests openpyxl
```
