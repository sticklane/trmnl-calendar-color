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
produced anything. `scripts/check.sh` also greps the built HTML, because a Liquid failure in
trmnlp renders as body text with a zero exit code. It asserts that the
output is a grid and not a list: an hour axis, one grid column per day
with today highlighted, the day math advancing, all-day band entries, and
event blocks whose `top`/`height` differ from one another (proving they
are placed from the clock rather than stacked). It also asserts that two
9:00 events lane side by side, and that nothing outside the day window
leaks in. `scripts/geometry_check.py` then parses every block rectangle
and fails if any two in a column intersect, or if an hour label is
anything but a clean `\d{1,2}[ap]`.

Keep those assertions in step with the template. The fixture is built to
falsify them: an out-of-window event on either side, and a Tuesday
cluster of a long block plus a stack of overlapping ones that only lanes
correctly under a real sweep.

## Color tokens

Grayscale steps are the default on purpose (see the README gotcha on hue
collapse). Only reach for hue tokens (`bg--red`, `bg--blue`) once the
target device is confirmed to be a color panel, and keep the glyphs on as
the redundant channel either way.
