# Columbus Districts — Maintenance Cadence

Post-launch recurring tasks for keeping the site current. All content updates are JSON file edits followed by a `git push` — Netlify auto-deploys within ~60 seconds.

---

## Quarterly

- **Council member verification:** Check all nine council member names, committee assignments, and contact info against the [official directory](https://www.columbus.gov/Government/City-Council/Directory). Update `councilMember` objects in the relevant district JSON files.
- **External link check:** Test all external links — area commission sites go down; council bio URLs change after reorganizations.
- **Form submissions:** Review Suggest an Edit and Name the Districts submissions in the Netlify dashboard.
- **CrimeRisk data:** Check whether Applied Geographic Solutions has published updated CrimeRisk data. If so, update `crimeRisk` blocks and `pull_date` in each district JSON.

## Annually — December (ACS Release Month)

The Census Bureau releases new ACS 5-year data each December. The next expected release is ACS 2020-2024, due December 2026.

When new ACS data releases:

1. Pull a fresh Esri export — update `Comparisons.xlsx` with current Esri estimates. Record the pull date in the file.
2. Update the vintage year in `build_district_profiles.py` (the `BASE_URL` variable).
3. Run `python scripts/build_district_profiles.py` — produces `district_profiles.csv`.
4. Run `python scripts/compare_sources.py` — produces `district_comparison.md` and `district_data.json`.
5. Review `district_comparison.md` for new or resolved variance flags — update `scripts/data_notes.md`.
6. Add a new snapshot object to each district JSON file for the new vintage; populate from `district_data.json`.
7. Update `current_vintage` in all nine district JSON files to the new vintage string.
8. Update the vintage history table on the `/data/` page (`src/pages/data.astro`).
9. Commit: `git commit -m "Demographics update — ACS [vintage] — [date]"`
10. Push to main — live within 60 seconds.

**Esri note:** Always take a fresh Esri export at the same time as the ACS pull. Do not reuse an old `Comparisons.xlsx` — Esri's numbers change on their own schedule.

## After Each November General Election

- Update `src/data/elections.json` with results (source: Franklin County BOE).
- Update affected district JSON files: `councilMember` object (name, `firstElected`, `termEnds`, `nextElection`).
- In January after council reorganization: update `committees` in affected district JSON files.

**Next election:** November 2027 (Districts 2, 5, 6, 8, 9).

---

## Content Update Workflows

### Update a council member

1. Open `src/data/districts/district-N.json`
2. Edit the `councilMember` object fields
3. Commit and push

### Add a Point of Interest

1. Open the relevant district JSON file
2. Add a new object to `pointsOfInterest` array with `name`, `url`, and `description`
3. Commit and push

### Add election results

1. Open `src/data/elections.json`
2. Add a new election cycle object with results
3. Commit and push

### Update demographics (new ACS vintage)

Follow the annual December pipeline above, then:
1. Add new snapshot to each district JSON (do not delete old snapshots)
2. Update `current_vintage` pointer
3. Update `/data/` vintage history table
4. Commit and push
