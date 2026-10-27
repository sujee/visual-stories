# Publishing on YouTube: What Happens When We Call an LLM API?

Written by hand (or by your agent): edit it freely. The one exception is the chapter lines between `Chapters:` and `---`
in the full video's description: `./render-full.sh final` rewrites them from the render's timeline (`window.CHAPTERS` in
`src/full/full2d.html`, written by `src/full/youtube.mjs`). To refresh them without a render:
`node src/shared/capture.mjs --page src/full/full2d.html --print-chapters | node src/full/youtube.mjs`.

Checked against the v15 final render (5:18, end card 5:11–5:18). After the final render, check the hand-written timings (marked below).

Publish the full video first. There is no separate Short for the full video: the promo Short already on YouTube
(about 43 s) does that job, and it links to this video.

## Full video (5:18)

### Upload steps

1. In YouTube Studio, choose **Create → Upload videos** and pick
   `workspace/export/tracing-llm-api-request-<version>-16x9-4k.mp4` (the version with music).
2. Paste the **Title** and **Description** below. The chapters appear automatically.
3. **Thumbnail:** pick one of `thumbnails/tracing-llm-api-request-thumbnail-full-{question,optimize,time}-16x9.png`
   ("What happens when we call an LLM API?", "5 tricks that make LLMs fast", "Where does the time go?") and upload it here.
4. **Audience:** No, it's not made for kids.
5. **Show more:** License **Creative Commons – Attribution**; Category **Science & Technology**;
   Altered or synthetic content **No** (an animated explainer; nothing realistic or deceptive); **Tags:** see below.
6. **End screen** (Editor → End screen): the end card runs from **5:11 to 5:18** (check after the final render). Add a
   Subscribe element and a "Best for viewer" video, kept clear of the end card's text.
7. **Visibility:** Public (or Unlisted to check it first). Publish.
8. **Pin a comment:** post the **Pinned comment** below and pin it.
9. **Copy the video's URL.** The promo Short and the posts need it (see "After publishing").
10. In the description, replace `<insert link to the promo Short>` with the Short's URL (it already exists).

### Title

```text
What Happens When We Call an LLM API? One request, traced to the GPU
```

### Description

```text
Follow one LLM API request from your code to the GPU and back, and see where the time goes: the gateway, the tokenizer, a cache-aware router, the queue, prefill, decode, and the tokens streaming back to you.

Along the way, five ideas that make it fast: prompt caching in blocks, continuous batching, the KV cache, disaggregated prefill and speculative decoding.

Timings shown are illustrative.

Short version (0:43): <insert link to the promo Short>

Chapters:
0:00 What happens when we call an LLM API
0:11 Gateway and tokenizer
0:30 Routing
0:45 Efficient prompt caching
1:24 The replica's queue
1:35 Continuous batching
1:56 Prefill
2:07 The KV cache
2:44 Decode
2:58 Disaggregated prefill
3:40 Speculative decoding
4:22 Streaming back
4:52 Where did the time go?
---

Based on my talk "What Happens When You Call a Model API". Slides: <insert link to the slides, or delete this line>
Created by sujee.dev. Music: original, generated in code.
Source, brief and how to reproduce or remix it: https://github.com/sujee/visual-stories/tree/main/projects/tracing-llm-api-request
Video and music: CC BY 4.0. Code: Apache-2.0.

#LLM #AI #GPU #AIEngineering #MotionGraphics
```

### Pinned comment

```text
Which of these have you run into in production: prompt caching, continuous batching, the KV cache, disaggregated prefill or speculative decoding? And what surprised you?
```

### Tags

```text
LLM, LLM inference, how LLMs work, LLM API, prompt caching, KV cache, continuous batching, prefill, decode, speculative decoding, disaggregated prefill, time to first token, tokens, GPU, AI engineering
```

## The promo Short (already on YouTube)

There is no new upload. In YouTube Studio, open the promo Short and:

1. **Related video:** set it to this video, so viewers can tap through from the Short (links typed into a Short's
   description aren't clickable).
2. **Title** and **Description:** use the ones below. Fill in `<insert link to the full video>` with this video's URL.
3. Nothing else changes: it already has its own thumbnail and tags.

Each description names the other video, so each leads to the other. The same text is in `social-publishing-promo.md`
(section "YouTube Short"); keep the two in step.

### Short title

```text
What happens when you call an LLM API? #shorts
```

### Short description

```text
One LLM request, from your code to the GPU and back, in 43 seconds: gateway, tokenizer, cache-aware router, queue, prefill, decode and the tokens streaming back to you.

Watch the full 5-minute explainer, with chapters: <insert link to the full video>

From my Hacktoberfest 2026 talk "What Happens When You Call a Model API". Event page: https://dev.to/events/hacktoberfest-sujee-model-api/october-22-2026

Timings are illustrative. Created by sujee.dev. Music: original, generated in code. Video and music: CC BY 4.0.

#LLM #AI #GPU #Shorts
```

## After publishing

### Link them both ways

- On this video, make sure the description's "Short version" line has the Short's URL.
- On the Short, check that **Related video** points here and the description has this video's URL.

### Back in the repo

- `README.md`: add the video and Short links (the README still says the full video is in progress).
- Root `README.md`: add or update the row in the Stories table.
- A GitHub release for this story with the 4K masters (see "GitHub Release" in `AGENTS.md`), linked from both READMEs.
- Social posts: see `social-publishing-full.md`.
