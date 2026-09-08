# TRMNL Google Calendar fork — color by calendar source

Four Liquid templates (one per TRMNL layout tab) for a **Private Plugin, strategy = Plugin Merge**. Each event gets a visual identity keyed on which calendar it came from: a left bar, a glyph, or a filled row.

## Why a Plugin Merge template and not a code fork

The public repo (`usetrmnl/plugins/lib/google_calendar`) only holds the Ruby data layer plus thin ERB wrappers. The actual week/month/schedule grids (`plugins/calendars/full_week`, `full_month`, `schedule`, `full_auto`, `all_day_event`, `title_bar`) live in TRMNL's private core app and use a commercial FullCalendar license. Not forkable. What *is* exposed: every event object already carries `calname` and `background_color`, and the locals include `calendar_names` (id → display name). This template builds on that.

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

## Knobs (top of each file)

| var | values | notes |
|---|---|---|
| `MODE` | `bar` / `glyph` / `both` / `fill` | `both` is the default. `fill` shades the whole row — readable only with light tokens (gray-20 or lighter) on 1-bit |
| `SHOW_LEGEND` | true/false | glyph + calendar name in the title bar |
| `SHOW_TIME`, `SHOW_DESC` | true/false | |
| `MAX_DAYS` | int, 0 = uncapped | quadrant = 1, half = 3 by default |
| `DAY_FMT` | strftime | day header format |

## Gotchas

- **Hue tokens collapse on grayscale panels.** `bg--red` and `bg--blue` at the same lightness step render as the *same* dither on the original 1-bit TRMNL and the same gray on TRMNL X (4-bit grayscale). Only true color panels distinguish hues. That's why the defaults are grayscale steps spaced ≥ 15 apart plus glyphs. Use hue tokens only if your device shows color.
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
