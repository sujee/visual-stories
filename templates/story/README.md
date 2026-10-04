# <Title>

<One sentence: what the story teaches.>

The intent (what it teaches, for whom, and what must come across) is in [brief.md](brief.md). The approved implementation is in `src/`.

Working with a coding agent? The house rules are in [AGENTS.md](../../AGENTS.md) at the repository root: read it first.

▶ Watch the finished story: <link, or *(coming soon)*>

## Prerequisites

<Only what the lockfile can't install: the package manager, system packages (at least ffmpeg, which render.sh uses), fonts. Exact commands, with the tested OS noted.>

## Run it yourself

```bash
./render.sh            # → workspace/preview/<timestamp>/  (<what the final deliverables are>; and rewrites thumbnails/ and youtube-publishing.md, if there are any)
./render.sh draft      # <what a draft produces>  → workspace/preview/<timestamp>/
./render.sh draft v2   # same, named version      → workspace/preview/v2/
./render.sh final v2   # everything, final quality → workspace/preview/v2/
```

## Customize

**Option 1: with a coding agent** (Claude Code, Codex, OpenCode, …), started in this directory:

1. **Edit `brief.md`.** Say what you want, not how. E.g. <an example change and the brief section it goes under>.
2. **Ask for a draft:** *"Update the story to match the brief and render a draft."* The agent edits `src/` and renders to `workspace/preview/v1/` (then `v2`, `v3`, …).
3. **Watch it and give notes**, ideally with timestamps: *"0:45: the caption overlaps the chart."* The agent applies them and renders the next draft. Repeat until you're happy.
4. **Approve and render final:** *"v3 is approved, render it at final quality"* (or `./render.sh final v3` yourself). This takes a while: <what a final render produces, e.g. 4K, both formats>.

**Option 2: edit the code directly:** <the main source files, and where the most common changes live>, then run `./render.sh draft <next version>`.

## Verification

Before committing, ask your agent for the *fresh-clone test* (or *repro test*): it renders from a copy of only the files Git tracks and checks that the output matches the approved version. It takes one full final render.
