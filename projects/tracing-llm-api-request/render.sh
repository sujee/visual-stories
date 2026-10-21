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
# TODO: install/verify the full video's dependencies here once it exists
npm ci --silent                             # the promo: pinned Playwright (Chromium: `npx playwright install chromium`, see README)

render_promo() {  # the promos, rendered from a web page (src/promo/promo.html): 2D ("promo2d") and 3D ("promo3d", the
                  # same page with ?3d) in 16:9, and the 3D one in 9:16 as a Short; 4K (or 720p draft) with music,
                  # silent, and at final quality a 1080p copy with music. PROMOS="promo2d" (or "promo3d") renders just one.
  local kind f W H flag hd base cues dur music
  cues=$(node src/promo/capture.mjs --print-cues)      # when the music's sections start (the same for 2D and 3D)
  [[ -n $cues ]] || { echo "render.sh: no music cues from capture.mjs" >&2; exit 1; }
  for f in ${PROMO_FORMATS:-16x9 9x16}; do   # PROMO_FORMATS=16x9 skips the Short
  music=""                              # one soundtrack per format, shared by 2D and 3D (same length, same cues)
  for kind in ${PROMOS:-promo2d promo3d}; do
    [[ $f == 9x16 && " ${PROMO_VERTICAL:-promo3d} " != *" $kind "* ]] && continue   # the Short: 3D only (PROMO_VERTICAL="promo2d promo3d" for both)
    if [[ $f == 16x9 ]]; then W=3840; H=2160; flag=""; hd=1920:1080; else W=2160; H=3840; flag="--portrait"; hd=1080:1920; fi
    [[ $QUALITY == draft ]] && { W=$((W / 3)); H=$((H / 3)); }
    [[ $kind == promo3d ]] && flag="$flag --3d"
    base=$OUT/$NAME-$kind-$VER-$f-$RES
    node src/promo/capture.mjs --out "$TMP/${kind}_${VER}_$f.mp4" --width $W --height $H --fps 30 $flag
    ffmpeg -v error -y -i "$TMP/${kind}_${VER}_$f.mp4" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -an \
      -movflags +faststart "$base-silent.mp4"
    if [[ -z $music ]]; then
      dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$base-silent.mp4")
      [[ -n $dur ]] || { echo "render.sh: no duration for $base-silent.mp4" >&2; exit 1; }
      music=$TMP/music_promo_${VER}_$f.wav
      node src/promo/music.mjs --duration "$dur" --cues "$cues" --out "$music"
    fi
    ffmpeg -v error -y -i "$base-silent.mp4" -i "$music" -map 0:v -map 1:a \
      -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$base.mp4"
    if [[ $QUALITY == final ]]; then
      ffmpeg -v error -y -i "$base.mp4" -vf "scale=$hd:flags=lanczos" -c:v libx264 -preset slow -crf 18 \
        -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT/$NAME-$kind-$VER-$f-1080p.mp4"
    fi
  done
  done
}

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

# The full video and the Short aren't built yet: until they are, every render is the promos only. Set FULL=1 once
# render_video, render_music, render_thumbnails and render_publishing are filled in (ONLY=promo then renders just the promos).
FULL=0
render_promo
node src/promo/thumbnails.mjs --out thumbnails   # the promo's YouTube thumbnails (tracked), at every quality: they're quick
if [[ $FULL == 1 && ${ONLY:-} != promo ]]; then
for f in "${FORMATS[@]}"; do
  base=$OUT/$NAME-$VER-$f-$RES
  render_video "$f" "$TMP/video_${VER}_$f.mp4"
  ffmpeg -v error -y -i "$TMP/video_${VER}_$f.mp4" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p \
    -movflags +faststart "$base-silent.mp4"
  render_music "$f" "$TMP/music_${VER}_$f.wav"
  ffmpeg -v error -y -i "$base-silent.mp4" -i "$TMP/music_${VER}_$f.wav" -map 0:v -map 1:a \
    -c:v copy -af apad -c:a aac -b:a 256k -shortest -movflags +faststart "$base.mp4"
  if [[ $QUALITY == final ]]; then   # 1080p copy for social posts; delete this block if the brief doesn't ask for one
    hd=1920:1080; [[ $f == 9x16 ]] && hd=1080:1920
    ffmpeg -v error -y -i "$base.mp4" -vf "scale=$hd:flags=lanczos" -c:v libx264 -preset slow -crf 18 \
      -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT/$NAME-$VER-$f-1080p.mp4"
  fi
done

render_thumbnails
render_publishing
fi

if [[ $QUALITY == final ]]; then   # a final render exports its deliverables (see AGENTS.md): same names, hard links (copy as a fallback)
  mkdir -p workspace/export
  for f in "$OUT"/*; do ln -f "$f" "workspace/export/$(basename "$f")" 2>/dev/null || cp -f "$f" workspace/export/; done
  mkdir -p workspace/export/thumbnails   # the thumbnails too, ready to upload
  for f in thumbnails/*.png; do ln -f "$f" "workspace/export/thumbnails/$(basename "$f")" 2>/dev/null || cp -f "$f" workspace/export/thumbnails/; done
fi

ln -sfn "$VER" workspace/preview/latest
ls -la "$OUT"
