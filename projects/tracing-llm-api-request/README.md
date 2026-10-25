# Tracing an LLM API Request

Follow one LLM API request from your code to the GPU and back, and see where the time goes.

The intent (what it teaches, for whom, and what must come across) is in [brief.md](brief.md) (full video) and [brief-teaser.md](brief-teaser.md) (the approved teaser/promos). The approved implementation is in `src/`.

Working with a coding agent? The house rules are in [AGENTS.md](../../AGENTS.md) at the repository root: read it first.

▶ Watch the finished story: *(coming soon)*

**Status:** the promo (2D and 3D, 16:9, plus a 9:16 Short of the 3D one) is approved. The full video and the Short aren't built yet, so `./render.sh` renders the promos only.

## Prerequisites

Tested on macOS 26 (Apple silicon).

- **Node.js 20+** and npm (`brew install node`)
- **ffmpeg** (`brew install ffmpeg`)
- **Chromium for Playwright**, once: `npx playwright install chromium` (after `npm ci`). The promo is a web page captured frame by frame in headless Chromium; the 3D version renders WebGL in software (SwiftShader) so frames are identical on every machine.

`render.sh` runs `npm ci` itself (Playwright and three.js, pinned in `package-lock.json`). Fonts (JetBrains Mono, OFL) are in `assets/fonts/`.

## Run it yourself

```bash
./render.sh            # final: both promos in 16:9 and the 3D one in 9:16, each 4K with music + 4K silent + 1080p with music
                       #   -> workspace/preview/<timestamp>/, and hard-linked into workspace/export/
./render.sh draft      # 720p drafts of the same (with music and silent)         -> workspace/preview/<timestamp>/
./render.sh draft v2   # same, named version                               -> workspace/preview/v2/
./render.sh final v2   # final quality, named version                      -> workspace/preview/v2/
PROMOS=promo3d ./render.sh draft v2       # just the 3D promo (or PROMOS=promo2d for just the 2D one)
PROMO_FORMATS=16x9 ./render.sh …          # skip the vertical Short (PROMO_VERTICAL="promo2d promo3d" makes both vertical)
```

Files are named `tracing-llm-api-request-promo2d-<version>-16x9-4k.mp4` (2D) and `…-promo3d-…` (3D), `…-9x16-…` for the Short, plus `-silent` and `-1080p` variants. Every render also writes the YouTube thumbnails to `thumbnails/` (tracked). A final 3D render takes a while (software WebGL at 4K).

To scrub through the promo in a browser, open `src/promo/promo.html` (add `?3d` for the 3D version, `?portrait` for the vertical layout).

## Customize

**Option 1: with a coding agent** (Claude Code, Codex, OpenCode, …), started in this directory:

1. **Edit `brief.md`** (or `brief-teaser.md` for the promos). Say what you want, not how. E.g. under *Deliverables*: "Promo music: a calm solo piano."
2. **Ask for a draft:** *"Update the promo to match the brief and render a draft."* The agent edits `src/` and renders to `workspace/preview/v1/` (then `v2`, `v3`, …).
3. **Watch it and give notes**, ideally with timestamps: *"0:13: the router shot feels rushed."* The agent applies them and renders the next draft. Repeat until you're happy.
4. **Approve and render final:** *"v3 is approved, render it at final quality"* (or `./render.sh final v3` yourself).

**Option 2: edit the code directly**, then run `./render.sh draft <next version>`:

- `src/promo/promo.html`: the promo as a pure function of time (`seek(t)`): content (prompt, tokens, reply, example timings), the 2D scenes, the stopwatch, stage titles and timeline, and the pacing (`PACE`).
- `src/promo/world3d.js`: the 3D journey (three.js) used by `promo.html?3d`: one place per stage along the camera's path, and the chase camera (`camAt`).
- `src/promo/music.mjs`: the house soundtrack; its sections follow the promo's cuts (`capture.mjs --print-cues`).
- `src/promo/capture.mjs`: renders the page to video with Playwright.
- `src/promo/thumbnails.mjs`: the YouTube thumbnails: headlines over a clean 3D frame (`promo.html?3d&clean`, designs in `DESIGNS`), and `path`, the trip from the client to the GPU with each stage's time.

## Verification

Before committing, ask your agent for the *fresh-clone test* (or *repro test*): it renders from a copy of only the files Git tracks and checks that the output matches the approved version. It takes one full final render.
