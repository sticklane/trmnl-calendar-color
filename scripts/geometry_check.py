import re, sys, pathlib
fail = []
for f in sorted(pathlib.Path('_build').glob('*.html')):
    h = f.read_text()
    labels = re.findall(r'data-hour="\d+">([^<]*)</span>', h)
    if not labels:
        fail.append(f"{f.name}: no hour labels"); continue
    for L in labels:
        if not re.fullmatch(r'\d{1,2}[ap]', L.strip()):
            fail.append(f"{f.name}: clipped/odd hour label {L!r}")
    # per grid column, blocks must not intersect
    cols = h.split('data-grid-col="')[1:]
    for c in cols:
        key = c[:10]
        seg = c.split('</div>\n        {%')[0]
        blocks = re.findall(r'top:(\d+)px;height:(\d+)px;left:(\d+)%;width:(\d+)%', seg)
        rects = [(int(t), int(t)+int(hh), int(l), int(l)+int(w)) for t,hh,l,w in blocks]
        for i in range(len(rects)):
            for j in range(i+1, len(rects)):
                a, b = rects[i], rects[j]
                if a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]:
                    fail.append(f"{f.name} {key}: blocks intersect {a} vs {b}")
if fail:
    print("\n".join(fail[:12])); sys.exit(1)
print("geometry OK: no intersecting blocks, all hour labels well formed")
