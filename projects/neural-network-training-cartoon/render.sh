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

NAME=neural-network-training-cartoon
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
  NN_ORIENT=$1 uv run --frozen manim "${MANIM_Q[@]}" --disable_caching --progress_bar none \
    --media_dir "$media" -o scene src/scene.py NeuralNet > "$TMP/render_$1.log" 2>&1
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
done

ln -sfn "$VER" workspace/preview/latest
ls -la "$OUT"
