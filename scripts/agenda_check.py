"""Invariants for the agenda view, checked against the .trmnlp.yml fixture
built with `mode: agenda` and `agenda_calendars: fun@example.com`.

Month headers appear in calendar order and only for months that have a
row under them. Every included one-off event is either a row under its
month or counted into "+N more". A past event and any other calendar's
event never appear. A multi-day all-day event shows its span once; one
that has already started is anchored to today and reads "now-m/d".
"""
import datetime as dt, html, pathlib, re, sys, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = yaml.safe_load((ROOT / '.trmnlp.yml').read_text())
NODE = next(v for v in FIX['variables'].values()
            if isinstance(v, dict) and 'events' in v)
EVENTS = NODE['events']
TODAY = dt.date.fromisoformat(NODE['today_in_tz'].split('T')[0])
CAL = FIX['variables']['agenda_calendars'].strip()

HEADER = re.compile(r'<div class="ag-month[^"]*"[^>]*data-month="(\d{4}-\d{2})" data-col="(\d)"')
ROW = re.compile(r'<div class="ag-row[^"]*"[^>]*data-month="(\d{4}-\d{2})" data-date="([^"]*)" '
                 r'data-cal="([^"]*)" data-text="([^"]*)" data-col="(\d)"')
MORE = re.compile(r'data-more="(\d+)"')


def flat(s):
    return html.unescape(s).strip()


def wanted():
    """The fixture events the agenda must account for, in order."""
    out = []
    for ev in sorted(EVENTS, key=lambda e: e['start_full']):
        if ev['calname'] != CAL:
            continue
        start = dt.date.fromisoformat(ev['start_full'][:10])
        if ev.get('all_day'):
            end = dt.date.fromisoformat(ev['end_full'][:10]) if ev.get('end_full') else start
            last = end - dt.timedelta(days=1) if end > start else start
            if last < TODAY:
                continue
        elif start < TODAY:
            continue
        anchor = max(start, TODAY)
        out.append((anchor, ev))
    return out

fail = []
WANT = wanted()
for f in sorted((ROOT / '_build').glob('*.html')):
    h = f.read_text()
    name = f.name
    headers = HEADER.findall(h)
    rows = ROW.findall(h)
    more = sum(int(n) for n in MORE.findall(h))
    cols = int(re.search(r'data-ag-cols="(\d)"', h).group(1))
    split = int(re.search(r'data-ag-split="(\d+)"', h).group(1))
    if not headers:
        fail.append(f'{name}: no month headers')
    # Per column: headers in order, none repeated, and exactly the months
    # that have rows there. A month may open a second column again.
    for c in range(1, cols + 1):
        hc = [m for m, col in headers if int(col) == c]
        rc = []
        for m, _, _, _, col in rows:
            if int(col) == c and m not in rc:
                rc.append(m)
        if hc != sorted(hc) or len(hc) != len(set(hc)):
            fail.append(f'{name}: column {c} month headers out of order or repeated: {hc}')
        if hc != rc:
            fail.append(f'{name}: column {c} headers {hc} do not match its months with rows {rc}')
    col_of = [int(col) for _, _, _, _, col in rows]
    if col_of != sorted(col_of):
        fail.append(f'{name}: rows are not in column order')
    if cols == 2 and more == 0 and len(rows) == len(WANT):
        want_first = (len(WANT) + 1) // 2
        if split != want_first or col_of.count(1) != want_first:
            fail.append(f'{name}: {col_of.count(1)} rows in column 1, want a balanced {want_first}')
    # every row is a wanted event, in order, and under its own month
    texts = [flat(t) for _, _, _, t, _ in rows]
    for (m, d, cal, text, _), (anchor, ev) in zip(rows, WANT):
        if cal != CAL:
            fail.append(f'{name}: row from another calendar {cal!r}')
        if m != anchor.strftime('%Y-%m'):
            fail.append(f'{name}: {ev["summary"]!r} placed under {m}, want {anchor:%Y-%m}')
        if not flat(text).startswith(ev['summary'][:12]) and not ev['summary'].startswith(flat(text).rstrip('.')):
            fail.append(f'{name}: row {flat(text)!r} is not {ev["summary"]!r} (order?)')
    if len(rows) + more != len(WANT):
        fail.append(f'{name}: {len(rows)} rows + {more} more != {len(WANT)} wanted events')
    if name == 'full.html' and not any(t == 'Concert at the Vic · The Vic' for t in texts):
        fail.append(f'{name}: the venue should be the location up to its first comma')
    if name == 'full.html' and not any(t.startswith('Comedy show with a very') and 'Zanies' not in t for t in texts):
        fail.append(f'{name}: a title that fills the cell must keep its words and drop the venue')
    for bad in ('Past show', 'Dentist', 'Standup', 'Busy'):
        if any(bad in t for t in texts):
            fail.append(f'{name}: {bad!r} must not be listed')
    ongoing = [d for _, d, _, t, _ in rows if 'Ongoing trip' in t]
    if ongoing and not ongoing[0].startswith('now-'):
        fail.append(f'{name}: the ongoing trip reads {ongoing[0]!r}, want "now-9/8"')
    denver = [d for _, d, _, t, _ in rows if 'Trip to Denver' in t]
    if denver and denver[0] != '10/15-10/18':
        fail.append(f'{name}: the Denver trip reads {denver[0]!r}, want "10/15-10/18"')
    tc = re.search(r'data-ag-chars="(\d+)"', h)
    if tc:
        for _, _, _, t, _ in rows:
            if len(flat(t)) > int(tc.group(1)):
                fail.append(f'{name}: row {flat(t)!r} is wider than {tc.group(1)} chars')
    else:
        fail.append(f'{name}: template does not report data-ag-chars')

if fail:
    print('\n'.join(sorted(set(fail))[:12]))
    sys.exit(1)
print('agenda OK: every one-off event is a row under its month or counted, and nothing else is')
