"""Placement and readability invariants for the rendered grid.

Placement follows the native 3 Day Week render: every block sits at its
clock position, a block that starts before an earlier block ends (by the
clock) is indented one step per such block and painted over it, and a
block spans its whole duration. One rule is ours: no block covers another
block's text, so it starts no higher than the text bottom of any drawn
box that reaches below its clock top. Text is still the
constraint: a block is never smaller than the text it carries, and the
only thing ever shortened is a title longer than its width can hold.
These checks falsify each of those claims against the .trmnlp.yml fixture.
"""
import html, pathlib, re, sys, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = yaml.safe_load((ROOT / '.trmnlp.yml').read_text())
NODE = next(v for v in FIX['variables'].values()
            if isinstance(v, dict) and 'events' in v)
EVENTS = NODE['events']
TODAY = NODE['today_in_tz'].split('T')[0]

SPAN = re.compile(r'<span class="label label--small cg-line[^"]*">(.*?)</span>', re.S)
BLOCK = re.compile(
    r'<div class="cg-block[^"]*"[^>]*data-block="([\d,]+)" data-clock="([\d,]+)" '
    r'data-tc="(\d+)" data-form="(\d)" '
    r'data-times="([^"]*)" data-title="([^"]*)">(.*?)</div>', re.S)


def flat(s):
    return re.sub(r'\s+', ' ', html.unescape(s).replace('&nbsp;', ' ')).strip()

fail = []


def minutes(t):
    hh, mm = t.split('T')[1][:5].split(':')
    return int(hh) * 60 + int(mm)


def axis_range(mode, window):
    """What AXIS_MODE should have produced for this window."""
    if mode == 'day':
        return (0, 24)
    lo, hi = 9999, -1
    for ev in EVENTS:
        if ev.get('all_day') or ev['start_full'].split('T')[0] not in window:
            continue
        s = minutes(ev['start_full'])
        e = minutes(ev['end_full']) if ev.get('end_full') else s + 60
        if e - s < 5:          # zero-length events never move the axis
            continue
        lo, hi = min(lo, s), max(hi, e)
    if hi < 0:
        return (8, 18)
    return (max(0, lo // 60 - 1), min(24, -(-hi // 60) + 1))


def truncate(s, n):
    """Liquid's `truncate`: n chars total, the last three being '...'."""
    return s if len(s) <= n else s[:n - 3] + '...'


# Every title the fixture could legitimately produce, per column width.
EXPECTED_TITLES = {n: {truncate(ev['summary'], n): ev for ev in EVENTS}
                   for n in range(10, 160)}


def compact(ev):
    """The block's time string: one meridian when both ends share it."""
    s, sap = ev['start'].split(' ')
    e, eap = ev['end'].split(' ')
    if sap == eap:
        return f'{s}-{e}{eap.lower()}'
    return f'{s}{sap.lower()}-{e}{eap.lower()}'


# A quiet calendar: two or more events, all with the same summary. Its
# blocks carry no title, only their times.
def _quiet():
    by_cal = {}
    for ev in EVENTS:
        by_cal.setdefault(ev['calname'], set()).add(ev['summary'])
    counts = {}
    for ev in EVENTS:
        counts[ev['calname']] = counts.get(ev['calname'], 0) + 1
    return {c for c, sums in by_cal.items() if len(sums) == 1 and counts[c] >= 2}

QUIET = _quiet()


for f in sorted((ROOT / '_build').glob('*.html')):
    h = f.read_text()
    name = f.name

    m = re.search(r'data-title-chars="(\d+)"', h)
    if not m:
        fail.append(f'{name}: template does not report data-title-chars')
        continue
    title_chars = int(m.group(1))

    for L in re.findall(r'data-hour="\d+" data-hour-y="\d+">([^<]*)</span>', h) or ['']:
        if not re.fullmatch(r'\d{1,2}(am|pm)', L.strip()):
            fail.append(f'{name}: clipped or odd hour label {L!r}')

    window = set(re.findall(r'data-grid-col="([\d-]+)"', h))
    mode = re.search(r'data-axis-mode="(\w+)"', h).group(1)
    got = (int(re.search(r'data-axis-start="(\d+)"', h).group(1)),
           int(re.search(r'data-axis-end="(\d+)"', h).group(1)))
    want = axis_range(mode, window)
    if got != want:
        fail.append(f'{name}: axis_mode {mode} gave hours {got}, expected {want}')
    labels = [(int(a), int(b)) for a, b in
              re.findall(r'data-hour="(\d+)" data-hour-y="(\d+)"', h)]
    hours = [a for a, _ in labels]
    grid_h = int(re.search(r'data-grid-h="(\d+)"', h).group(1))
    line_h = int(re.search(r'data-line-h="(\d+)"', h).group(1))
    line_h_full = line_h
    if hours and hours[0] != want[0]:
        fail.append(f'{name}: first hour label {hours[0]}, expected {want[0]}')
    # The window is a hard constraint: its END is labelled, inside the grid.
    if hours and hours[-1] != want[1]:
        fail.append(f'{name}: last hour label {hours[-1]}, expected the window end {want[1]}')
    for hh, hy in labels:
        if hy + line_h > grid_h:
            fail.append(f'{name}: hour label {hh} sits at y={hy}, past the {grid_h}px grid')
        if hy < 0:
            fail.append(f'{name}: hour label {hh} sits above the grid')
    ys = sorted(hy for _, hy in labels)
    for y1, y2 in zip(ys, ys[1:]):
        if y2 - y1 < line_h:
            fail.append(f'{name}: hour labels {y1}px and {y2}px are closer than one line')

    axis_start, axis_end = got
    span_min = (axis_end - axis_start) * 60
    tight_h = int(re.search(r'data-tight-line-h="(\d+)"', h).group(1))
    indent_w = int(re.search(r'data-indent-w="(\d+)"', h).group(1))
    max_depth = int(re.search(r'data-max-depth="(\d+)"', h).group(1))

    def clock_px(mins):
        mins = min(max(mins, axis_start * 60), axis_end * 60)
        return (mins - axis_start * 60) * grid_h // span_min

    drawn, more_total = set(), 0
    cols = re.split(r'<div class="cg-col[^"]*" data-grid-col="', h)[1:]
    if not cols:
        fail.append(f'{name}: no grid columns')
    for chunk in cols:
        day = chunk.split('"', 1)[0]
        placed = []   # (top, bottom, text_bottom, clock_bottom) per block drawn so far
        for geom, clock, tc, form, dtimes, dtitle, inner in BLOCK.findall(chunk):
            top, hgt, left, lines, line_h = (int(x) for x in geom.split(','))
            ctop, cbot = (int(x) for x in clock.split(','))
            tc = int(tc)
            bottom = top + hgt
            text_h = lines * line_h + 2
            if text_h > hgt:
                fail.append(f'{name} {day}: {lines} line(s) need {text_h}px, block is {hgt}px')
            if line_h < 10:
                fail.append(f'{name} {day}: line height {line_h}px is below the 10px floor')
            # Small event, small text: the tight face appears only when the
            # 12px text could not fit the event's minutes, and the 12px face
            # only when it did.
            dur_h = cbot - ctop
            if line_h == tight_h and dur_h >= 2 * line_h_full + 2:
                fail.append(f'{name} {day}: {dtitle!r} is in small type but its {dur_h}px would hold two 12px lines')
            if line_h == line_h_full and text_h > dur_h:
                fail.append(f'{name} {day}: {dtitle!r} is in 12px type ({text_h}px) but its event is only {dur_h}px')
            rendered = flat(' '.join(SPAN.findall(inner)))
            title = flat(dtitle)
            # The title leads and the times follow; form 3 has dropped the
            # times entirely rather than shorten the title.
            want = title if form == '3' else flat(title + ' ' + dtimes)
            if rendered != want:
                fail.append(f'{name} {day}: rendered {rendered!r} != {want!r}')
            if not rendered.startswith(title):
                fail.append(f'{name} {day}: {rendered!r} does not lead with its title')
            # The small face carries more characters across the same width,
            # by the same ratio the template uses (hundredths of a px).
            max_tc = title_chars * 665 // (665 * line_h // line_h_full)
            if tc > max_tc:
                fail.append(f'{name} {day}: {title!r} claims {tc} chars, wider than the column ({max_tc})')
            if title.endswith('...') and len(title) != tc:
                fail.append(f'{name} {day}: title {title!r} shortened below its {tc}-char width')
            if title == '':
                ev = next((e for e in EVENTS if e['calname'] in QUIET and not e.get('all_day')
                           and e['start_full'].startswith(day) and compact(e) == dtimes), None)
                if ev is None:
                    fail.append(f'{name} {day}: a block with no title at {dtimes} is not a quiet-calendar event')
            else:
                ev = EXPECTED_TITLES.get(tc, {}).get(title)
                if ev is not None and ev['calname'] in QUIET:
                    fail.append(f'{name} {day}: quiet calendar shows its summary {title!r}')
                if dtimes != compact(ev) if ev else False:
                    fail.append(f'{name} {day}: {title!r} shows times {dtimes!r}, want {compact(ev)!r}')
            if ev is None and title != '':
                fail.append(f'{name} {day}: title {title!r} is not any fixture event, in full')
            else:
                drawn.add(ev['summary'])
                s = minutes(ev['start_full'])
                e = minutes(ev['end_full']) if ev.get('end_full') else s + 60
                if e <= s:
                    e = s + 30
                if (ctop, cbot) != (clock_px(s), clock_px(e)):
                    fail.append(f'{name} {day}: {want!r} claims clock {ctop}-{cbot}px, '
                                f'the fixture says {clock_px(s)}-{clock_px(e)}px')

            # Native placement: the block sits at its clock top and spans
            # its whole duration ...
            depth = sum(1 for _, _, _, cb in placed if cb > ctop)
            if top < ctop:
                fail.append(f'{name} {day}: {want!r} drawn at {top}px, above its clock top {ctop}px')
            if bottom < cbot:
                fail.append(f'{name} {day}: {want!r} ends at {bottom}px, before its clock end {cbot}px')
            if bottom > grid_h:
                fail.append(f'{name} {day}: {want!r} runs to {bottom}px, past the {grid_h}px grid')
            # ... indented one step per earlier block still running, by the clock ...
            want_left = min(depth, max_depth) * indent_w
            if left != want_left:
                fail.append(f'{name} {day}: {want!r} nests {depth} deep but is indented '
                            f'{left}px, want {want_left}px')
            # ... and moves down ONLY to clear text it would have covered, never further.
            floor = max((tb for _, b, tb, _ in placed if b > ctop), default=0)
            if top != max(ctop, floor):
                fail.append(f'{name} {day}: {want!r} drawn at {top}px; clock top {ctop}px, '
                            f'parent text ends {floor}px')
            for t, b, tb, _ in placed:
                if top < tb and bottom > t:
                    fail.append(f'{name} {day}: {want!r} ({top}-{bottom}) covers the text of the '
                                f'block at {t}-{tb}')
            placed.append((top, bottom, top + text_h, cbot))
        for n in re.findall(r'data-more="(\d+)"', chunk):
            more_total += int(n)

    if len(drawn) < 4:
        fail.append(f'{name}: only {len(drawn)} distinct blocks drawn')

    # Every timed fixture event inside the window is either drawn in full
    # or counted into a "+N more".
    missing = []
    for ev in EVENTS:
        if ev.get('all_day') or 'should not render' in ev['summary']:
            continue
        if ev['start_full'].split('T')[0] not in window:
            continue
        if ev['summary'] not in drawn:
            missing.append(ev['summary'])
    if len(missing) > more_total:
        fail.append(f'{name}: {len(missing)} events absent but only +{more_total} counted: '
                    f'{missing[:4]}')

if fail:
    print('\n'.join(sorted(set(fail))[:12]))
    sys.exit(1)
print('geometry OK: every block sits at its clock position, holds its full text, and covers no other text')
