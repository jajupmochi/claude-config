#!/usr/bin/env bash
set -euo pipefail
# Screenshot-based visual verification for non-vision models (e.g., DeepSeek).
# Captures screenshots at specified viewports using Playwright or headless Chrome.
# Does NOT attempt AI analysis — saves files for manual review or external tools.

input="$(cat || true)"

# Parse parameters from event or environment
url=""
if command -v jq >/dev/null 2>&1; then
  url="$(printf '%s' "$input" | jq -r '.tool_input.url // .url // .args.url // empty' 2>/dev/null || true)"
fi

# Configurable viewports
VIEWPORTS="${VISUAL_VERIFY_VIEWPORTS:-1280x720 375x812}"
OUTDIR="${VISUAL_VERIFY_OUTDIR:-./.visual-verify/$(date +%Y-%m-%d_%H%M%S)}"
TIMEOUT_MS="${VISUAL_VERIFY_TIMEOUT:-15000}"

if [ -z "$url" ]; then
  echo '{"systemMessage":"[visual-verify] No URL provided. Use /verify-visual <url> or set VISUAL_VERIFY_URL.","decision":""}'
  exit 0
fi

mkdir -p "$OUTDIR"

# Try Playwright first, fall back to headless Chrome
screenshot_tool=""
if command -v npx >/dev/null 2>&1 && npx playwright --version >/dev/null 2>&1; then
  screenshot_tool="playwright"
elif command -v google-chrome >/dev/null 2>&1; then
  screenshot_tool="chrome"
elif command -v chromium-browser >/dev/null 2>&1; then
  screenshot_tool="chromium"
fi

if [ -z "$screenshot_tool" ]; then
  jq -n --arg url "$url" '{
    systemMessage: ("[visual-verify] No screenshot tool available (playwright/chrome/chromium). Install: npx playwright install chromium. URL: "+$url),
    decision: "block",
    reason: "Cannot capture screenshots without a browser."
  }'
  exit 0
fi

results_file="$OUTDIR/results.json"
echo "[]" > "$results_file"

for vp in $VIEWPORTS; do
  w="${vp%x*}"
  h="${vp#*x}"
  outfile="$OUTDIR/screenshot-${url##*/}-${w}x${h}.png"

  case "$screenshot_tool" in
    playwright)
      npx playwright screenshot --viewport "${w},${h}" "$url" "$outfile" --timeout "$TIMEOUT_MS" 2>/dev/null || true
      ;;
    chrome|chromium)
      "$screenshot_tool" --headless --disable-gpu --no-sandbox \
        --window-size="${w},${h}" --screenshot="$outfile" --timeout="$((TIMEOUT_MS / 1000))" "$url" 2>/dev/null || true
      ;;
  esac

  if [ -f "$outfile" ]; then
    size="$(stat -c%s "$outfile" 2>/dev/null || stat -f%z "$outfile" 2>/dev/null || echo 0)"
    if [ "$size" -gt 100 ]; then
      # Append to results
      tmp="$(mktemp)"
      jq --arg vp "${w}x${h}" --arg path "$outfile" --arg size "$size" \
        '. + [{"viewport":$vp,"path":$path,"size_bytes":($size|tonumber),"url":$url}]' "$results_file" > "$tmp" && mv "$tmp" "$results_file"
    fi
  fi
done

captured="$(jq 'length' "$results_file" 2>/dev/null || echo 0)"
jq -n --arg count "$captured" --arg dir "$OUTDIR" --arg url "$url" '{
  systemMessage: ("[visual-verify] Captured ($count) screenshot(s) for "+$url+". Saved to "+$dir+"." + (if ($count|tonumber) == 0 then " WARNING: all attempts failed." else "" end)),
  decision: ""
}'
