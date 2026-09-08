@AGENTS.md

# Conventions

## The four layouts move together

`src/*.liquid` are four copies of one template that differ only in the
knob block at the top (lines 1-40ish). Any edit below the
`---- derived ----` comment belongs in all four files, or the layouts
drift. Diff them against each other before committing:
`diff src/full.liquid src/quadrant.liquid` should show knobs only.

## Never commit real calendar ids

`CAL_MAP` in `src/*.liquid` and the fixture in `.trmnlp.yml` both ship
placeholder addresses (`you@gmail.com`, `abc123@group.calendar.google.com`).
The owner's real calendar ids are Google account identifiers — they belong in
the markup pasted into usetrmnl.com, never in this repo.

## Deploy is paste, not push

`trmnlp push` uploads `src/settings.yml`, whose `strategy` this repo sets
to a placeholder because trmnlp has no Plugin Merge strategy. Pushing
would replace the Plugin Merge plugin with a polling one. Deploy by
pasting each `src/*.liquid` into its markup tab on the site.

## Verify against the renderer, not just the linter

`trmnlp lint` checks TRMNL best practices; it does not prove the Liquid
produced anything. `scripts/check.sh` also greps the built HTML for
render errors and for at least one day header, because a Liquid failure
in trmnlp renders as body text with a zero exit code. Keep that assertion
in step with the template — if day headers stop being the reliable
marker, assert on whatever replaces them.

## Color tokens

Grayscale steps are the default on purpose (see the README gotcha on hue
collapse). Only reach for hue tokens (`bg--red`, `bg--blue`) once the
target device is confirmed to be a color panel, and keep the glyphs on as
the redundant channel either way.
