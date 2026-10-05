#!/usr/bin/env bash
# Render the story. Output goes to workspace/preview/<version>/ (see README.md).
#
#   ./render.sh [quality] [version]
#
#   ./render.sh              all deliverables, final quality -> workspace/preview/<timestamp>/
#   ./render.sh draft        quick 720p draft, both formats  -> workspace/preview/<timestamp>/
#   ./render.sh draft v6     quick 720p draft, both formats  -> workspace/preview/v6/
#   ./render.sh final v6     all deliverables, final quality -> workspace/preview/v6/
#
# final: 16:9 3840x2160 + 9:16 2160x3840, 30 fps, each with music and silent.
set -euo pipefail
cd "$(dirname "$0")"
renice -n "${NICE:-10}" -p $$ > /dev/null   # low CPU priority (inherited by every job) keeps the machine usable; NICE=0 for full speed

NAME=jev-vs-llm
QUALITY=${1:-final}
VER=${2:-$(date +%Y-%m-%d_%H%M%S)}
case $QUALITY in
  final) MANIM_Q=(-qk --frame_rate 30); RES=4k;   ORIENTS=(landscape portrait) ;;
  draft) MANIM_Q=(-qm);                 RES=720p; ORIENTS=(landscape portrait) ;;
  *) echo "usage: ./render.sh [draft|final] [version]  (quality comes first)" >&2; exit 1 ;;
esac

OUT=workspace/preview/$VER
TMP=workspace/tmp
mkdir -p "$OUT" "$TMP"
uv sync --frozen --quiet                      # create/verify the pinned .venv from uv.lock

render() {  # <orient>: render one format, print the path of the raw video
  local media=$TMP/media_$1
  rm -rf "$media"
  JEV_ORIENT=$1 uv run --frozen manim "${MANIM_Q[@]}" --disable_caching --progress_bar none \
    --media_dir "$media" -o scene src/scene.py JevExplainer > "$TMP/render_$1.log" 2>&1
  find "$media/videos" -name scene.mp4 -not -path "*partial*" | head -1
}

for o in "${ORIENTS[@]}"; do render "$o" > "$TMP/path_$o" & done   # formats render in parallel
wait

for o in "${ORIENTS[@]}"; do
  src=$(cat "$TMP/path_$o")
  [[ -n $src ]] || { echo "render failed for $o, see $TMP/render_$o.log" >&2; exit 1; }
  aspect=16x9; [[ $o == portrait ]] && aspect=9x16
  base=$OUT/$NAME-$VER-$aspect-$RES
  ffmpeg -v error -y -i "$src" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart \
    "$base-silent.mp4"
  uv run --frozen python src/music.py "$TMP/events_$o.json" "$TMP/music_$o.wav"   # normalized to -14 LUFS
  ffmpeg -v error -y -i "$base-silent.mp4" -i "$TMP/music_$o.wav" -map 0:v -map 1:a \
    -c:v copy -af apad -c:a aac -b:a 256k -shortest -movflags +faststart "$base.mp4"
  if [[ $QUALITY == final ]]; then   # 1080p copy for posting on X / LinkedIn (they don't play 4K in the feed)
    hd=1920:1080; [[ $o == portrait ]] && hd=1080:1920
    ffmpeg -v error -y -i "$base.mp4" -vf "scale=$hd:flags=lanczos" -c:v libx264 -preset slow -crf 18 \
      -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT/$NAME-$VER-$aspect-1080p.mp4"
  fi
done

# YouTube thumbnails: three designs (see JevThumbnail in src/scene.py), both formats, as stills.
# Tracked in Git (thumbnails/) so they can be shared without rendering; rewritten by every render.
thumb() {  # <orient> <design> <out.png>
  local media=$TMP/thumb_$1_$2 res=1280,720
  [[ $1 == portrait ]] && res=1920,1080          # scene.py turns this into 1080x1920
  rm -rf "$media"
  JEV_ORIENT=$1 JEV_THUMB=$2 uv run --frozen manim -s -r "$res" --disable_caching --progress_bar none \
    --media_dir "$media" -o thumb src/scene.py JevThumbnail > "$TMP/thumb_$1_$2.log" 2>&1
  cp "$(find "$media/images" -name 'thumb*.png' | head -1)" "$3"
}
mkdir -p thumbnails
for d in a b c; do
  thumb landscape "$d" "thumbnails/$NAME-thumbnail-$d-16x9.png" &
  thumb portrait  "$d" "thumbnails/$NAME-thumbnail-$d-9x16.png" &
done
wait
for d in a b c; do for a in 16x9 9x16; do
  [[ -s thumbnails/$NAME-thumbnail-$d-$a.png ]] || { echo "thumbnail $d $a failed, see $TMP/thumb_*.log" >&2; exit 1; }
done; done

# YouTube publishing guide: upload steps + descriptions, with chapters taken from the landscape timeline
# (so they always match the video). Tracked in Git and rewritten by every render.
uv run --frozen python src/youtube.py "$TMP/events_landscape.json" "$TMP/events_portrait.json" \
  > youtube-publishing.md

ln -sfn "$VER" workspace/preview/latest
ls -la "$OUT"
