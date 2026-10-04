# Jev: A System One Model

A visual story of Jev, TypeSafe AI's "System One" model: instead of writing text, it returns typed decisions with calibrated probabilities that code can act on directly.

The intent (what it teaches, for whom, and what must come across) is in [brief.md](brief.md). The approved implementation is in `src/`.

Working with a coding agent? The house rules are in [AGENTS.md](../../AGENTS.md) at the repository root: read it first.

▶ Watch the finished story: [video](https://youtu.be/RQ6f6z-dPWA) · [Short](https://youtube.com/shorts/Iv2K_rx5Jso) · Download the 4K masters: [release](https://github.com/sujee/visual-stories/releases/tag/jev-vs-llm-v1)

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/). It installs Python 3.11 and the pinned packages itself.
- System packages for Manim, audio and the font:

```bash
sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config ffmpeg sox fonts-inter   # Debian/Ubuntu
brew install cairo pango pkg-config ffmpeg sox && brew install --cask font-inter          # macOS (tested)
```

The monospace font (JetBrains Mono, OFL) is bundled in `assets/fonts/`.

## Render it

From the existing source. This reproduces the approved video exactly.

**Yourself:**

```bash
./render.sh            # → workspace/preview/<timestamp>/  (4K landscape ~2:05 + Short ~0:36, with and without music,
                       #    1080p copies for X/LinkedIn, and rewrites thumbnails/ (3 designs per format) and youtube-publishing.md)
./render.sh draft      # quick 720p draft, both formats → workspace/preview/<timestamp>/
./render.sh draft v5   # same, named version            → workspace/preview/v5/
./render.sh final v5   # everything, final quality      → workspace/preview/v5/
```

**With a coding agent** (Claude Code, Codex, OpenCode, …), started in this directory:

> Read ../../AGENTS.md and README.md. Install the prerequisites and render the final video.

## Re-create it from the brief

This makes a fresh take from [brief.md](brief.md) alone: same goals, new visuals and code. Start the agent in this directory:

> Read ../../AGENTS.md and brief.md. Delete src/ and re-create this story from brief.md only, updating README.md to match. Render draft v1 for me to review.

Then iterate on drafts as below. Git still has the approved version: `git restore . && git clean -fd .` in this directory brings it back (and discards every uncommitted change here, including edits to the brief).

## Change it

**With a coding agent**, started in this directory:

1. **Edit `brief.md`.** Say what you want, not how. E.g. add a point under **Must communicate**, or change a length under **Deliverables**.
2. **Ask for a draft:**
   > Update the story to match the brief and render a draft.

   The agent edits `src/` and renders to `workspace/preview/v1/` (then `v2`, `v3`, …).
3. **Watch it and give notes**, ideally with timestamps:
   > v3 notes: 0:45: the caption overlaps the chart. 1:10: hold this scene longer.

   The agent applies them and renders the next draft. Repeat until you're happy.
4. **Approve and render final:**
   > v3 is approved. Render it at final quality.

   Or run `./render.sh final v3` yourself. This takes a while: 4K, both formats.

**Or edit the code directly:** `src/scene.py` (one method per beat, `b_title` … `b_end`; colors and the example ticket, options and probabilities are at the top; the section titles are in `SECTIONS`), `src/music.py`, or `src/youtube.py` (the YouTube publishing guide and descriptions; chapter times come from the render); thumbnails are `JevThumbnail` at the end of `src/scene.py`, then run `./render.sh draft <next version>`.

## Verify before committing

Ask your agent:

> Run the fresh-clone test for this story.

It renders from a copy of only the files Git tracks and checks that the output matches the approved version. It takes one full final render.
