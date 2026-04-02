# Display Conventions: Columbus Districts Demographic Data

This document establishes the research-informed conventions for presenting demographic data on the Columbus Districts website. These guidelines ensure consistency, clarity, and appropriate context for all users interpreting the data.

## 1. Primary vs. Supplemental Data Sources

### ACS Estimates as Primary Figures
The American Community Survey (ACS) 5-year estimates are displayed as the primary demographic figures throughout the site.

**Rationale:** ACS 5-year estimates are the Census Bureau standard for sub-county demographic analysis. They provide:
- Established reliability and transparency
- Wide adoption by researchers, planners, and civic institutions
- Published margins of error for all categories
- Consistency with other municipalities and regional analyses
- Stability from reduced year-to-year sampling variability

**Display convention:** ACS figures appear as the main statistic on district pages and are introduced as "ACS estimate" with vintage labeling (e.g., "ACS 2019-2023 estimate").

### Esri Estimates as Supplemental Comparison
Esri current-year estimates appear alongside ACS figures on district pages where available, clearly labeled as "Esri Current-Year Estimate" with pull date.

**Rationale:** Esri estimates provide a supplemental forward-looking view:
- Esri applies proprietary estimation models to 2020 Census baseline
- Current-year estimates incorporate building permits and IRS migration data
- The contrast between backward-looking (ACS) and forward-looking (Esri) enriches user understanding
- Users can see both the 5-year survey average and the latest projection

**Display convention:** When both ACS and Esri are available, Esri appears as a secondary comparison with clear labeling of pull date (e.g., "Esri Current-Year Estimate, pulled [date]").

## 2. Margin of Error Handling

### MOE Not Displayed on District Pages
Margins of Error are not surfaced on individual district pages.

**Rationale:**
- At the population sizes of Columbus's nine districts (~100,000 residents each), ACS 5-year estimates for major demographic categories (total population, race/ethnicity, household income) have acceptable reliability without MOE display
- Showing MOE on every figure would reduce readability without proportional value for civic use
- Users accessing the data for civic engagement or planning typically need point estimates, not statistical confidence intervals
- Showing MOE on some figures but not others would create inconsistency

### MOE Available on Methodology Page
The `/data/` methodology page:
- Explains that all ACS figures carry margins of error
- Provides the formula for calculating confidence intervals (point estimate ± margin of error)
- Links to Census Bureau guidance for users who need to evaluate estimate reliability
- References the Census Bureau's ACS reliability handbook

**Display convention:** District pages include a link to the methodology page with the phrase "All ACS estimates carry margins of error. See /data/ for methodology and guidance."

## 3. Aggregation Disclaimer

### Standard Data Note on Every District Page
Each district page's demographics section includes the following data note:

> "Median income, rent, and home value are population-weighted averages of block-group medians — approximations, not true district medians. See /data/ for methodology."

**Rationale:**
- Users commonly misinterpret aggregated median values as true district-level medians
- ACS data is collected at the block-group level; district-level medians are created by weighting block-group medians by population
- This is a defensible approximation but is not equivalent to calculating the true median from individual household data
- Transparency about this limitation is essential for correct interpretation

**Display convention:** This disclaimer appears in a data_note field on every district page where median income, rent, or home value is displayed.

## 4. Vintage Labeling

### Consistent Vintage Labels on All Data
Every demographic figure is labeled with its ACS vintage (e.g., "ACS 2019-2023") and the pull date (e.g., "pulled January 15, 2026").

**Rationale:**
- Users must always know the exact time period the data represents
- ACS vintage indicates the survey period (5 years of data collection)
- Pull date indicates when the data was retrieved from Census Bureau
- This metadata prevents confusion when multiple ACS vintages are available
- Pull date is important for Esri data, which is snapshot-based

**Display convention:**
- ACS vintage: "ACS 2019-2023 estimate"
- Pull date: Included in the data source attribution, e.g., "ACS 2019-2023 (pulled January 15, 2026)" or "Esri Current-Year Estimate (pulled January 15, 2026)"

## 5. ACS vs. Esri Distinction Language

### Standard Framing for Both Data Sources
When both ACS and Esri are presented, the site uses this standard explanatory language:

> "ACS estimates are 5-year averages based on survey data collected from [start year] to [end year]. Esri estimates are current-year projections derived from the 2020 Census, updated with building permits and IRS migration data."

**Variations by context:**

**For total population comparisons:**
> "ACS provides a 5-year backward average of population survey data (2019-2023). Esri provides a current-year projection incorporating 2020 Census baseline, updated with building permits and recent IRS migration data. The difference between the two reflects both this time lag and differences in estimation methodology."

**For income, rent, and home value:**
> "ACS figures are population-weighted averages of block-group medians from the 5-year survey period (2019-2023). Esri figures are current-year estimates using proprietary models. Differences may reflect both the time lag and methodological differences in how medians are estimated."

**For race/ethnicity:**
> "ACS uses Census Bureau definitions from the decennial Census replication in the 5-year survey. Esri applies current-year estimation models. Small populations may show larger percentage differences due to estimation differences and classification methodology."

**Rationale:**
- These explanations contextualize the data without overwhelming users
- They acknowledge both temporal and methodological differences
- They position both sources as valid for different purposes (survey average vs. projection)
- They prepare users to expect variance without suggesting error

**Display convention:** This framing appears on the `/data/` methodology page and is referenced from individual district pages via a data tooltip or link.

## 6. Special Cases and Documentation

### High-Growth Districts with Large Temporal Variance
Districts with significant variance between ACS and Esri (e.g., D2 +38.4%, D5 +21.9%, D6 +14.0%) include an additional note:

> "District population increased significantly during the ACS survey period. ACS 2019-2023 reflects a 5-year average; Esri reflects current-year projection. This difference is expected in areas of active development."

**Display convention:** This note appears as a tooltip or expanded data note on affected district pages.

### American Indian Population Classification Difference
The American Indian population counts show systematic Esri > ACS across all districts due to classification methodology. The methodology page explains:

> "Esri's American Indian counts include individuals who selected American Indian as one of their races (including multiracial individuals). ACS Table B03002 counts only individuals who identify as Non-Hispanic American Indian alone. Both figures are valid for their respective purposes; they reflect different classification approaches rather than data discrepancies."

**Display convention:** This explanation appears on the `/data/` methodology page and may be referenced via a data note if American Indian population is displayed on a district page.

### Items Under Investigation
Until investigation is complete (see `data_notes.md` Bucket 3), the following variances should include a caveat if displayed:

- **D3 Asian population variance (-59.5%):** If displayed, include: "This figure is being reviewed for data validation. See /data/ for details."
- **D3 Black population variance (-33.5%):** If displayed, include: "This figure is being reviewed for data validation. See /data/ for details."
- **D2 population anomaly (+38.4%):** If displayed, include: "This figure is being reviewed for data validation. See /data/ for details."

**Display convention:** These figures are displayed with a caveat note until investigation is complete and documented.

## Implementation Checklist

- [ ] All demographic figures on district pages labeled with ACS vintage and pull date
- [ ] All Esri supplemental figures clearly labeled with "Esri Current-Year Estimate" and pull date
- [ ] Standard aggregation disclaimer present on all district pages displaying median income, rent, or home value
- [ ] Link to `/data/` methodology page present on every district demographics section
- [ ] Standard ACS vs. Esri framing language used consistently across all pages and tooltips
- [ ] High-growth district notes added to D2, D5, D6, D8, D9
- [ ] American Indian classification difference documented on methodology page
- [ ] Investigation caveats applied to D2, D3 Asian, D3 Black until investigation is complete
- [ ] MOE guidance and Census Bureau links present on methodology page
- [ ] All data sources and pull dates documented in site metadata/footer
