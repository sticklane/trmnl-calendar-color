"""Geometry invariants for the rendered grid.

Blocks are solid fills that deliberately OVERLAY one another when events
overlap, mirroring the native render, so intersection is not an error
here. What must hold is that every block is tall enough for the text it
was given, and that the hour axis is not clipping its labels.
"""
import re, sys, pathlib

MIN_BLOCK_H = 14
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

    blocks = re.findall(r'data-block="([\d,]+)"', h)
    if len(blocks) < 4:
        fail.append(f"{f.name}: only {len(blocks)} blocks drawn")
    for g in blocks:
        top, hgt, left, lines, line_h = (int(x) for x in g.split(','))
        if hgt < MIN_BLOCK_H:
            fail.append(f"{f.name}: block height {hgt} below the one-line minimum {MIN_BLOCK_H}")
        # the text has to fit inside the fill, borders included
        need = lines * line_h + 2
        if need > hgt:
            fail.append(f"{f.name}: {lines} line(s) need {need}px but block is {hgt}px")
        if left < 0 or left > 100:
            fail.append(f"{f.name}: block left {left}% off the column")
        # a cascaded block must keep a usable width
        if 100 - left < 55:
            fail.append(f"{f.name}: block at left {left}% leaves under 55% width")

if fail:
    print("\n".join(sorted(set(fail))[:12]))
    sys.exit(1)
print("geometry OK: blocks clear the one-line minimum, text fits, labels well formed")
