# Design concepts — Columbus Districts

Approved visual system and page mockups (August 2026). These are the **source of truth** for
the Astro build. Each `.html` is a self-contained, static concept (open it in a browser; it has
light + dark, hover the maps, toggle theme with the sun icon top-right). Nav links and forms are
stubs — these are design references, not the app.

## Files
- `design-system.css` — tokens (color, type, spacing), base styles, header/footer, buttons,
  cards, data-viz primitives, and the light/dark theme system. Split this into
  `src/styles/global.css` + per-component styles.
- `home.html` — homepage: interactive nine-district map hero + district grid + ballot band.
- `district-one-concept.html` — the district page template (District 1 shown). The richest page:
  map, civic snapshot, council card, demographics as data-viz, Public Safety (crime vs. city),
  Get Involved.
- `ballot.html` — the new 2026 ballot explainer (hybrid vs. single-member, timeline, pro/con).
- `all-districts.html` — comparison table + Columbus row + superlatives.
- `data.html` — Data & Trends: dumbbell change charts + methodology.
- `how-it-works.html` — plain-language explainer of the current system.

## Design language
- **Type:** Newsreader (editorial serif) + Public Sans (US civic sans), via Google Fonts.
- **Palette:** warm paper ground · deep "Scioto" slate blue `#233B54` · Columbus-scarlet accent
  `#C13B2A` · gold micro-accent. Full light + dark.
- **Maps:** real CivicWorth council boundaries, rendered as inline SVG at high fidelity
  (`ST_SimplifyPreserveTopology ≤ 0.00012` — never coarser; coarse simplification straightens
  the jagged annexed city limits).
- **Data:** shown as visuals (change chips, rank/position strips, dumbbells, vs-city bars) with a
  consistent "compared to Columbus" framing, not bare tables.

See `../CLAUDE.md` and `../columbusdistricts_implementation_brief.md` for the build plan.
