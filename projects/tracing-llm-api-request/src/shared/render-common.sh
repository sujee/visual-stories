# Sourced by render-promo.sh and render-full.sh: the Render Interface from AGENTS.md (arguments, output folder,
# low CPU priority, dependencies, export). Not meant to be run on its own. The caller sets WS, its workspace folder
# (workspace/promo for the promos, workspace/full for the full video), so each part has its own versions v1, v2, …
renice -n "${NICE:-10}" -p $$ > /dev/null   # low CPU priority (inherited by every job) keeps the machine usable; NICE=0 for full speed

NAME=$(basename "$PWD")                     # the story directory name
QUALITY=${1:-final}
VER=${2:-$(date +%Y-%m-%d_%H%M%S)}
case $QUALITY in
  final) RES=4k ;;
  draft) RES=720p ;;
  *) echo "usage: $0 [draft|final] [version]  (quality comes first)" >&2; exit 1 ;;
esac

WS=${WS:?the caller sets WS}
OUT=$WS/preview/$VER
TMP=$WS/tmp
mkdir -p "$OUT" "$TMP"
npm ci --silent                             # pinned Playwright and three.js (Chromium: `npx playwright install chromium`, see README)

# finish <glob>...: after a final render, export the deliverables matching the globs (in $OUT) to $WS/export/
# (hard links, copies as a fallback), and the thumbnails in thumbnails/ to $WS/export/thumbnails/, then point $WS/preview/latest at this version.
finish() {
  if [[ $QUALITY == final ]]; then
    mkdir -p "$WS/export"
    local f
    for f in "$@"; do ln -f "$f" "$WS/export/$(basename "$f")" 2>/dev/null || cp -f "$f" "$WS/export/"; done
    mkdir -p "$WS/export/thumbnails"
    for f in thumbnails/*.png; do [[ -e $f ]] && { ln -f "$f" "$WS/export/thumbnails/$(basename "$f")" 2>/dev/null || cp -f "$f" "$WS/export/thumbnails/"; }; done
  fi
  ln -sfn "$VER" "$WS/preview/latest"
}
