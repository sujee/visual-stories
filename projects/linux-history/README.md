# History of Linux

Traces the history of Linux from birth to present: a 2-minute video and a 30-second Short, with original music.

🎂 Published Oct 5, 2026: 35 years after Linus publicly released Linux 0.02.

▶ Watch it: [video](https://youtu.be/lkOxEeqwMBo) · [Short](https://youtube.com/shorts/fmgBYJmWyXs) · Download the 4K masters: [release](https://github.com/sujee/visual-stories/releases/tag/linux-history-v1)

## Starter prompt

This whole project started from one prompt to Claude Code (Opus 5.5):

> Create visualization tracing Linux history. A 2 min video, with cool music.

That gets you 70–80% of the way there; the rest came from a few rounds of feedback. The details it grew into are in [brief.md](brief.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (it installs Python and everything else)
- ffmpeg: `brew install ffmpeg` (macOS) or `sudo apt-get install -y ffmpeg` (Linux)

## Make the video

```bash
./render.sh draft   # quick preview, about a minute
./render.sh         # full 4K videos (takes a while)
```

Videos land in `workspace/preview/latest/`.

## Customize

Start a coding agent (Claude Code, Codex, …) in this folder and say what you want:

> Add Solaris as a lane next to BSD, and render a draft.

Or edit [brief.md](brief.md) first and ask: *"Update the story to match the brief and render a draft."*
Watch the draft, give notes ("0:45: hold this longer"), and repeat.

Prefer code? Everything is in `src/`: `video.py` (main video), `short.py` (Short), `music.py` (soundtrack).

---

Working with an agent? The house rules are in [AGENTS.md](../../AGENTS.md).
