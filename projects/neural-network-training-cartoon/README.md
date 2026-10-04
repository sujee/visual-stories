# How a Neural Network Learns (cartoon style)

A visual story of how a neural network learns from its mistakes: forward pass, error, backpropagation, and weight updates. Told in a bright cartoon style, with a bouncy soundtrack.

The intent (what it teaches, for whom, and what must come across) is in [brief.md](brief.md). The approved implementation is in `src/`.

Working with a coding agent? The house rules are in [AGENTS.md](../../AGENTS.md) at the repository root: read it first.

▶ Watch the finished story: [video](https://youtu.be/11BqOZ9HJeY) · Download the 4K masters: [release](https://github.com/sujee/visual-stories/releases/tag/neural-network-training-cartoon-v1)

Same story and animation as [neural-network-training](../neural-network-training/), in a different visual and musical style. Compare the two `brief.md` files to see what changed.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/). It installs Python 3.11 and the pinned packages itself.
- System packages for Manim and audio. The fonts (Luckiest Guy, Apache-2.0; Sniglet, OFL) are bundled in `assets/fonts/` with their licenses.

```bash
sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config ffmpeg sox   # Debian/Ubuntu (tested)
brew install cairo pango pkg-config ffmpeg sox   # macOS (tested)
```

The display fonts (Luckiest Guy, Comic Neue) are bundled in `assets/fonts/` with their licence files, so no font has to be installed on the machine.

## Run it yourself

```bash
./render.sh            # → workspace/preview/<timestamp>/  (4K landscape ~1:55 + Short ~0:59, with and without music)
./render.sh draft      # quick 720p draft, both formats → workspace/preview/<timestamp>/
./render.sh draft v12  # same, named version            → workspace/preview/v12/
./render.sh final v12  # everything, final quality      → workspace/preview/v12/
```

## Customize

- **Through the brief:** edit `brief.md` (e.g. a color preference under **Style**), then ask your agent to *update the story and render a draft*. Give notes on each draft until you approve one, then render it at final quality: `./render.sh final <version>`.
- **Directly:** edit `src/scene.py` (animation; colors and fonts are at the top) or `src/music.py` (the cartoon soundtrack), then run `./render.sh draft <next version>`.

## Verification

Before committing, ask your agent for the *fresh-clone test* (or *repro test*): it renders from a copy of only the files Git tracks and checks that the output matches the approved version. It takes one full final render.
