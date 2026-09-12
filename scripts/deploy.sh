#!/usr/bin/env bash
# Deploy the four generated layouts to one or more private plugins on
# usetrmnl.com, through the same archive endpoint the official trmnlp CLI
# uses. For each plugin the script downloads the server's own archive, so
# the server's settings.yml (strategy, custom fields, their values) stays
# the truth, swaps in the four *.liquid files from src/ with the
# merge-variable node name filled in, and uploads the archive back.
#
# Needs:
#   TRMNL_API_KEY   in the environment. Get it from https://trmnl.com/account
#                   (it starts with user_). Never write it into a file here.
#   deploy.env      next to this repo's root, untracked:
#                     PLUGIN_IDS="123456 234567"     # each plugin to update
#                     NODE="google_calendar_123456"  # the merge variable node
#   curl, unzip, zip.
#
# Usage:
#   scripts/deploy.sh            run the gate, then deploy to every id
#   scripts/deploy.sh --dry-run  build the archives under _deploy/ and stop
#   scripts/deploy.sh --skip-check
set -euo pipefail
cd "$(dirname "$0")/.."

dry_run=false; skip_check=false
for arg in "$@"; do
    case "$arg" in
        --dry-run) dry_run=true ;;
        --skip-check) skip_check=true ;;
        *) echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done

[ -f deploy.env ] || { echo "deploy.env is missing; see the header of $0" >&2; exit 2; }
# shellcheck disable=SC1091
source deploy.env
: "${PLUGIN_IDS:?deploy.env must set PLUGIN_IDS}"
: "${NODE:?deploy.env must set NODE}"
if ! $dry_run; then : "${TRMNL_API_KEY:?set TRMNL_API_KEY in the environment}"; fi
api="${TRMNL_API:-https://trmnl.com/api}"

$skip_check || ./scripts/check.sh

rm -rf _deploy; mkdir -p _deploy
for id in $PLUGIN_IDS; do
    dir="_deploy/$id"; mkdir -p "$dir/archive"
    if $dry_run; then
        echo "dry run: not downloading plugin $id; archive holds the layouts only"
    else
        curl -fsS -H "Authorization: Bearer $TRMNL_API_KEY" "$api/plugin_settings/$id/archive" -o "$dir/server.zip"
        unzip -q -o "$dir/server.zip" -d "$dir/archive"
        [ -f "$dir/archive/settings.yml" ] || { echo "plugin $id: the server archive has no settings.yml; not touching it" >&2; exit 1; }
    fi
    for layout in full half_horizontal half_vertical quadrant; do
        sed "s/assign src = google_calendar_12345/assign src = $NODE/" "src/$layout.liquid" > "$dir/archive/$layout.liquid"
    done
    (cd "$dir/archive" && zip -q -r ../upload.zip .)
    if $dry_run; then
        echo "built $dir/upload.zip"; continue
    fi
    curl -fsS -X POST -H "Authorization: Bearer $TRMNL_API_KEY" -F "file=@$dir/upload.zip;type=application/zip" \
        "$api/plugin_settings/$id/archive" -o "$dir/response.json"
    echo "plugin $id: uploaded $(grep -o "assign src = $NODE" "$dir/archive/full.liquid" | wc -l | tr -d ' ') node reference(s); $(wc -c < "$dir/upload.zip" | tr -d ' ') bytes"
done
echo "Force Refresh each plugin on its settings page to see the new render."
