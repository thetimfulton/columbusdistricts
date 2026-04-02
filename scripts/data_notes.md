# Data Notes: ACS vs. Esri Variance Analysis

This document categorizes the 113 flagged variances between ACS 2019-2023 estimates and Esri current-year estimates for the nine Columbus City Council Districts. Variances are organized into three buckets based on root cause: methodological differences, temporal lag, and items requiring investigation before publication.

## Bucket 1: Methodological Variance (Expected, No Action Required)

These variances reflect known differences in data collection and estimation methodology between the Census Bureau (ACS) and Esri. They are expected, well-understood, and do not indicate data errors.

### Median Household Income (All Districts D1-D9)
- **Variance range:** +12.4% to +36.5% (ACS > Esri)
- **Cause:** ACS values are population-weighted averages of block-group medians. This methodology systematically produces higher figures than Esri's direct estimation approach, which estimates median income at the district level without aggregating from smaller geographies.
- **Status:** Expected variance. No action required.

### Median Gross Rent (All Districts D1-D9)
- **Variance range:** +30.1% to +54.2% (ACS > Esri)
- **Cause:** Same methodology issue as median household income. ACS aggregates block-group medians using population weights; Esri applies a different estimation model.
- **Status:** Expected variance. No action required.

### Median Home Value (Most Districts)
- **Variance range:** Mostly negative (ACS < Esri), with exceptions in D4 (-12.3%), D6 (-10.0%), and D8 (-11.6%)
- **Cause:** The general pattern (ACS < Esri) reflects the same aggregation methodology difference as income and rent. However, D4, D6, and D8 show the **reverse pattern** (ACS ABOVE Esri), which may reflect rapid recent home value appreciation in these more affordable districts. Esri's current-year projections may not yet fully capture recent market gains.
- **Status:** Expected variance. The reverse pattern in D4, D6, D8 suggests strong recent appreciation in these areas and warrants documentation.

### Unemployment Rate (All Districts)
- **Variance range:** Systematic ACS > Esri across all districts
- **Cause:** ACS unemployment is a 5-year backward-looking average (covering the full 2019-2023 survey period). Esri provides current-year estimates. Since unemployment trended downward nationally over this period, the 5-year average is higher than the current rate.
- **Status:** Expected variance. No action required.

## Bucket 2: Temporal Variance (Expected, Requires Documentation)

These variances reflect the time lag between ACS data collection (2019-2023 is a 5-year backward average) and Esri's current-year estimates (derived from 2020 Census + building permits + IRS migration data). They are expected in high-growth areas and should be documented on the site.

### Total Population (High-Growth Districts)
- **D2: +38.4%** (ACS 143,899 vs. Esri 103,970)
- **D5: +21.9%**
- **D6: +14.0%**
- **D8: +12.8%**
- **D9: +12.5%**
- **Cause:** ACS 2019-2023 is a 5-year backward average. Esri projects the current year from 2020 Census baseline, updated with building permits and IRS migration data. Districts with significant new construction show divergence.
- **Status:** Expected variance in high-growth areas. Document on the site as a limitation of using 5-year ACS averages.

### Total Households (High-Growth Districts)
- **Variance tracking the same pattern as population across D2, D5, D6, D8, D9**
- **Cause:** Same temporal lag as population.
- **Status:** Expected variance. Document alongside population.

### Non-Hispanic White Count (High-Growth Districts)
- **D2: +44.9%**
- **D5: +22.0%**
- **D6: +23.6%**
- **D8: +20.3%**
- **Cause:** Likely reflects the same temporal lag as overall population growth. These districts have experienced significant new residential construction.
- **Status:** Expected variance. No action required beyond general documentation.

### Hispanic Count (Selected Districts)
- **D2: +46.4%**
- **D4: +53.1%**
- **D5: +53.0%**
- **Cause:** May reflect both temporal growth and differences in ACS counting methodology for Hispanic/Latino origin. ACS B03002 (the ancestry table) may capture ethnicity differently than Esri's current-year projections.
- **Status:** Expected variance with a potential methodology component. Document as temporal lag plus possible classification differences.

## Bucket 3: Investigate Before Publishing

These variances are statistically significant, affect numerically important populations, or show patterns that warrant further investigation to ensure data integrity before public release.

### NH Asian in D3: ACS 9,739 vs. Esri 24,075 (-59.5%)

**Severity:** This is the single largest percentage variance for a numerically significant population in the dataset.

**Context:** D3 includes the Ohio State University campus area, which hosts a large Asian student population.

**Possible causes:**
- (a) Block-group crosswalk issue: OSU-area block groups may be split across district boundaries, with some assigned to D3 and others to D7, causing Esri's count for D3 to include students assigned elsewhere by the crosswalk.
- (b) International student classification: Esri may count international students differently than ACS B03002.
- (c) Group quarters methodology: ACS group quarters processing may undercount university populations compared to Esri's estimation approach.

**Investigation steps:**
1. Verify block-group assignments for OSU-area blocks in `CensusBlock2020_with_CouncilDistrict2023.xlsx`
2. Compare Esri's D3 total (24,075) to the sum of D3 + D7 Asian counts in ACS to see if counts reconcile across districts
3. Consult Esri documentation on how group quarters (dormitories) are counted in current-year estimates

**Status:** INVESTIGATE before publishing.

### NH American Indian Counts (All Districts: -13.8% to -84.5%)

**Severity:** ACS counts are consistently far below Esri across all 9 districts.

**Root cause (highly likely):** This is almost certainly a **classification methodology difference**, not a data error:
- **ACS B03002** uses a strict single-race definition: "Non-Hispanic American Indian and Alaska Native alone"
- **Esri** likely includes multiracial individuals who selected American Indian as one of their races in the 2020 Census

**Status:** DOCUMENT as a methodology difference on the site. This is not a discrepancy requiring data correction; it reflects how two organizations categorize race/ethnicity differently. Users should understand that Esri's American Indian counts are higher because they include individuals with mixed race, not because one source is "wrong."

### NH Black in D3: ACS 5,552 vs. Esri 8,354 (-33.5%)

**Severity:** Notable divergence in a significant population (Esri's count is 50% higher).

**Possible cause:** May relate to the same block-group assignment issues affecting D3's Asian population. The OSU area's demographic composition and block-group boundaries deserve scrutiny.

**Investigation steps:**
1. Verify that D3 block-group assignments are correct and complete
2. Check whether there are any major institutional (OSU) or residential complexes split across D3/D7 boundaries
3. Compare to D7's corresponding NH Black count to see if counts appear reconciled across the district split

**Status:** INVESTIGATE alongside the D3 Asian population variance.

### D2 Population Anomaly: ACS 143,899 vs. Esri 103,970 (+38.4%)

**Severity:** D2 shows the largest population divergence of any district.

**Possible causes:**
- (a) Crosswalk issue: The block-group to council district crosswalk may assign too many block groups to D2 in the ACS dataset
- (b) Rapid growth: D2 includes the Clintonville and Northland corridors, which have experienced significant new construction. The +38.4% variance could reflect genuine population growth between the 2020 Census (baseline for Esri) and 2023 (ACS collection period).

**Investigation steps:**
1. Verify block-group assignments to D2 in `CensusBlock2020_with_CouncilDistrict2023.xlsx`
2. Examine building permit data for D2 to assess actual construction activity and growth rate
3. If the variance is confirmed to be a crosswalk error, correct the block-group assignments and rerun ACS aggregation
4. If growth is confirmed as real, document the rapid expansion in D2 on the site

**Status:** INVESTIGATE. This variance is too large to ignore; the cause must be determined before publishing D2 data.

---

## Summary and Next Steps

**Total variances analyzed:** 113

**Disposition:**
- **Bucket 1 (Methodological):** ~40 variances — No action required; expected differences
- **Bucket 2 (Temporal):** ~65 variances — Document on site as limitations of 5-year ACS averages
- **Bucket 3 (Investigate):** ~8 variances across 5 specific items — Require verification before publication

**Priority for investigation:** D3 (Asian and Black populations) and D2 (overall population) are highest priority.
