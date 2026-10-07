#!/usr/bin/env bash
# Render the story. Output goes to workspace/preview/<version>/ (see README.md).
#
#   ./render.sh [quality] [version]
#
#   ./render.sh              all deliverables, final quality -> workspace/preview/<timestamp>/
#   ./render.sh draft        quick 1080p draft, both formats -> workspace/preview/<timestamp>/
#   ./render.sh draft v2     quick 1080p draft, both formats -> workspace/preview/v2/
#   ./render.sh final v2     all deliverables, final quality -> workspace/preview/v2/
#
# final: 16:9 3840x2160 + 9:16 2160x3840, 30 fps, each with music and silent, plus 1080p social copies.
# Every render also rewrites thumbnails/ and youtube-publishing.md.
# Frames render in parallel chunks: JOBS=<n> ./render.sh ... to change the number (default: CPU count).
# Renders run at low CPU priority so the computer stays responsive: NICE=0 ./render.sh ... for full priority.
set -euo pipefail
cd "$(dirname "$0")"
renice -n "${NICE:-10}" -p $$ > /dev/null   # low CPU priority (inherited by every job) keeps the machine usable; NICE=0 for full speed

NAME=$(basename "$PWD")                     # the story directory name
QUALITY=${1:-final}
VER=${2:-$(date +%Y-%m-%d_%H%M%S)}
case $QUALITY in
  final) SCALE=2; RES=4k;    FORMATS=(16x9 9x16) ;;
  draft) SCALE=1; RES=1080p; FORMATS=(16x9 9x16) ;;
  *) echo "usage: ./render.sh [draft|final] [version]  (quality comes first)" >&2; exit 1 ;;
esac
FPS=30
JOBS=${JOBS:-$(getconf _NPROCESSORS_ONLN)}

OUT=workspace/preview/$VER
TMP=workspace/tmp
mkdir -p "$OUT" "$TMP"
uv sync --frozen --quiet                      # create/verify the pinned .venv from uv.lock

render_video() {  # <format> <out.mp4>: render one format, silent, at $QUALITY
  local script=src/video.py dur=120
  [[ $1 == 9x16 ]] && script=src/short.py dur=30
  local frames=$((dur * FPS)) i pids=()
  : > "$TMP/chunks_$1.txt"
  for ((i = 0; i < JOBS; i++)); do
    local a=$((frames * i / JOBS)) b=$((frames * (i + 1) / JOBS))
    SCALE=$SCALE FPS=$FPS uv run --frozen python "$script" chunk "$a" "$b" "$TMP/chunk_$1_$i.mp4" \
      > "$TMP/render_$1_$i.log" 2>&1 &
    pids+=($!)
    echo "file 'chunk_$1_$i.mp4'" >> "$TMP/chunks_$1.txt"
  done
  for p in "${pids[@]}"; do wait "$p" || { echo "render failed for $1, see $TMP/render_$1_*.log" >&2; exit 1; }; done
  ffmpeg -v error -y -f concat -safe 0 -i "$TMP/chunks_$1.txt" -c copy "$2"
}

render_music() {  # <format> <out.wav>: the music track, matching that format's length,
                  # normalized to -14 LUFS integrated, true peak <= -1 dBTP (two-pass loudnorm)
  local script=src/music.py
  [[ $1 == 9x16 ]] && script=src/short_music.py
  uv run --frozen python "$script" "$TMP/music_raw_$1.wav"
  local m
  m=$(ffmpeg -hide_banner -i "$TMP/music_raw_$1.wav" -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 \
      | sed -n '/^{/,/^}/p' \
      | uv run --frozen python -c "import json,sys; d=json.load(sys.stdin); print(f\"measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}\")")
  ffmpeg -v error -y -i "$TMP/music_raw_$1.wav" -af "loudnorm=I=-14:TP=-1.5:LRA=11:$m:linear=true" -ar 44100 "$2"
}

render_thumbnails() {  # YouTube thumbnail stills: thumbnails/<name>-thumbnail-<design>-<aspect>.png (tracked)
  mkdir -p thumbnails
  uv run --frozen python src/thumbnails.py thumbnails > "$TMP/thumbs_16x9.log"
  uv run --frozen python src/short_thumbnails.py thumbnails > "$TMP/thumbs_9x16.log"
}

render_publishing() {  # refresh only the chapter timestamps in the hand-editable youtube-publishing.md
  uv run --frozen python src/youtube.py youtube-publishing.md
}

render_thumbnails   # first: the Short's end card shows the landscape "tree" thumbnail

for f in "${FORMATS[@]}"; do
  base=$OUT/$NAME-$VER-$f-$RES
  render_video "$f" "$TMP/video_$f.mp4"
  ffmpeg -v error -y -i "$TMP/video_$f.mp4" -c copy -movflags +faststart "$base-silent.mp4"
  render_music "$f" "$TMP/music_$f.wav"
  ffmpeg -v error -y -i "$base-silent.mp4" -i "$TMP/music_$f.wav" -map 0:v -map 1:a \
    -c:v copy -af apad -c:a aac -b:a 256k -shortest -movflags +faststart "$base.mp4"
  if [[ $QUALITY == final ]]; then   # 1080p copy for social posts (X, LinkedIn, Bluesky don't play 4K in the feed)
    hd=1920:1080; [[ $f == 9x16 ]] && hd=1080:1920
    ffmpeg -v error -y -i "$base.mp4" -vf "scale=$hd:flags=lanczos" -c:v libx264 -preset slow -crf 18 \
      -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT/$NAME-$VER-$f-1080p.mp4"
  fi
done

render_publishing

if [[ $QUALITY == final ]]; then   # a final render exports its deliverables (see AGENTS.md): same names, hard links (copy as a fallback)
  mkdir -p workspace/export
  for f in "$OUT"/*; do ln -f "$f" "workspace/export/$(basename "$f")" 2>/dev/null || cp -f "$f" workspace/export/; done
fi

ln -sfn "$VER" workspace/preview/latest
ls -la "$OUT"
