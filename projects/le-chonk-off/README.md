# Le Chonk-Off

Five open models of 1T+ parameters as cartoon cats: size is total parameters, perch height is the Artificial Analysis Intelligence Index, the red smile is active parameters per token.

The intent (what it shows, for whom, and what must come across) is in [brief.md](brief.md). The approved implementation is in `src/`.

Working with a coding agent? The house rules are in [AGENTS.md](../../AGENTS.md) at the repository root: read it first.

▶ Watch the finished story: [video](https://youtu.be/Ez7uIjdLnRQ) · [Short](https://youtube.com/shorts/-ioImu61b1s)

Publishing: see [youtube-publishing.md](youtube-publishing.md).

The soundtrack is a very quiet, mellow piano, generated in code (`src/music.mjs`). This is also the one story here built with Node instead of Python: the animation is an HTML/SVG page, captured frame by frame.

## Prerequisites

- [Node.js](https://nodejs.org/) 20+ (tested: 26) and `ffmpeg`. `render.sh` runs `npm ci`; the browser used for rendering is Playwright's Chromium, which you install once.
- The fonts (Luckiest Guy, Apache-2.0; Comic Neue, OFL) are bundled in `assets/fonts/` with their licenses.

```bash
brew install ffmpeg node           # macOS (tested)
npm ci && npx playwright install chromium
```

## Run it yourself

```bash
./render.sh            # → workspace/preview/<timestamp>/  (landscape 3840×2160 and vertical 2160×3840, each ≈ 15.6 s, with the piano and silent, plus 1080p copies and a clean still PNG of the final scene for each format; every render also rewrites `thumbnails/`)
./render.sh draft      # quick 720p drafts (1280×720 and 720×1280) → workspace/preview/<timestamp>/
./render.sh draft v2   # same, named version               → workspace/preview/v2/
./render.sh final v2   # everything, final quality         → workspace/preview/v2/
```

To watch the animation live, open `src/story.html` in a browser (play, pause, scrub and mute controls at the bottom). Add `?portrait` to the address to preview the vertical 9:16 layout (`…/story.html?portrait`). For sound, generate the piano once (and again after changing the story's length): `npm run music`. It writes `workspace/tmp/music_16x9.wav`, which the page plays in step with the animation (any render also refreshes it). Without it the page plays silently and says so.

## Customize

**Option 1: with a coding agent** (Claude Code, Codex, OpenCode, …), started in this directory:

1. **Edit `brief.md`.** Say what you want, not how. E.g. a different set of models, or a vertical Short under **Deliverables**.
2. **Ask for a draft:** *"Update the story to match the brief and render a draft."* The agent edits `src/` and renders to `workspace/preview/v1/` (then `v2`, `v3`, …).
3. **Watch it and give notes**, ideally with timestamps: *"0:12: the label overlaps the perch."* The agent applies them and renders the next draft. Repeat until you're happy.
4. **Approve and render final:** *"v3 is approved, render it at final quality"* (or `./render.sh final v3` yourself). This takes a while: 4K landscape and vertical, each with the piano and silent, plus 1080p copies.

**Option 2: edit the code directly.** The data is the `CSV` list near the top of `src/story.html`, copied from `models.csv` (edit both: the CSV is the readable reference and holds only data). How each model looks (short name, cat colors) is the `STYLE` list right below it. Animation timing is the constants at the top of the script (`LAND`, `FISH0`, `FIN`, `CREDIT0`, `T_END`); colors and fonts are at the top of the file. The piano is `src/music.mjs` (chords, tempo, level at the top); it only needs the story's length. Then run `./render.sh draft <next version>`.

## How it renders

`src/story.html` is a pure function of time, so `src/capture.mjs` steps it frame by frame in headless Chromium (several workers in parallel) and pipes the frames to ffmpeg. `src/music.mjs` synthesizes the piano and normalizes it with ffmpeg. Nothing is fetched at render time.

## Verification

Before committing, ask your agent for the *fresh-clone test* (or *repro test*): it renders from a copy of only the files Git tracks and checks that the output matches the approved version. It takes one full final render.
