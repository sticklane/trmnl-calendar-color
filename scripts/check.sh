#!/usr/bin/env bash
# Canonical repo check: lint the plugin, then render every layout.
# Uses the local trmnlp gem when installed, otherwise the Docker image
# (bin/trmnlp picks whichever is available).
set -euo pipefail

cd "$(dirname "$0")/.."

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
    # One column per day in the window, today first, no duplicates.
    cols=$(grep -o 'data-day-col="[^"]*"' "$out" | sort)
    n=$(echo "$cols" | wc -l | tr -d ' ')
    [ "$n" -ge 2 ] || { echo "FAIL: $out rendered $n day columns, want >= 2"; exit 1; }
    [ "$(echo "$cols" | uniq | wc -l | tr -d ' ')" = "$n" ] || { echo "FAIL: $out repeats a day column"; exit 1; }
    grep -q 'data-day-col="2026-09-07"' "$out" || { echo "FAIL: $out has no column for today"; exit 1; }
    grep -q 'label--filled" data-day-header' "$out" || { echo "FAIL: $out does not highlight today"; exit 1; }

    # today_in_tz arrives as a full ISO timestamp from the live merge
    # variable, so the day key has to be normalized before any date math.
    grep -q 'data-day-col="2026-09-08"' "$out" || { echo "FAIL: $out day math did not advance a day"; exit 1; }

    # The window is today..today+N. Anything outside it must not render.
    if grep -q 'should not render' "$out"; then
        echo "FAIL: $out shows an event outside the day window"; exit 1
    fi

    # A multi-day all-day event has to repeat in every day it covers,
    # and all-day rows lead their column.
    [ "$(grep -c "Cousin Pam" "$out")" -ge 2 ] || { echo "FAIL: $out does not span a multi-day all-day event"; exit 1; }
done

echo "OK: lint clean, 4 layouts rendered from the .trmnlp.yml fixture"
