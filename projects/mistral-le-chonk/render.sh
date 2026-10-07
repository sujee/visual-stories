#!/usr/bin/env bash
# Render the story. Output goes to workspace/preview/<version>/ (see README.md).
#
#   ./render.sh [quality] [version]
#
#   ./render.sh              all deliverables, final quality -> workspace/preview/<timestamp>/
#   ./render.sh draft        quick 720p drafts               -> workspace/preview/<timestamp>/
#   ./render.sh draft v2     quick 720p drafts               -> workspace/preview/v2/
#   ./render.sh final v2     all deliverables, final quality -> workspace/preview/v2/
#
# final, per format (landscape 16:9 and vertical 9:16), 30 fps:
#   4K master with the quiet piano, 4K silent master, and a 1080p copy with the piano
#   (landscape 3840x2160 / 1920x1080; vertical 2160x3840 / 1080x1920), plus a clean still of the final scene (no confetti) at the master size.
# Every render also rewrites thumbnails/ (two designs x two formats); a final render also copies the 4K stills there as <name>-still-<aspect>.png (no version in the name). A final render also hard-links its deliverables into workspace/export/.
# draft: 720p, both formats (landscape 1280x720, vertical 720x1280), with the piano and silent.
set -euo pipefail
cd "$(dirname "$0")"
renice -n "${NICE:-10}" -p $$ > /dev/null   # low CPU priority (inherited by every job) keeps the machine usable; NICE=0 for full speed

NAME=$(basename "$PWD")
QUALITY=${1:-final}
VER=${2:-$(date +%Y-%m-%d_%H%M%S)}
case $QUALITY in
  final) RES=4k;   W16=3840; H16=2160; W9=2160; H9=3840 ;;
  draft) RES=720p; W16=1280; H16=720;  W9=720;  H9=1280 ;;
  *) echo "usage: ./render.sh [draft|final] [version]  (quality comes first)" >&2; exit 1 ;;
esac

OUT=workspace/preview/$VER
TMP=workspace/tmp
mkdir -p "$OUT" "$TMP" thumbnails
npm ci --silent                                # the pinned Playwright (Chromium: `npx playwright install chromium`, see README)

for f in 16x9 9x16; do
  if [[ $f == 16x9 ]]; then W=$W16; H=$H16; FLAG=""; HD=1920:1080; else W=$W9; H=$H9; FLAG="--portrait"; HD=1080:1920; fi
  base=$OUT/$NAME-$VER-$f-$RES
  node src/capture.mjs --out "$TMP/video_$f.mp4" --width $W --height $H --fps 30 $FLAG
  ffmpeg -v error -y -i "$TMP/video_$f.mp4" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -an \
    -movflags +faststart "$base-silent.mp4"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/video_$f.mp4")
  node src/music.mjs --duration "$DUR" --out "$TMP/music_$f.wav"      # very quiet piano, about -20 LUFS (see brief.md)
  ffmpeg -v error -y -i "$base-silent.mp4" -i "$TMP/music_$f.wav" -map 0:v -map 1:a \
    -c:v copy -af apad -c:a aac -b:a 256k -shortest -movflags +faststart "$base.mp4"
  node src/capture.mjs --out "$OUT/$NAME-$VER-$f-$RES-still.png" --width $W --height $H --at end --still $FLAG   # clean final scene, no confetti, for screenshots
  if [[ $QUALITY == final ]]; then               # the tracked copy of the still has no version in its name (a draft never overwrites it)
    cp -f "$OUT/$NAME-$VER-$f-$RES-still.png" "thumbnails/$NAME-still-$f.png"
  fi
  if [[ $QUALITY == final ]]; then             # 1080p copy (with the piano) for social posts (see the brief)
    ffmpeg -v error -y -i "$base.mp4" -vf "scale=$HD:flags=lanczos" -c:v libx264 -preset slow -crf 18 \
      -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT/$NAME-$VER-$f-1080p.mp4"
  fi
done

# YouTube thumbnails (tracked, rewritten by every render): thumbnails/<name>-thumbnail-<design>-<aspect>.png,
# 1280x720 for 16:9 and 1080x1920 for 9:16, each under 2 MB. Two designs: lineup (title) and question (hook).
for design in lineup question; do
  node src/capture.mjs --out "thumbnails/$NAME-thumbnail-$design-16x9.png" --width 1280 --height 720 --at end --thumb $design
  node src/capture.mjs --out "thumbnails/$NAME-thumbnail-$design-9x16.png" --width 1080 --height 1920 --at end --thumb $design --portrait
done
for t in thumbnails/*thumbnail*.png; do [[ $(wc -c < "$t") -lt 2000000 ]] || { echo "thumbnail over 2 MB: $t" >&2; exit 1; }; done

if [[ $QUALITY == final ]]; then               # a final render exports its deliverables (see AGENTS.md): same names, hard links
  mkdir -p workspace/export
  for f in "$OUT"/*; do ln -f "$f" "workspace/export/$(basename "$f")" 2>/dev/null || cp -f "$f" workspace/export/; done
  echo "exported to workspace/export/"
fi

ln -sfn "$VER" workspace/preview/latest
ls -la "$OUT"
