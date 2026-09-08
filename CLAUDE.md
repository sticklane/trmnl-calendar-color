@AGENTS.md

# Conventions

## src/*.liquid are generated — never edit them

`scripts/layout_body.liquid` is the template and the `LAYOUTS` table in
`scripts/gen_layouts.py` holds the per-layout knobs. Change one of those,
run `python3 scripts/gen_layouts.py`, commit the regenerated files.
`scripts/check.sh` runs `gen_layouts.py --check` first and fails if the
tree disagrees.

## Never commit real calendar ids

The fixture and the fallbacks ship placeholder addresses
(`you@gmail.com`, `shared@group.calendar.google.com`). The owner's real
calendar ids are Google account identifiers. They now live in the
plugin's `cal_map` custom field on usetrmnl.com, not in markup at all —
which is the point of that field. Never write one into this repo, and
never print one into a transcript.

## Deploy is paste, not push

`trmnlp push` uploads `src/settings.yml`, whose `strategy` this repo sets
to a placeholder because trmnlp has no Plugin Merge strategy. Pushing
would replace the Plugin Merge plugin with a polling one. Deploy by
pasting each `src/*.liquid` into its markup tab on the site.

## Colour tokens are the device's four inks

`black`, `white`, `red`, `yellow`. Everything else — grey steps, other
hues, opacity — is dithered into speckle on the OG B/W/R/Y panel and
reads as fuzz. `check.sh` greps for greys, `rgba(`, `opacity:` and
fractional pixel offsets and fails on any of them.

## Verify against the renderer, not just the linter

`trmnlp lint` checks TRMNL best practices; it does not prove the Liquid
produced anything. `scripts/check.sh` also greps the built HTML, because a Liquid failure in
trmnlp renders as body text with a zero exit code. It asserts that the
output is a grid and not a list: an hour axis, one grid column per day
with today highlighted, the day math advancing, all-day band entries, and
event blocks whose `top`/`height` differ from one another (proving they
are placed from the clock rather than stacked). It builds the fixture twice, once per `axis_mode`, and asserts nothing
outside the day window leaks in. `scripts/geometry_check.py` then asserts
that each block's rendered spans equal that event's full
`start - end  title`, that a title ending in an ellipsis was genuinely
longer than its width, that each block sits at its clock top and covers
its duration, that a nested block is indented one step per event still
running, that no block covers another block's text, that
every in-window fixture event is either drawn or counted into a
"+N more", and that the hour range and its first and last labels match
what `axis_mode` should have produced.

Keep those assertions in step with the template. The fixture is built to
falsify them: an out-of-window event on either side, a five-minute event,
three back-to-back fifteen-minute events, a nine-hour block, and a
four-hour block under a stack of short ones.
