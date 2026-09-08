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
| `scripts/geometry_check.py` | asserts every block holds its full text and nothing overlaps |
| `reference/native-3day/` | what the native render exposes, and the settings it came from |

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
independently; all-day events never move it. `day` is 00:00-24:00. A
range that will not fit is kept, not squeezed - the column clips at the
bottom and the surplus becomes "+N more".

`GRID_BUDGET_H` is a px budget, not the height: `HOUR_H` is that budget
divided by the hours on the axis, clamped to `HOUR_H_MIN..HOUR_H_MAX`,
and the real `GRID_H` is `HOUR_H * HOURS`. Pinning `HOUR_H` instead is
what broke the live render on 2026-09-07: 24px times an 18-hour axis
overflowed the panel, and TRMNL centres an overflowing view, so the day
headers went off the top. `scripts/check.sh` now reads `data-grid-h` back
out of the built HTML and fails if it exceeds the layout's budget.

**Readability decides the geometry.** A block is at least as tall as its
text — one line when `start - end  Title` fits `ONE_LINE_CHARS`, two
otherwise — grows to its duration, and stops at `MAX_BLOCK_H` so one
nine-hour event cannot push the day off the bottom. A block that would
collide slides DOWN. So blocks never overlap, always have the full column
width, and a title is shortened only when the title alone exceeds
`TITLE_CHARS`. What no longer fits becomes "+N more" rather than smaller
type. There are no lanes: two lanes in a 253px column left 197px, which
is where truncated titles came from.

**Crispness.** The panel dithers anything that is not one of its four
inks, and a dither reads as fuzz. So: no grey tokens, no opacity, no
half-tone fill anywhere (a weekend is a heavier column rule, never a
shaded column); block text is black or white only; hour rules and column
edges land on whole pixels, which is why `AXIS_W` is chosen to divide the
panel exactly and `HOUR_H` is an integer quotient. `check.sh` greps the
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
