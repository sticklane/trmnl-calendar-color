#!/usr/bin/env bash
# Canonical repo check: lint the plugin, then render every layout.
# Uses the local trmnlp gem when installed, otherwise the Docker image
# (bin/trmnlp picks whichever is available).
set -euo pipefail

cd "$(dirname "$0")/.."
fixture_backup="$(mktemp -t trmnlp-fixture)"

python3 scripts/gen_layouts.py --check
./bin/trmnlp lint
./bin/trmnlp build

for layout in full half_horizontal half_vertical quadrant; do
    out="_build/${layout}.html"
    [ -s "$out" ] || { echo "FAIL: $out missing or empty"; exit 1; }
    if grep -q 'invalid JSON in static_data\|Liquid error\|Liquid syntax error' "$out"; then
        echo "FAIL: $out contains a render error"
        grep -o 'invalid JSON in static_data\|Liquid[^<]*' "$out" | head -3
        exit 1
    fi
    # A time grid, not a list: hour axis, one grid column per day, and
    # every timed event an absolutely positioned block.
    hours=$(grep -o 'data-hour=' "$out" | wc -l | tr -d ' ')
    [ "$hours" -ge 4 ] || { echo "FAIL: $out has $hours hour labels, want >= 4"; exit 1; }
    cols=$(grep -o 'data-grid-col="[^"]*"' "$out" | sort)
    n=$(echo "$cols" | wc -l | tr -d ' ')
    [ "$n" -ge 2 ] || { echo "FAIL: $out rendered $n grid columns, want >= 2"; exit 1; }
    [ "$(echo "$cols" | uniq | wc -l | tr -d ' ')" = "$n" ] || { echo "FAIL: $out repeats a grid column"; exit 1; }
    grep -q 'data-grid-col="2026-09-07"' "$out" || { echo "FAIL: $out has no column for today"; exit 1; }
    grep -q 'data-grid-col="2026-09-08"' "$out" || { echo "FAIL: $out day math did not advance a day"; exit 1; }
    grep -q 'label--filled" data-day-header' "$out" || { echo "FAIL: $out does not highlight today"; exit 1; }

    blocks=$(grep -o 'data-block=' "$out" | wc -l | tr -d ' ')
    [ "$blocks" -ge 4 ] || { echo "FAIL: $out placed $blocks blocks, want >= 4"; exit 1; }
    grep -q 'data-allday="true"' "$out" || { echo "FAIL: $out has no all-day band entries"; exit 1; }

    # Block geometry lives in a generated stylesheet, one rule per block:
    # trmnlp's lint scans the markup for CSS property names and allows six
    # across the four layouts, so it cannot go in style attributes.
    grep -qE '\.cg-b[0-9]+\{top:[0-9]+px;height:[0-9]+px\}' "$out" || { echo "FAIL: $out blocks are not time-positioned"; exit 1; }
    [ "$(grep -oE 'top:[0-9]+px;height:[0-9]+px' "$out" | sort -u | wc -l | tr -d ' ')" -ge 3 ] || {
        echo "FAIL: $out blocks all share one geometry"; exit 1; }

    # Every block carries a calendar fill and black-or-white text.
    grep -qE 'cg-block cg-b[0-9]+ bg--' "$out" || { echo "FAIL: $out blocks are not filled with a calendar colour"; exit 1; }
    grep -qE 'cg-line text--(white|black)' "$out" || { echo "FAIL: $out block text has no contrast class"; exit 1; }
    if grep -oE 'cg-line text--[a-z0-9-]+' "$out" | grep -vqE 'text--(white|black)$'; then
        echo "FAIL: $out prints block text in a colour other than black or white"; exit 1
    fi
    # The wide layouts name each calendar next to its colour swatch.
    case "$layout" in
        full|half_horizontal)
            grep -q 'data-legend="' "$out" || { echo "FAIL: $out legend does not show the calendar colours"; exit 1; } ;;
    esac

    # Crispness: the B/W/R/Y panel has four solid inks and dithers
    # everything else into speckle, so nothing may ask for a grey, a
    # translucency or a half-tone. Hairlines only, on whole pixels.
    if grep -oE '(bg|text|border)--gray-[0-9]+' "$out" | head -1 | grep -q .; then
        echo "FAIL: $out uses a grey token, which dithers on a 4-colour panel"
        grep -oE '(bg|text|border)--gray-[0-9]+' "$out" | sort -u | head -3; exit 1
    fi
    if grep -qE 'opacity:|rgba\(|#(999|ccc|eee|888|666|aaa)' "$out"; then
        echo "FAIL: $out uses a translucency or an off-palette grey"
        grep -oE 'opacity:[^;]*|rgba\([^)]*\)|#(999|ccc|eee|888|666|aaa)' "$out" | sort -u | head -3
        exit 1
    fi
    if grep -qE 'style="[^"]*(top|height):[0-9]*\.[0-9]' "$out"; then
        echo "FAIL: $out places a block on a fractional pixel"; exit 1
    fi
    # Whole-pixel columns: the axis must divide the panel exactly.
    grep -qE -- '--cg-col-w:[0-9]+px' "$out" || { echo "FAIL: $out has no whole-pixel column width"; exit 1; }

    # Headers + all-day band + grid + title bar must fit the panel. TRMNL
    # centres an overflowing view, so anything over budget loses the day
    # headers off the TOP rather than clipping at the bottom.
    panel=$(grep -o 'data-panel-h="[0-9]*"' "$out" | head -1 | grep -o '[0-9]*')
    total=$(grep -o 'data-total-h="[0-9]*"' "$out" | head -1 | grep -o '[0-9]*')
    [ -n "$panel" ] && [ -n "$total" ] || { echo "FAIL: $out does not report its height budget"; exit 1; }
    [ "$total" -le "$panel" ] || { echo "FAIL: $out wants ${total}px of a ${panel}px panel - the header row will be clipped"; exit 1; }

    # The window is today..today+N; anything outside it must not render.
    if grep -q 'should not render' "$out"; then
        echo "FAIL: $out shows an event outside the day window"; exit 1
    fi
done

python3 scripts/geometry_check.py || exit 1

# Second pass: AXIS_MODE=day. The budget assertion is deliberately not
# repeated - a 24-hour axis cannot fit a half-height panel at a legible
# hour pitch, and the rule is to keep the range and clip at the bottom,
# which align-self:flex-start on .cg-wrap guarantees.
cp .trmnlp.yml "$fixture_backup"
trap 'cp "$fixture_backup" .trmnlp.yml; rm -f "$fixture_backup"' EXIT
sed -i '' 's/axis_mode: fit/axis_mode: day/' .trmnlp.yml
./bin/trmnlp build >/dev/null
for layout in full half_horizontal half_vertical quadrant; do
    out="_build/${layout}.html"
    grep -q 'data-axis-start="0" data-axis-end="24"' "$out" || {
        echo "FAIL: $out did not honour AXIS_MODE=day"; exit 1; }
done
grep -q 'data-hour="0" data-hour-y="0">12am' _build/full.html || { echo "FAIL: day axis does not start at 12am"; exit 1; }
grep -qE 'data-hour="24" data-hour-y="[0-9]+">12am' _build/full.html || { echo "FAIL: day axis does not label midnight at its end"; exit 1; }
python3 scripts/geometry_check.py || exit 1

cp "$fixture_backup" .trmnlp.yml
rm -f "$fixture_backup"
trap - EXIT
./bin/trmnlp build >/dev/null

echo "OK: lint clean, both axis modes rendered from the .trmnlp.yml fixture"
