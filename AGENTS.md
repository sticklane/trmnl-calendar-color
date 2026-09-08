# trmnl-calendar-color

Four TRMNL Liquid templates that render a **3 Day Week time grid** —
hours down the left axis, one column per day starting today, every timed
event a filled block carrying its start time, end time and title in
full — colour-coded by which calendar it came from. They run as a TRMNL **Private Plugin with
strategy Plugin Merge**, reading the merge variable a native Google
Calendar plugin instance publishes. There is no application code and no
data layer here — TRMNL's own plugin fetches the events; these templates
only render them.

## Map

| path | what |
|---|---|
| `scripts/layout_body.liquid` | THE template. Everything below the knobs |
| `scripts/gen_layouts.py` | writes the four `src/*.liquid` from that body plus a knob table |
| `src/*.liquid` | generated: full, half_horizontal, half_vertical, quadrant |
| `src/settings.yml` | plugin metadata and the custom-field schema |
| `.trmnlp.yml` | local-preview fixture that stands in for the merge variable |
| `bin/trmnlp` | gem-or-Docker wrapper for the `trmnlp` CLI |
| `scripts/check.sh` | the canonical check |
| `scripts/geometry_check.py` | asserts every block sits at its clock position, holds its full text, and covers no other text |
| `reference/native-3day/` | what the native render exposes, and the settings it came from |

The framework title bar is gone: it spent ~44px on a name and an icon.
A one-line legend (swatch plus calendar name, 18px) replaces it, and the
reclaimed height goes to the grid.

**`trmnlp lint` scans all four layouts for eight CSS property names and
allows six hits across the set** - comments included, since it is a plain
substring scan (`lib/trmnlp/lint/checks/limited_inline_styles.rb`). That
is why block geometry is emitted as a generated stylesheet keyed on
`.cg-bN` rather than a style attribute per block, and why this repo
reaches for utility classes over hand-written spacing.

`src/*.liquid` are GENERATED. Edit `scripts/layout_body.liquid` or the
`LAYOUTS` table in `scripts/gen_layouts.py`, then run the script;
`scripts/check.sh` fails if the tree disagrees. Four hand-maintained
copies is how they drifted.

Colours and the axis mode are the plugin's own custom fields
(`cal_map`, `default_color`, `axis_mode`), declared in `src/settings.yml`
and edited on the plugin's settings page. The values in the markup are
only the empty-field fallback.

The knobs mirror the native Google Calendar instance's own display
settings, so the private plugin and the native one agree: `NUM_DAYS = 3`
for its `three_day_week` layout, `DAY_FMT` for `date_format: short`, and
`HIGHLIGHT_TODAY` / `MARK_WEEKENDS` for its matching toggles. Event times
print straight from `ev.start`, which the native plugin has already
formatted with its `time_format`, so the clock style needs no knob.

`axis_mode` picks the hour range. `fit` (default) runs from the whole
hour before the earliest timed event in view to the whole hour after the
latest one ends, each end rounded outward and clamped to midnight
independently; events shorter than `MIN_AXIS_DUR` (5 minutes) and all-day
events never move it.  `day` is 00:00-24:00.

**The window is a hard constraint and the PITCH gives way.** `HOUR_H` is
the budget divided by the hours the window spans, capped above by
`HOUR_H_MAX` and floored only at 1px - there is no comfortable minimum,
because a minimum would push the last hour off the panel. The window end
is always labelled, one line inside the grid, and labels thin out
automatically (`HOUR_EVERY` rises) so two are never closer than one line.

`GRID_BUDGET_H` is a px budget, not the height: `HOUR_H` is that budget
divided by the hours on the axis, clamped to `HOUR_H_MIN..HOUR_H_MAX`,
and the real `GRID_H` is `HOUR_H * HOURS`. Pinning `HOUR_H` instead is
what broke the live render on 2026-09-07: 24px times an 18-hour axis
overflowed the panel, and TRMNL centres an overflowing view, so the day
headers went off the top. `scripts/check.sh` now reads `data-grid-h` back
out of the built HTML and fails if it exceeds the layout's budget.

**Placement follows the native render.** Every block sits at its clock
position and spans its whole duration. A block that starts before an
earlier block ends, by the clock, is nested: it is indented `INDENT_W`
per such block, up to `MAX_DEPTH` steps, and painted over it, because
later blocks come later in the column. That is how the native 3 Day
Week render cascades overlapping events (`reference/native-3day/NOTES.md`).
Depth counts clock overlap, not box overlap, so a block drawn taller
than its minutes to hold its text does not turn the back-to-back block
after it into a nested one. The earlier model, which slid a colliding
block DOWN to the next free pixel, lost the clock: nine events inside
one 7:30-4:30 "Busy" landed hours late.

**One rule is ours: no block covers another block's text.** A block
starts no higher than the text bottom of any drawn box that reaches
below its clock top. Two events that start at the same minute therefore
sit one line apart instead of on top of each other, and a burst of
short events chains down by one line each. The native render paints
them over each other and loses the covered text.

**Readability still decides the height and the width.** A block is at
least as tall as its text: one line when `Title  start-end` fits the
width left after the indent, two otherwise. A title is shortened only
when the title alone exceeds that width. Each indent step costs
`INDENT_CHARS`, derived from `INDENT_W` and the 6.65px character. What
no longer fits above the fold becomes "+N more" rather than smaller
type.

**Text.** The title leads: `Title  h:mm-h:mm` on one line when it fits,
otherwise the title on line one and the times on line two. When the
column has room for one more line but not two the TIMES are dropped - the
title is shortened only when the title alone is wider than the column.

The face is `label--small`, which is the framework's 12px pixel-hinted
bitmap (TRMNL12, 12px line height, 6.65px per character, measured in the
live preview). `label--xsmall` is an ALIAS of the 16px face (TRMNL16,
8.5px per character), not a smaller size; nothing below 12px exists.
At its native pixel size the face needs no scaling, so no glyph is
anti-aliased. `ONE_LINE_CHARS` and `TITLE_CHARS` are derived from that
6.65px measurement and the column width.

**Crispness.** The panel dithers anything that is not one of its four
inks, and a dither reads as fuzz. So: no grey tokens, no opacity, no
half-tone fill anywhere; block text is black or white only; hour rules and column
edges land on whole pixels, which is why `AXIS_W` is chosen to divide the
panel exactly and `HOUR_H` is an integer quotient. `PANEL_W`/`PANEL_H` are
the USABLE box - 780x460 on the 800x480 device - because the framework's
`.screen` insets its content by 10px on every side; budgeting against the
raw panel overflowed both axes and clipped the right-hand column. `check.sh` greps the
built HTML for every one of those.

## Commands

Docker supplies the toolchain: this Mac's system Ruby is 2.6, and the
`trmnl_preview` gem needs 3.2+. `bin/trmnlp` runs the gem when it exists
and otherwise `trmnl/trmnlp:latest`, so nothing below needs a local Ruby.

```
./scripts/check.sh     # lint + render all four layouts (the gate)
./bin/trmnlp lint      # TRMNL best-practice checks only
./bin/trmnlp build     # write _build/*.html
./bin/trmnlp serve     # live preview on http://localhost:4567
```

`./bin/trmnlp serve` serves one page per layout and shows the assembled
JSON payload underneath, which is the quickest way to see what the
fixture resolves to.

## State

Working. `scripts/check.sh` is green: lint clean, all four layouts render
from the fixture.

Live on usetrmnl.com as private plugin <grid-id> (`trmnl-calendar-color`,
strategy Plugin Merge), reading merge variable `google_calendar_<id>`
and displayed on device <device-id>'s playlist, with the native instance kept
on that playlist but hidden so it keeps syncing.

Deploying the full layout means pasting `src/full.liquid` into the
markup editor with the node name and `CAL_MAP` lines kept from the live
copy. The form no-ops unless `data-markup-dirty-value` is `true`, and the
editor's device dropdown must be set to `TRMNL OG (B/W/R/Y)` for the
preview to show the colours the device will actually print.

There is no CI workflow, on purpose: `scripts/check.sh` needs only Docker
and runs locally in seconds, and TRMNL's generated workflow would push to
the server on every merge to main.
