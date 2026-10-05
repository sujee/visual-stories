#!/usr/bin/env bash
# Render the story. Output goes to workspace/preview/<version>/ (see README.md).
#
#   ./render.sh [quality] [version]
#
#   ./render.sh              all deliverables, final quality -> workspace/preview/<timestamp>/
#   ./render.sh draft        quick draft                     -> workspace/preview/<timestamp>/
#   ./render.sh draft v2     quick draft                     -> workspace/preview/v2/
#   ./render.sh final v2     all deliverables, final quality -> workspace/preview/v2/
#
# Template: fill in the TODOs; the rest follows the Render Interface in AGENTS.md.
set -euo pipefail
cd "$(dirname "$0")"
renice -n "${NICE:-10}" -p $$ > /dev/null   # low CPU priority (inherited by every job) keeps the machine usable; NICE=0 for full speed

NAME=$(basename "$PWD")                     # the story directory name
QUALITY=${1:-final}
VER=${2:-$(date +%Y-%m-%d_%H%M%S)}
case $QUALITY in
  final) RES=4k;   FORMATS=(16x9 9x16) ;;
  draft) RES=720p; FORMATS=(16x9 9x16) ;;   # a draft may render only the main format
  *) echo "usage: ./render.sh [draft|final] [version]  (quality comes first)" >&2; exit 1 ;;
esac

OUT=workspace/preview/$VER
TMP=workspace/tmp
mkdir -p "$OUT" "$TMP"
# TODO: install/verify locked dependencies, e.g. `uv sync --frozen --quiet` or `npm ci`

render_video() {  # <format> <out.mp4>: render one format, silent, at $QUALITY
  echo "TODO: render_video in render.sh" >&2; exit 1
}

render_music() {  # <format> <out.wav>: the music track, matching that format's length,
                  # normalized to about -14 LUFS integrated, true peak <= -1 dBTP (see AGENTS.md)
  echo "TODO: render_music in render.sh" >&2; exit 1
}

render_thumbnails() {  # YouTube thumbnail stills: thumbnails/<name>-thumbnail-<design>-<aspect>.png (tracked)
                       # (see AGENTS.md). Delete this, and its call below, if the brief doesn't ask for them.
  echo "TODO: render_thumbnails in render.sh" >&2; exit 1
}

render_publishing() {  # refresh only the chapters between "Chapters:" and "---" in the hand-editable
                       # youtube-publishing.md, from this render's own timeline (see AGENTS.md). Delete this,
                       # and its call below, if the brief doesn't ask for a YouTube publishing guide.
                       # projects/linux-history/src/youtube.py is a working example.
  echo "TODO: render_publishing in render.sh" >&2; exit 1
}

for f in "${FORMATS[@]}"; do
  base=$OUT/$NAME-$VER-$f-$RES
  render_video "$f" "$TMP/video_$f.mp4"
  ffmpeg -v error -y -i "$TMP/video_$f.mp4" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
    -movflags +faststart "$base-silent.mp4"
  render_music "$f" "$TMP/music_$f.wav"
  ffmpeg -v error -y -i "$base-silent.mp4" -i "$TMP/music_$f.wav" -map 0:v -map 1:a \
    -c:v copy -af apad -c:a aac -b:a 256k -shortest -movflags +faststart "$base.mp4"
  if [[ $QUALITY == final ]]; then   # 1080p copy for social posts; delete this block if the brief doesn't ask for one
    hd=1920:1080; [[ $f == 9x16 ]] && hd=1080:1920
    ffmpeg -v error -y -i "$base.mp4" -vf "scale=$hd:flags=lanczos" -c:v libx264 -preset slow -crf 18 \
      -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT/$NAME-$VER-$f-1080p.mp4"
  fi
done

render_thumbnails
render_publishing

ln -sfn "$VER" workspace/preview/latest
ls -la "$OUT"
