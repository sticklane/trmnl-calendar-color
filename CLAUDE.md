@AGENTS.md

# Conventions

## src/*.liquid are generated — never edit them

`scripts/layout_body.liquid` is the template and the `LAYOUTS` table in
`scripts/gen_layouts.py` holds the per-layout knobs. Change one of those,
run `python3 scripts/gen_layouts.py`, commit the regenerated files.
`scripts/check.sh` runs `gen_layouts.py --check` first and fails if the
tree disagrees.

## Two views, one body

`scripts/agenda_body.liquid` is the agenda render. `gen_layouts.py`
splits `layout_body.liquid` at its first `<style>` and emits the derived
section, then `{% if MODE == "agenda" %}` agenda `{% else %}` grid.
Anything both views need (colours, labels, quiet calendars, `today`)
belongs above that `<style>`; `scripts/agenda_check.py` is the agenda's
gate and `specs/agenda.md` its spec.

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

A black-and-white device takes `cal_map_bw`, greys only. The number is
the lightness, measured in the framework's 1-bit tiles: `gray-40` and
up carry black text, `gray-35` and down white. It reaches the
render as CSS scoped to `.screen--1bit,.screen--2bit` (class `cg-cal-N`
per calendar) because the render cannot tell its device. `check.sh`
asserts those rules name greys and never a hue; the markup's own tokens
still never include a grey.

Blends are allowed as event fills: `orange` (a red-and-yellow tile),
`pink` (a red-and-white tile), and the `-45`..`-75` tints of red, yellow,
orange and pink (the hue's dots on a white ground). All of those are
light, so the template's `LIGHT_FILLS` list gives them black text. Keep
the fixture's `cal_map` using blends so the render proves that rule.

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
running, that no block covers another block's text, that the 10px face
appears only where 12px text could not fit the event's minutes, that
every in-window fixture event is either drawn or counted into a
"+N more", and that the hour range and its first and last labels match
what `axis_mode` should have produced.

Keep those assertions in step with the template. The fixture is built to
falsify them: an out-of-window event on either side, a five-minute event,
three back-to-back fifteen-minute events, a nine-hour block, and a
four-hour block under a stack of short ones.
