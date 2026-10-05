# Visual Stories

Open-source, reproducible visual stories for AI, software, and technical concepts.

**Watch them. Reproduce them. Remix them.**

### [▶ YouTube Playlist](https://www.youtube.com/playlist?list=PLUs9fKO_C_uw)

### [Browse the stories](#stories) · [Reproduce one](#explore-and-reproduce) · [Create your own](#create-a-new-story)

The code and templates are licensed under [Apache-2.0](LICENSE), and the original videos and soundtracks under [CC BY 4.0](LICENSE-CONTENT). If you build something cool with them, a link back is always appreciated (not required). Most of the projects here are open source, unless noted otherwise.

## Working with Agents

[AGENTS.md](AGENTS.md)

## Explore and reproduce

Each visual story is self-contained.

**On your own:**

```bash
git clone https://github.com/sujee/visual-stories.git
cd visual-stories/projects/neural-network-training
# install the prerequisites listed in its README.md, then:
./render.sh          # all deliverables, final quality (4K, takes a while)
./render.sh draft    # quick draft preview
```

**With a coding agent:** start it in the story's folder (or the repository root) and ask:

> Read AGENTS.md and README.md. Install the prerequisites and render the final video.

## Create a new story

Start a coding agent in the repository root (the new story's folder doesn't exist yet) and ask, for example:

> Create a new story about prefill vs decode.

The agent starts by writing a `brief.md` for you to review, then renders drafts (`v1`, `v2`, …) for your feedback. Once you approve a version, ask it to *prepare the Repro Bundle* before committing.

Or start by hand: copy [`templates/story/`](templates/story/) to `projects/<name>/` and fill in the placeholders.

## Stories

All the videos are in one [YouTube playlist](https://www.youtube.com/playlist?list=PLUs9fKO_C_uw).

| Published | Story | What it's about | Watch |
|---|---|---|---|
| 2026-10-05 | [linux-history](projects/linux-history/) | Linux at 35. from "just a hobby" post to running the cloud, phones and Mars | [Video](https://youtu.be/lkOxEeqwMBo) · [Short](https://youtube.com/shorts/fmgBYJmWyXs) · [release](https://github.com/sujee/visual-stories/releases/tag/linux-history-v1) |
| 2026-10-03 | [jev-vs-llm](projects/jev-vs-llm/) | Jev, TypeSafe AI's "System One" model, vs. a chat LLM | [Video](https://youtu.be/RQ6f6z-dPWA) · [Short](https://youtube.com/shorts/Iv2K_rx5Jso) · [release](https://github.com/sujee/visual-stories/releases/tag/jev-vs-llm-v1) |
| 2026-09-27 | [neural-network-training](projects/neural-network-training/) | How a neural network learns  | [Video](https://youtu.be/BJC3FuMHRvs) · [Short](https://youtube.com/shorts/0fBcojHo-SI) · [release](https://github.com/sujee/visual-stories/releases/tag/neural-network-training-v1) |
| 2026-09-27 | [neural-network-training-cartoon](projects/neural-network-training-cartoon/) | The same story in a bright cartoon style | [Video](https://youtu.be/11BqOZ9HJeY) · [Short](https://youtube.com/shorts/wK1GNcRc8jY) · [release](https://github.com/sujee/visual-stories/releases/tag/neural-network-training-cartoon-v1) |
