# Linux History Visualization: Production Metrics

> **Snapshot:** covers the first version only (Oct 3–4, 2026: the original video, the 4K60 render, thumbnails, the Short and the publishing guide). Later iterations (the move into this repository, the 35th-birthday edition, highlighted milestones, v1–v11) are not included.

Session date: 2026-10-03 (all times are local Pacific time, PDT / UTC−7). Model: **Claude Opus 5.5** (`claude-opus-5-5`), used for all 39 API calls.

## Deliverables

| File | Resolution | FPS | Length | Size | Status |
|---|---|---|---|---|---|
| `linux_history_1080p30.mp4` | 1920×1080 | 30 | 2:00 | 15 MB | Done |
| `linux_history_4k60.mp4` | 3840×2160 | 60 | 2:00 | 43 MB | Done |

## Time

### Request 1: the 1080p video (from prompt to finished file)

| Milestone | Time (PDT) | Elapsed |
|---|---|---|
| Prompt received | 15:12:27 | 0:00 |
| Tools checked; Python environment set up | ~15:13:30 | ~1:00 |
| Soundtrack synthesized, levels rebalanced | 15:16:29 | 4:02 |
| Renderer written; test stills reviewed and layout fixed | ~15:18:40 | ~6:15 |
| All 3,600 frames rendered and muxed (29 s on 10 cores) | 15:19:11 | 6:44 |
| Final frames checked; summary delivered | 15:19:27 | **7:00** |

**About 7 minutes in total**, from prompt to a finished, reviewed 2-minute video with an original soundtrack.

### Request 2: the 4K60 version

| Milestone | Time (PDT) | Elapsed |
|---|---|---|
| Prompt received | 22:32:31 | 0:00 |
| Renderer given a resolution-scaling layer; 4K test still checked; full render started | ~22:33:45 | ~1:15 |
| All 7,200 frames rendered and muxed (2,747 s) | 23:19:11 | 46:40 |
| Final frame checked; summary delivered | 23:19:52 | **47:21** |

The 4K60 render is 8× more work than 1080p30 (4× the pixels, 2× the frames). It took ~46 min rather than ~4 min because 10 Python renderers and 10 x264 4K encoders ran at once on 10 cores and competed for CPU. Running fewer chunks in parallel would likely be faster.

## Tokens

These are API usage figures for every call in the session, read from the Claude Code transcript. Usage of the final calls that wrote this report is only partly included.

| Phase | API calls | Input (uncached) | Cache writes (1h) | Cache reads | Output |
|---|---:|---:|---:|---:|---:|
| 1. Make the 1080p video | 16 | 32 | 71,929 | 1,008,939 | 38,070 |
| 2. Token, cost and time questions | 10 | 20 | 120,402 | 1,117,690 | 5,168 |
| 3. 4K60 version and file naming | 11 | 24 | 136,079 | 1,555,874 | 6,918 |
| 4. This report | 2+ | 4 | 506 | 319,671 | 396 |
| **Total** | **39** | **80** | **328,916** | **4,002,174** | **50,552** |

**Total tokens processed: ~4.38 million.** About 91% of these were cache reads: the conversation context is re-read on each step, which is cheap. Only ~51K tokens were generated (output includes thinking), and those included all of the code: 557 lines for the renderer and 283 for the music synthesizer.

## Cost

Claude Opus 5.5 API rates (Anthropic first-party, per million tokens):

| Token type | Rate | Tokens | Cost |
|---|---:|---:|---:|
| Input (uncached) | $4.00 | 80 | $0.00 |
| Cache writes (1-hour TTL, 2× input) | $8.00 | 328,916 | $2.63 |
| Cache reads | $0.20 | 4,002,174 | $0.80 |
| Output (incl. thinking) | $20.00 | 50,552 | $1.01 |
| **Total** | | | **$4.44** |

By phase: 1080p video **$1.54** · token/cost/time questions **$1.29** · 4K version **$1.54** · this report **$0.08** (partial).

Phase 2 cost almost as much as making the video. Looking up current pricing loaded a large API reference document into context, and that was written to the cache.

Without prompt caching, the same work would have cost about **$18.34**: all ~4.33M input tokens at $4 plus output. Caching cut the bill by about 76%.

### Notes

- These are **API-equivalent prices**. With a Claude subscription (Pro/Max/Team), you aren't billed per token; this usage counts against your plan's limits instead.
- Not included: local compute. Rendering, encoding and audio synthesis ran on this Mac (10-core, 24 GB) using free tools: Python, NumPy, SciPy, Pillow and FFmpeg.
- No paid assets or services were used. Every visual and every sound was generated procedurally from code, so there are no stock footage or music licensing costs.

## Production stats

- **Visuals:** a terminal-styled, three-panel layout with neon glow.
  - A `git log --graph`-style family tree of 20 lineages: Unix, BSD, MINIX and GNU, then Linux and 15 distros.
  - A `dmesg`-style log of 49 dated milestones (1969–2026) that types itself out.
  - A live year counter with kernel version, line count and distro count, plus a chart of kernel size growing from 10K to ~41M lines.
- **Timing:** 1969–1991 plays at 1 year/s; 1991–2026 at ~2.3 s/year. The Linux 0.01 release lands exactly on the musical drop.
- **Audio:** original 120 BPM synthwave score in A minor (Am–F–C–G), 60 bars, synthesized from scratch: detuned-saw pads, 16th-note arpeggio, offbeat bass, kick, clap, hats, lead melody, risers and impacts, with sidechain pumping and reverb. Integrated loudness −10.4 LUFS. Visual glow pulses are synced to the kick.
- **Frames rendered:** 3,600 (1080p30) and 7,200 (4K60).
