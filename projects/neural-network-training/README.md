# How a Neural Network Learns

A visual story of how a neural network learns from its mistakes: forward pass, error, backpropagation, and weight updates.

The intent (what it teaches, for whom, and what must come across) is in [brief.md](brief.md). The approved implementation is in `src/`.

Working with a coding agent? The house rules are in [AGENTS.md](../../AGENTS.md) at the repository root: read it first.

▶ Watch the finished story: [video](https://youtu.be/BJC3FuMHRvs) · [Short](https://youtube.com/shorts/0fBcojHo-SI) · Download the 4K masters: [release](https://github.com/sujee/visual-stories/releases/tag/neural-network-training-v1)

Also in a cartoon style, with the same story and animation: [neural-network-training-cartoon](../neural-network-training-cartoon/).

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/). It installs Python 3.11 and the pinned packages itself.
- System packages for Manim, audio and the font:

```bash
sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config ffmpeg sox fonts-inter   # Debian/Ubuntu (tested)
brew install cairo pango pkg-config ffmpeg sox && brew install --cask font-inter          # macOS (tested)
```

## Run it yourself

```bash
./render.sh            # → workspace/preview/<timestamp>/  (4K landscape ~1:55 + Short ~0:59, with and without music)
./render.sh draft      # quick 720p draft, both formats → workspace/preview/<timestamp>/
./render.sh draft v7   # same, named version            → workspace/preview/v7/
./render.sh final v7   # everything, final quality      → workspace/preview/v7/
```

## Customize

**Option 1: with a coding agent** (Claude Code, Codex, OpenCode, …), started in this directory:

1. **Edit `brief.md`.** Say what you want, not how. E.g. change the guesses under **Story**, or add a color preference under **Style**.
2. **Ask for a draft:** *"Update the story to match the brief and render a draft."* The agent edits `src/` and renders to `workspace/preview/v1/` (then `v2`, `v3`, …).
3. **Watch it and give notes**, ideally with timestamps: *"0:45: the caption overlaps the chart."* The agent applies them and renders the next draft. Repeat until you're happy.
4. **Approve and render final:** *"v3 is approved, render it at final quality"* (or `./render.sh final v3` yourself). This takes a while: 4K, both formats.

**Option 2: edit the code directly:** `src/scene.py` (animation; colors and the guesses are at the top) or `src/music.py`, then run `./render.sh draft <next version>`.

## Verification

Before committing, ask your agent for the *fresh-clone test* (or *repro test*): it renders from a copy of only the files Git tracks and checks that the output matches the approved version. It takes one full final render.
