# Reverse-engineering the native 3 Day Week render

## The native render is a raster image, not HTML

The instance edit page embeds the render as an
Active Storage blob (`plugin-<hash>`), 800x480 PNG. `native-3day-800x480.png`
is that blob. No route on the site serves the render as HTML: `/render`,
`/preview`, `/render_markup`, `/markup`, `/screens`, `/screen`,
`/plugins/<id>/render` and `/plugin_settings/<id>.json` all 404, and
the page's own "Edit Markup" button is a link to
`docs.trmnl.com/go/private-api/plugin-data` - the Plugin Merge writeup -
not to an editor. The markup is not exposed by the product.

It is not exposed in source either. `usetrmnl/plugins` publishes
`lib/google_calendar/google_calendar.rb` (the data layer) and
`lib/google_calendar/views/calendars/_full.html.erb`, but that file only
dispatches on `event_layout` to partials named `full_week`, `full_month`,
`schedule` and `full_auto`, and those partials are not in the repo. The
grid lives in TRMNL's closed core app.

So the layout below was read off the pixels, not copied.

## What the pixels show

* 800x480. Day header row, then the all-day band, then the hour grid.
  The grid overflows and is cut off around 3pm - the native render does
  not shrink to fit.
* Day headers centred over each column, `Mon 9/7` (`date_format: short`).
  Today is a filled black pill with white text (`highlight_today: yes`).
* A narrow (~31px) hour gutter on the left, labels `5am`, `6am`, ...,
  one per hour, aligned to the rule.
* Dashed horizontal rules above and below the all-day band. Dotted
  vertical rules between day columns. Dotted horizontal hour rules.
* All-day entries are filled bars with the summary inside, spanning the
  days they cover.
* Timed events are filled blocks sized to their duration with a thin
  white outline. One line of text when short (`9:00 AM - 9:45 AM - Busy`),
  two when tall (time, then summary). Overlapping events cascade to the
  right and paint over each other rather than dividing the column.
* Every fill is black despite `colorize_events: yes`, which is the whole
  reason this plugin exists.
