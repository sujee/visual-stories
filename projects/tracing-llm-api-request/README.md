# Tracing an LLM API Request

Follow one LLM API request from your code to the GPU and back, and see where the time goes.

The intent (what it teaches, for whom, and what must come across) is in the briefs below. The implementation is in `src/`.

Working with a coding agent? The house rules are in [AGENTS.md](../../AGENTS.md) at the repository root: read it first.

▶ Watch the finished story: *(coming soon)*

The story has two parts, each with its own brief, code and render script:

| | Brief | Code | Render | Status |
|---|---|---|---|---|
| **Full explainer** (16:9, 4 to 5 min) | [brief-full.md](brief-full.md) | `src/full/` | `./render-full.sh` | v15 (5:18); the Short is the promo's; thumbnails in `thumbnails/…-full-…`; publishing notes: [youtube-publishing-full.md](youtube-publishing-full.md), [social-publishing-full.md](social-publishing-full.md) |
| **Promos** (2D and 3D in 16:9, 3D also as a 9:16 Short) | [brief-promo.md](brief-promo.md) | `src/promo/` | `./render-promo.sh` | approved |

They share the page capture and the 3D world in `src/shared/`. Each has its own render script; there is no combined one.

## Prerequisites

Tested on macOS 26 (Apple silicon).

- **Node.js 20+** and npm (`brew install node`)
- **ffmpeg** (`brew install ffmpeg`)
- **Chromium for Playwright**, once: `npx playwright install chromium` (after `npm ci`). The videos are web pages captured frame by frame in headless Chromium; the 3D version renders WebGL in software (SwiftShader) so frames are identical on every machine.

The render scripts run `npm ci` themselves (Playwright and three.js, pinned in `package-lock.json`). Fonts (JetBrains Mono, OFL) are in `assets/fonts/`.

## Run it yourself

```bash
./render-full.sh              # final: the full video, 4K with music + 4K silent + 1080p with music
                              #   -> workspace/full/preview/<timestamp>/, and hard-linked into workspace/full/export/
./render-full.sh draft        # 720p draft (with music and silent)                -> workspace/full/preview/<timestamp>/
./render-full.sh draft v2     # same, named version                               -> workspace/full/preview/v2/
./render-full.sh final v2     # final quality, named version                      -> workspace/full/preview/v2/
./render-promo.sh [draft|final] [version]   # the same for the promos (workspace/promo/preview/, workspace/promo/export/): both in 16:9, the 3D one also in 9:16
PROMOS=promo3d ./render-promo.sh draft v2      # just the 3D promo (or PROMOS=promo2d for just the 2D one)
PROMO_FORMATS=16x9 ./render-promo.sh …      # skip the vertical Short (PROMO_VERTICAL="promo2d promo3d" makes both vertical)
```

Files are named `tracing-llm-api-request-<version>-16x9-4k.mp4` for the full video, `tracing-llm-api-request-promo2d-<version>-16x9-4k.mp4` (2D) and `…-promo3d-…` (3D), `…-9x16-…` for the Short, plus `-silent` and `-1080p` variants. Every render also writes the YouTube thumbnails to `thumbnails/` (tracked); a final render also copies them into `workspace/full/export/thumbnails/` (or `workspace/promo/export/thumbnails/`). A final 3D render takes a while (software WebGL at 4K).

## Customize

**Option 1: with a coding agent** (Claude Code, Codex, OpenCode, …), started in this directory:

1. **Edit `brief-full.md`** (the full video) or `brief-promo.md` (the promos). Say what you want, not how. E.g. under *Deliverables*: "Promo music: a calm solo piano."
2. **Ask for a draft:** *"Update the promo to match the brief and render a draft."* The agent edits `src/` and renders to `workspace/promo/preview/v1/` for the promos or `workspace/full/preview/v1/` for the full video (then `v2`, `v3`, …). The two have separate version numbers.
3. **Watch it and give notes**, ideally with timestamps: *"0:13: the router shot feels rushed."* The agent applies them and renders the next draft. Repeat until you're happy.
4. **Approve and render final:** *"v3 is approved, render it at final quality"* (or `./render-full.sh final v3` / `./render-promo.sh final v3` yourself).

**Option 2: edit the code directly**, then run `./render-full.sh draft <next version>` (or `./render-promo.sh`):

*Full explainer* (`./render-full.sh`):

- `src/full/full2d.html`: the full video as a pure function of time (`seek(t)`): one 2D map of the whole route with a zooming camera, the transition and title cards, the explainer scenes (prompt caching, batching, KV cache, disaggregated prefill, speculative decoding, streaming, recap), the end card and the captions. `src/full/full.html` is an earlier 3D experiment of the same video (`PAGE=src/full/full.html ./render-full.sh`).
- `src/full/thumbnails.mjs`: the full video's YouTube thumbnails (16:9; designs `question`, `optimize`, `time`) over a frame of the video.
- `src/full/youtube.mjs`: writes the chapters into `youtube-publishing-full.md` from the page's `window.CHAPTERS` (a final render does it; checks YouTube's rules).
- `src/full/music.mjs`: its soundtrack: an upbeat, mellow kalimba arpeggio over a warm pad and bass (option `u2`, the default); the other `--option` values are variations to compare or remix. It lifts under the optimization slides and goes quieter in the busy scenes (the page's `window.MUSIC_CUES`).

*Promos* (`./render-promo.sh`):

- `src/promo/promo.html`: the promo as a pure function of time (`seek(t)`): content (prompt, tokens, reply, example timings), the 2D scenes, the stopwatch, stage titles and timeline, and the pacing (`PACE`). Open it in a browser to scrub (add `?3d` for the 3D version, `?portrait` for the vertical layout).
- `src/promo/music.mjs`: the house soundtrack; its sections follow the promo's cuts (`capture.mjs --print-cues`).
- `src/promo/thumbnails.mjs`: the YouTube thumbnails: headlines over a clean 3D frame (`promo.html?3d&clean`, designs in `DESIGNS`), and `path`, the trip from the client to the GPU with each stage's time.

*Shared* (`src/shared/`):

- `world3d.js`: the 3D journey (three.js) used by both pages: one place per stage along the camera's path, and the chase camera (`camAt`).
- `capture.mjs`: renders a page to video with Playwright (`--page` picks the page; the promo by default). `--segments 10 --cache <dir>` renders in cached segments (cut at the page's `window.SCENE_STARTS`; `--plan` lists what would re-render).
- `clip.mjs`: a short clip or one frame of a page, without a render: `node src/shared/clip.mjs --page src/full/full2d.html --range 45-50 --out workspace/tmp/clip.mp4`, or `--at 78.5` for a still.
- `render-common.sh`: the arguments, output folder, `npm ci` and export that both render scripts share.

## Verification

Before committing, ask your agent for the *fresh-clone test* (or *repro test*): it renders from a copy of only the files Git tracks and checks that the output matches the approved version. It takes one full final render.
