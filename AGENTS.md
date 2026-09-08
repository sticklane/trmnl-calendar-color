# trmnl-calendar-color

Four TRMNL Liquid templates that render a **3 Day Week time grid** —
hours down the left axis, one column per day starting today, every timed
event a block positioned by start time and sized by duration — with each
event color-coded by which calendar it came from. They run as a TRMNL **Private Plugin with
strategy Plugin Merge**, reading the merge variable a native Google
Calendar plugin instance publishes. There is no application code and no
data layer here — TRMNL's own plugin fetches the events; these templates
only render them.

## Map

| path | what |
|---|---|
| `src/full.liquid` | full layout, 3 day columns, 17px/hour, hourly labels |
| `src/half_horizontal.liquid` | half layout, 3 day columns, 7px/hour, every 3rd label |
| `src/half_vertical.liquid` | half layout, 2 day columns, 16px/hour, legend off |
| `src/quadrant.liquid` | quadrant layout, 2 day columns, 6px/hour, legend off |
| `src/settings.yml` | plugin metadata read by trmnlp. Not the deploy path |
| `.trmnlp.yml` | local-preview fixture that stands in for the merge variable |
| `bin/trmnlp` | gem-or-Docker wrapper for the `trmnlp` CLI |
| `scripts/check.sh` | the canonical check |

Each layout is the same template with a different knob block at the top
(`NUM_DAYS`, `HOUR_H`, `HOUR_EVERY`, `SHOW_LEGEND`, `CAL_MAP`, …). A change
to the render body has to land in all four files.

The knobs mirror the native Google Calendar instance's own display
settings, so the private plugin and the native one agree: `NUM_DAYS = 3`
for its `three_day_week` layout, `DAY_FMT` for `date_format: short`,
`HIGHLIGHT_TODAY` and `SHADE_WEEKENDS` for its matching toggles, and
`GRID_START_H` / `GRID_END_H` (5 and 23) for its `scroll_time` and
`scroll_time_end`. Event times are printed straight from `ev.start`,
which the native plugin has already formatted with its `time_format`, so
the clock style needs no knob.

`HOUR_H` is pixels per hour and the grid height is derived from it. Do
not set a height directly: the hour rules are a repeating gradient at a
fixed pixel pitch, and a height that is not a whole multiple of the hour
count slides the rules out from under the events.

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

There is no CI workflow, on purpose: `scripts/check.sh` needs only Docker
and runs locally in seconds, and TRMNL's generated workflow would push to
the server on every merge to main.
