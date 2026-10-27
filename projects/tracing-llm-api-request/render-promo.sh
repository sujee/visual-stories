#!/usr/bin/env bash
# The promos (brief-promo.md): 2D ("promo2d") and 3D ("promo3d") in 16:9, and the 3D one in 9:16 as a Short,
# rendered from a web page (src/promo/promo.html). 4K (or 720p draft) with music, silent, and at final quality a
# 1080p copy with music. Output: workspace/promo/preview/<version>/, and workspace/promo/export/ after a final render. Also writes the promo's YouTube thumbnails to thumbnails/ (tracked).
#
#   ./render-promo.sh [quality] [version]            (see README.md)
#   PROMOS=promo3d ./render-promo.sh draft v2        just one promo (or promo2d)
#   PROMO_FORMATS=16x9 ./render-promo.sh …           skip the vertical Short (PROMO_VERTICAL="promo2d promo3d" makes both vertical)
set -euo pipefail
cd "$(dirname "$0")"
WS=workspace/promo                         # the promos have their own versions, apart from the full video's
source src/shared/render-common.sh "$@"

cues=$(node src/shared/capture.mjs --print-cues)      # when the music's sections start (the same for 2D and 3D)
[[ -n $cues ]] || { echo "render-promo.sh: no music cues from capture.mjs" >&2; exit 1; }
for f in ${PROMO_FORMATS:-16x9 9x16}; do
  music=""                              # one soundtrack per format, shared by 2D and 3D (same length, same cues)
  for kind in ${PROMOS:-promo2d promo3d}; do
    [[ $f == 9x16 && " ${PROMO_VERTICAL:-promo3d} " != *" $kind "* ]] && continue   # the Short: 3D only
    if [[ $f == 16x9 ]]; then W=3840; H=2160; flag=""; hd=1920:1080; else W=2160; H=3840; flag="--portrait"; hd=1080:1920; fi
    [[ $QUALITY == draft ]] && { W=$((W / 3)); H=$((H / 3)); }
    [[ $kind == promo3d ]] && flag="$flag --3d"
    base=$OUT/$NAME-$kind-$VER-$f-$RES
    node src/shared/capture.mjs --out "$TMP/${kind}_${VER}_$f.mp4" --width $W --height $H --fps 30 $flag
    ffmpeg -v error -y -i "$TMP/${kind}_${VER}_$f.mp4" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -an \
      -movflags +faststart "$base-silent.mp4"
    if [[ -z $music ]]; then
      dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$base-silent.mp4")
      [[ -n $dur ]] || { echo "render-promo.sh: no duration for $base-silent.mp4" >&2; exit 1; }
      music=$TMP/music_promo_${VER}_$f.wav
      node src/promo/music.mjs --duration "$dur" --cues "$cues" --out "$music"
    fi
    ffmpeg -v error -y -i "$base-silent.mp4" -i "$music" -map 0:v -map 1:a \
      -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$base.mp4"
    if [[ $QUALITY == final ]]; then      # 1080p copy for social posts
      ffmpeg -v error -y -i "$base.mp4" -vf "scale=$hd:flags=lanczos" -c:v libx264 -preset slow -crf 18 \
        -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT/$NAME-$kind-$VER-$f-1080p.mp4"
    fi
  done
done

node src/promo/thumbnails.mjs --out thumbnails   # the promo's YouTube thumbnails (tracked), at every quality: they're quick

finish "$OUT"/$NAME-promo*-$VER-*.mp4
if [[ $QUALITY == final ]]; then
  mkdir -p "$WS/export/thumbnails"
  for f in thumbnails/*promo*.png; do ln -f "$f" "$WS/export/thumbnails/$(basename "$f")" 2>/dev/null || cp -f "$f" "$WS/export/thumbnails/"; done
fi
ls -la "$OUT"
