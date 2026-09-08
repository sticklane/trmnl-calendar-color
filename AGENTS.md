# trmnl-calendar-color

Four TRMNL Liquid templates that render a **3-day week** — one column per
day, starting today — with each event color-coded by which calendar it
came from. They run as a TRMNL **Private Plugin with
strategy Plugin Merge**, reading the merge variable a native Google
Calendar plugin instance publishes. There is no application code and no
data layer here — TRMNL's own plugin fetches the events; these templates
only render them.

## Map

| path | what |
|---|---|
| `src/full.liquid` | full layout, 800x480, 3 day columns, descriptions on |
| `src/half_horizontal.liquid` | half layout, 3 day columns, 4 events/day |
| `src/half_vertical.liquid` | half layout, 2 day columns, legend off |
| `src/quadrant.liquid` | quadrant layout, 2 day columns, 3 events/day |
| `src/settings.yml` | plugin metadata read by trmnlp. Not the deploy path |
| `.trmnlp.yml` | local-preview fixture that stands in for the merge variable |
| `bin/trmnlp` | gem-or-Docker wrapper for the `trmnlp` CLI |
| `scripts/check.sh` | the canonical check |

Each layout is the same template with a different knob block at the top
(`NUM_DAYS`, `MAX_PER_DAY`, `MODE`, `SHOW_LEGEND`, `CAL_MAP`, …). A change
to the render body has to land in all four files.

The knobs mirror the native Google Calendar instance's own display
settings, so the private plugin and the native one agree: `NUM_DAYS = 3`
for its `three_day_week` layout, `DAY_FMT` for `date_format: short`,
`HIGHLIGHT_TODAY` and `SHADE_WEEKENDS` for its matching toggles, and
`SHOW_DESC` for `include_description`. Event times are printed straight
from `ev.start` / `ev.end`, which the native plugin has already formatted
with its `time_format`, so the clock style needs no knob.

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
