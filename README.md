# TRMNL Google Calendar fork — color by calendar source

Four Liquid templates (one per TRMNL layout tab) for a **Private Plugin, strategy = Plugin Merge**. Each event gets a visual identity keyed on which calendar it came from: a left bar, a glyph, or a filled row.

## Why a Plugin Merge template and not a code fork

The public repo (`usetrmnl/plugins/lib/google_calendar`) only holds the Ruby data layer plus thin ERB wrappers. The actual week/month/schedule grids (`plugins/calendars/full_week`, `full_month`, `schedule`, `full_auto`, `all_day_event`, `title_bar`) live in TRMNL's private core app and use a commercial FullCalendar license. Not forkable. What *is* exposed: every event object already carries `calname` and `background_color`, and the locals include `calendar_names` (id → display name). This template builds on that.

## Is there anything to fork instead?

Checked 2026-09-07. No.

- `usetrmnl/plugins` publishes `lib/google_calendar/google_calendar.rb`
  and `lib/google_calendar/views/calendars/_full.html.erb`, but that ERB
  only dispatches on `event_layout` to `full_week`, `full_month`,
  `schedule` and `full_auto`, and none of those partials is in the repo.
  Its README says the code is published "to showcase which values, and
  how, are extracted", not to run.
- TRMNL Recipes are forkable - "Forking a Recipe will make the markup and
  other settings editable, as if it was your own"
  (help.trmnl.com/en/articles/10122094-plugin-recipes, needs the
  Developer Edition add-on). But native plugins are not Recipes, so the
  Google Calendar grid is not on that list.
- Every public community calendar plugin renders an agenda LIST, not an
  hour-axis grid: `zoltanhosszu/trmnl-calendar`, `jfsso/trmnl-calendar`,
  `frjo/usetrmnl-plugins`. The marketplace "Simple Calendar" recipe is a
  month grid; "Pretty Calendar" is closed and CalDAV-only.
- The design framework (trmnl.com/framework) ships `Grid`, `Columns` and
  `Table` but no calendar or week component.

So the grid here is hand-built, and `reference/native-3day/NOTES.md`
records what it was built to match.

## Setup

1. Connect **Google Calendar** natively. Select every calendar you want. Set Event Layout to `schedule` (14-day window) or `week` (7-day) — that controls how far ahead the JSON reaches.
2. Playlists → hide that instance (eyeball icon). Hidden but on a playlist = still syncs.
3. Plugins → Private Plugin → Strategy **Plugin Merge** → Edit Markup.
4. Open the **Merge Variables** dropdown, find `google_calendar_<id>`. Click **Force Refresh** if it's empty.
5. Paste `full.liquid` into the Full tab, etc. In each file replace `google_calendar_12345` with your node name.
6. Fill `CAL_MAP`. Keys are the `calname` values you see in the JSON (calendar id/email), values are framework tokens:
   ```
   {%- assign CAL_MAP = "you@gmail.com=black,work@google.com=gray-40,abc@group.calendar.google.com=gray-65" | split: "," -%}
   ```
   Unlisted calendars get tokens from `FALLBACK`, skipping any token already claimed in `CAL_MAP`.

## Repo layout

| path | what |
|---|---|
| `src/full.liquid`, `half_horizontal`, `half_vertical`, `quadrant` | the four markup tabs, one per TRMNL layout |
| `src/settings.yml` | plugin metadata for trmnlp. Not the deploy path — see below |
| `.trmnlp.yml` | local preview fixture standing in for the merge variable |
| `bin/trmnlp` | runs the `trmnlp` gem if installed, else the Docker image |
| `scripts/check.sh` | lint plus a render of all four layouts |

## Local preview

Needs either the `trmnl_preview` gem (Ruby >= 3.2) or Docker. This machine
has neither a modern Ruby nor the gem, so `bin/trmnlp` falls through to
`trmnl/trmnlp:latest` on Docker.

```
./scripts/check.sh          # lint + render all four layouts into _build/
./bin/trmnlp serve          # live preview at http://localhost:4567
```

trmnlp knows the `polling`, `webhook` and `static` strategies but not
Plugin Merge, so the preview fakes the merge variable: `variables:` in
`.trmnlp.yml` deep-merges into the top-level Liquid scope, which is
exactly where `google_calendar_<id>` lands on the server. The fixture
covers three mapped calendars, an all-day event, and one unmapped
calendar so the `FALLBACK` token cycle gets exercised. Rename the fixture
key and the `assign src = ...` line together.

`strategy: polling` with an empty `polling_url` is an inert placeholder
that keeps the local renderer happy. **Do not `trmnlp push`** — that
would create a polling plugin on the server, not a Plugin Merge one.
Deploy by pasting each `src/*.liquid` into its markup tab, per Setup above.

## Knobs (top of each file)

| var | values | notes |
|---|---|---|
| `MODE` | `bar` / `glyph` / `both` / `fill` | `both` is the default. `fill` shades the whole row — readable only with light tokens (gray-20 or lighter) on 1-bit |
| `SHOW_LEGEND` | true/false | glyph + calendar name in the title bar |
| `SHOW_TIME`, `SHOW_DESC` | true/false | |
| `MAX_DAYS` | int, 0 = uncapped | quadrant = 1, half = 3 by default |
| `DAY_FMT` | strftime | day header format |

## Gotchas

- **Hue tokens collapse on grayscale panels, but not on a colour one.** `bg--red` and `bg--blue` at the same lightness step render as the *same* dither on the 1-bit TRMNL and the same gray on TRMNL X. The placeholder `CAL_MAP` in this repo is therefore grayscale steps spaced ≥ 15 apart plus glyphs. A TRMNL OG (B/W/R/Y) panel does distinguish hues: the framework dithers a hue token into the device's ink set, selected by the `screen--color-4bwry` palette. Check before you choose - the markup editor's device dropdown has a `TRMNL OG (B/W/R/Y)` entry that previews exactly that mapping.
- **Google's own hex colors are ignored on purpose.** `background_color` is present in the JSON, but mapping arbitrary hex to a dither pattern in Liquid is brittle and Google's palette shifted between API versions. Explicit `CAL_MAP` is deterministic.
- **Day grouping uses `start_full | date`.** Timed events carry their offset (`...-05:00`), so the day key is local. All-day events are `YYYY-MM-DD` strings and parse fine. Multi-day all-day events appear once, under their start date (native expands them per day — not replicated here).
- **JSON shape assumption:** `events` is a flat, sorted array (matches current `prepare_events`). The April 2025 hackathon sample showed `events` as a hash keyed by day label. If your merge variable shows that older shape, swap the outer loop for `{% for day in events %}{% for ev in day[1] %}…` and drop the day-key logic.
- **Legend overflow.** Five-plus calendars with long names will overflow the title bar `instance` span. Shorten via `calendar_names` (rename in Google) or set `SHOW_LEGEND = false` on half/quadrant.
- Untested claims: the TRMNL custom `date` filter behavior with millisecond ISO strings, and `data-overflow-*` behavior in a Plugin Merge context. Both were validated against Ruby-compatible Liquid locally, not against TRMNL's renderer. Check the preview after paste.

## Merging a second calendar source (Outlook, iCal)

Plugin Merge lets you reference multiple nodes. Liquid `concat` joins arrays:
```
{%- assign events = google_calendar_12345.events | concat: outlook_calendar_67890.events | sort: "date_time" -%}
```
Whether Outlook/iCal events carry a `calname` field: data missing — that plugin's source isn't in the public repo. If they don't, key `CAL_MAP` on whatever distinguishing field they expose, or tag by loop instead of concat.
