"""Readability invariants for the rendered grid.

The layout is text-first: a block is never smaller than the text it
carries, blocks slide down instead of overlapping, and the only thing
ever shortened is a title longer than the column can hold. These checks
falsify each of those claims against the .trmnlp.yml fixture.
"""
import html, pathlib, re, sys, yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = yaml.safe_load((ROOT / '.trmnlp.yml').read_text())
NODE = next(iter(FIX['variables'].values()))
EVENTS = NODE['events']
TODAY = NODE['today_in_tz'].split('T')[0]

SPAN = re.compile(r'<span class="label label--xsmall cg-line[^"]*">(.*?)</span>', re.S)
BLOCK = re.compile(
    r'<div class="cg-block[^"]*"[^>]*data-block="([\d,]+)" data-times="([^"]*)" '
    r'data-title="([^"]*)">(.*?)</div>', re.S)


def flat(s):
    return re.sub(r'\s+', ' ', html.unescape(s).replace('&nbsp;', ' ')).strip()

fail = []


def truncate(s, n):
    """Liquid's `truncate`: n chars total, the last three being '...'."""
    return s if len(s) <= n else s[:n - 3] + '...'


for f in sorted((ROOT / '_build').glob('*.html')):
    h = f.read_text()
    name = f.name

    m = re.search(r'data-title-chars="(\d+)"', h)
    if not m:
        fail.append(f'{name}: template does not report data-title-chars')
        continue
    title_chars = int(m.group(1))

    for L in re.findall(r'data-hour="\d+">([^<]*)</span>', h) or ['']:
        if not re.fullmatch(r'\d{1,2}(am|pm)', L.strip()):
            fail.append(f'{name}: clipped or odd hour label {L!r}')

    drawn, more_total = set(), 0
    cols = re.split(r'<div class="cg-col[^"]*" data-grid-col="', h)[1:]
    if not cols:
        fail.append(f'{name}: no grid columns')
    for chunk in cols:
        day = chunk.split('"', 1)[0]
        spans = []
        for geom, dtimes, dtitle, inner in BLOCK.findall(chunk):
            top, hgt, left, lines, line_h = (int(x) for x in geom.split(','))
            need = lines * line_h + 2
            if need > hgt:
                fail.append(f'{name} {day}: {lines} line(s) need {need}px, block is {hgt}px')
            if line_h < 10:
                fail.append(f'{name} {day}: line height {line_h}px is below the 10px floor')
            rendered = flat(' '.join(SPAN.findall(inner)))
            title = flat(dtitle)
            want = flat(dtimes + ' ' + title)
            if rendered != want:
                fail.append(f'{name} {day}: rendered {rendered!r} != {want!r}')
            if title.endswith('...') and len(title) != title_chars:
                fail.append(f'{name} {day}: title {title!r} shortened below the column width')
            drawn.add(want)
            spans.append((top, top + hgt, want))
        spans.sort()
        for (t1, b1, w1), (t2, b2, w2) in zip(spans, spans[1:]):
            if t2 < b1:
                fail.append(f'{name} {day}: {w1!r} and {w2!r} overlap ({t1}-{b1} vs {t2}-{b2})')
        for n in re.findall(r'data-more="(\d+)"', chunk):
            more_total += int(n)

    if len(drawn) < 4:
        fail.append(f'{name}: only {len(drawn)} distinct blocks drawn')

    # Every timed fixture event inside the window is either drawn in full
    # or counted into a "+N more".
    window = set(re.findall(r'data-grid-col="([\d-]+)"', h))
    missing = []
    for ev in EVENTS:
        if ev.get('all_day') or 'should not render' in ev['summary']:
            continue
        if ev['start_full'].split('T')[0] not in window:
            continue
        want = flat(f"{ev['start']} - {ev['end']} {truncate(ev['summary'], title_chars)}")
        if want not in drawn:
            missing.append(ev['summary'])
    if len(missing) > more_total:
        fail.append(f'{name}: {len(missing)} events absent but only +{more_total} counted: '
                    f'{missing[:4]}')

if fail:
    print('\n'.join(sorted(set(fail))[:12]))
    sys.exit(1)
print('geometry OK: every block holds its full text, nothing overlaps, nothing is clipped')
