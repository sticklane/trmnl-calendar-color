# trmnl-calendar-color

Four TRMNL Liquid templates that color-code Google Calendar events by
which calendar they came from. They run as a TRMNL **Private Plugin with
strategy Plugin Merge**, reading the merge variable a native Google
Calendar plugin instance publishes. There is no application code and no
data layer here — TRMNL's own plugin fetches the events; these templates
only render them.

## Map

| path | what |
|---|---|
| `src/full.liquid` | full layout, 800x480, no day cap, 3 overflow columns |
| `src/half_horizontal.liquid` | half layout, 3-day cap |
| `src/half_vertical.liquid` | half layout, 3-day cap |
| `src/quadrant.liquid` | quadrant layout, 1-day cap, legend off |
| `src/settings.yml` | plugin metadata read by trmnlp. Not the deploy path |
| `.trmnlp.yml` | local-preview fixture that stands in for the merge variable |
| `bin/trmnlp` | gem-or-Docker wrapper for the `trmnlp` CLI |
| `scripts/check.sh` | the canonical check |

Each layout is the same template with a different knob block at the top
(`MODE`, `MAX_DAYS`, `SHOW_LEGEND`, `CAL_MAP`, …). A change to the render
body usually has to land in all four files.

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

Not yet configured on usetrmnl.com — the private plugin has not been
created and no device playlist references it. Doing that needs a signed-in
session and the owner's own calendar ids for `CAL_MAP`.

There is no CI workflow, on purpose: `scripts/check.sh` needs only Docker
and runs locally in seconds, and TRMNL's generated workflow would push to
the server on every merge to main.
