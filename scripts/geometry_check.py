"""Geometry invariants for the rendered grid.

An event is drawn as a duration BAR plus a TEXT ENTRY anchored at its
start time. The bars carry the timing truth, so they must never overlap
inside a column; the entries carry the words, so within one lane their y
ranges must be disjoint or the text overprints and neither is readable.
"""
import re, sys, pathlib

fail = []
for f in sorted(pathlib.Path('_build').glob('*.html')):
    h = f.read_text()

    labels = re.findall(r'data-hour="\d+">([^<]*)</span>', h)
    if not labels:
        fail.append(f"{f.name}: no hour labels")
    for L in labels:
        if not re.fullmatch(r'\d{1,2}(am|pm)', L.strip()):
            fail.append(f"{f.name}: clipped/odd hour label {L!r}")

    cols = h.split('data-grid-col="')[1:]
    if not cols:
        fail.append(f"{f.name}: no grid columns")
    for c in cols:
        key = c[:10]
        seg = c.split('data-grid-col="')[0]

        def rects(attr):
            out = []
            for g in re.findall(attr + r'="([\d,]+)"', seg):
                t, hh, l, w = (int(x) for x in g.split(','))
                out.append((t, t + hh, l, l + w))
            return out

        bars = rects('data-bar-geom')
        for i in range(len(bars)):
            for j in range(i + 1, len(bars)):
                a, b = bars[i], bars[j]
                if a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]:
                    fail.append(f"{f.name} {key}: bars intersect {a} vs {b}")

        lanes = {}
        for lane, g in re.findall(r'data-entry="(-?\d+)" data-entry-geom="([\d,]+)"', seg):
            t, hh, _l, _w = (int(x) for x in g.split(','))
            lanes.setdefault(lane, []).append((t, t + hh))
        for lane, spans in lanes.items():
            spans.sort()
            for (t1, b1), (t2, b2) in zip(spans, spans[1:]):
                if t2 < b1:
                    fail.append(
                        f"{f.name} {key} lane {lane}: entries overprint "
                        f"[{t1},{b1}) vs [{t2},{b2})")

if fail:
    print("\n".join(fail[:12]))
    sys.exit(1)
print("geometry OK: bars disjoint, no entry overprints, hour labels well formed")
