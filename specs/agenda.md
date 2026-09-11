# Agenda view: what is out of the routine, by month

## Goal

A second view of the same private plugin that lists the one-off events
(tournaments, shows, concerts, trips) from one or more chosen calendars,
grouped under month headers, as far ahead as the data reaches. The grid
answers "what is my day"; the agenda answers "what is coming that is not
routine". It must read on the 1-bit TRMNL and on the OG B/W/R/Y panel.

## Data, and the horizon

The plugin reads the native Google Calendar instance through Plugin
Merge. That plugin fetches `days_ahead` from today, set by its layout
(`lib/google_calendar/google_calendar.rb`, `time_max`): 42 days for
`month` and `rolling_month`, 14 for `schedule`, 7 for the rest, 1 for
`today_only`. So the native instance must run the `month` layout, and
the horizon is six weeks. Nothing on TRMNL fetches further: the iCal
plugins' widest layout is "this calendar month". A longer horizon needs
a polling source that serves the same event shape from the calendar's
private iCal address; that is a later phase and is not built here.

The one-off calendar is a Google calendar the user keeps for these
events only, ticked in the native instance's calendar list. The agenda
lists every ticked calendar that is not quiet unless `agenda_calendars`
names the ones to show.

## Settings (custom fields)

| field | keyname | values |
|---|---|---|
| View | `mode` | `grid` (default) or `agenda` |
| Agenda calendars | `agenda_calendars` | calendar ids, one per line or comma-separated; empty = every calendar that is not quiet |

`cal_map` still colours the swatch and names the calendar. One private
plugin, two instances: the grid instance and the agenda instance differ
only in these fields.

## Render

- A panel 700px or wider (full, half-horizontal) lists in two columns
  balanced by count; the second column repeats the header of a month it
  continues. Narrow panels use one column.
- A second event on the same day leaves its date cell blank.
- Rows are one line each: `[swatch] Sat 10/17  7:00pm  Title · Location`.
  The date column is 9 characters, the time column 7. Location follows
  the title after a middle dot and only in the full layout, cut at its
  first comma: Google sends the whole postal address and the venue is
  the part before it. The line is
  cut with an ellipsis, never wrapped.
- A month header is a black bar with the month name in white, `October
  2026`. It is emitted the first time an event of that month is placed.
- Today's date column reads `Today`. A multi-day all-day event shows
  its span, `10/3-10/7`, once, under the month it starts in; one that
  has already started is anchored to today and reads `now-10/7`.
- Order: by start. Included: an all-day event whose last day is today
  or later; a timed event that starts today or later.
- Budget: the usable panel height less one footer line. Rows and
  headers are placed until the next one would not fit; the rest are
  counted into `+N more` in the footer. The footer's left side says
  `through <last day of the horizon>` so the reader knows how far the
  list looks.
- Empty: one row, `Nothing out of the routine through <date>`.
- Inks: black and white only, plus the calendar's own token on the
  8px swatch. On a 1-bit panel a hue token dithers or maps to black;
  the layout carries no information in colour alone.

## Checks

`scripts/agenda_check.py` runs on a fixture build with `mode: agenda`
and `agenda_calendars: fun@example.com`. It asserts: month headers in
calendar order and only for months that have rows; every row under the
right header; the past one-off absent; other calendars' events absent;
the ongoing trip first with a `now-` span; the later trip with its
`m/d-m/d` span; the total of rows shown plus `+N more` equals the
included events; no row text wider than the row's character budget.

## Deploy

Paste the four layouts as before. Add `mode` and `agenda_calendars` to
the plugin's Form Fields on the site. Create a second instance of the
plugin with `mode: agenda`. Set the native instance's layout to
`month`. Tick the one-off calendar in the native instance.
