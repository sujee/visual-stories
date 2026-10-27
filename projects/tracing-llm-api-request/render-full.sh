#!/usr/bin/env bash
# The full explainer (brief-full.md), 16:9 for now: a web page captured frame by frame. PAGE picks it: src/full/full2d.html (the default:
# one 2D map of the whole route, a camera that zooms in on each stop, and transition cards) or src/full/full.html (the 3D journey
# experiment; its 3D is drawn in software WebGL, so frames are identical on every machine); 4K (or 720p draft) with music, silent, and
# at final quality a 1080p copy with music.
#
#   ./render-full.sh [quality] [version]             (see README.md)
#
# Output: workspace/full/preview/<version>/, and workspace/full/export/ after a final render.
# Also writes the YouTube thumbnails to thumbnails/ and, at final quality, refreshes the chapters in youtube-publishing-full.md. (The Short is the promo's.)
set -euo pipefail
cd "$(dirname "$0")"
WS=workspace/full                          # the full video has its own versions (v1, v2, …), apart from the promos'
source src/shared/render-common.sh "$@"

W=3840; H=2160
[[ $QUALITY == draft ]] && { W=1280; H=720; }
base=$OUT/$NAME-$VER-16x9-$RES
PAGE=${PAGE:-src/full/full2d.html}
[[ $PAGE == *full.html ]] && flag=--3d || flag=""
[[ -z ${UNTIL:-} || $QUALITY == draft ]] || { echo "render-full.sh: UNTIL is for drafts only" >&2; exit 2; }   # UNTIL=<seconds, a scene start>: a draft of the first part only
# 10 s segments, cached by frame fingerprint: only the segments that changed since the last render are rendered again (--no-cache: all)
node src/shared/capture.mjs --page $PAGE $flag --out "$TMP/full_${VER}_16x9.mp4" --width $W --height $H --fps 30 --segments 10 --cache "$WS/cache/$RES" ${NO_CACHE:+--no-cache} ${UNTIL:+--to $UNTIL} --report "$OUT/changed.txt"
ffmpeg -v error -y -i "$TMP/full_${VER}_16x9.mp4" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -an \
  -movflags +faststart "$base-silent.mp4"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$base-silent.mp4")
[[ -n $dur ]] || { echo "render-full.sh: no duration for $base-silent.mp4" >&2; exit 1; }
music=$TMP/music_full_${VER}.wav
node src/shared/capture.mjs --page $PAGE --print-cues > "$TMP/cues_${VER}.json"    # where the music lifts and goes quiet
node src/full/music.mjs --duration "$dur" --cues "$TMP/cues_${VER}.json" --out "$music"
ffmpeg -v error -y -i "$base-silent.mp4" -i "$music" -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$base.mp4"
if [[ $QUALITY == final ]]; then      # 1080p copy for social posts
  ffmpeg -v error -y -i "$base.mp4" -vf "scale=1920:1080:flags=lanczos" -c:v libx264 -preset slow -crf 18 \
    -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT/$NAME-$VER-16x9-1080p.mp4"
fi

[[ $PAGE == *full2d.html ]] && node src/full/thumbnails.mjs                                          # the YouTube thumbnails (thumbnails/, tracked)
[[ $QUALITY == final ]] && node src/shared/capture.mjs --page $PAGE --print-chapters | node src/full/youtube.mjs youtube-publishing-full.md   # the description's chapters, from this render's timeline
finish "$OUT"/$NAME-$VER-*.mp4
ls -la "$OUT"
