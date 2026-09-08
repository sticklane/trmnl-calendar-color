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
    grep -q 'group-header' "$out" || { echo "FAIL: $out rendered no day headers"; exit 1; }
    # today_in_tz arrives as a full ISO timestamp from the live merge
    # variable, so the day-key comparison has to normalize it. Without
    # that, the Today highlight silently never fires.
    grep -q 'Today ·' "$out" || { echo "FAIL: $out rendered no Today header"; exit 1; }
    # The live merge variable does NOT hand back a sorted array, despite
    # the README's assumption, so each day must still appear exactly once.
    dupes=$(grep -o 'data-group-header="true">[^<]*' "$out" | sort | uniq -d)
    [ -z "$dupes" ] || { echo "FAIL: $out repeats a day header: $dupes"; exit 1; }
done

echo "OK: lint clean, 4 layouts rendered from the .trmnlp.yml fixture"
