# Social media: What Happens When We Call an LLM API? (full video)

Copy for posting the full video (5:18 at v13; re-check the length after the final render). Edit it freely. The promo's copy is in
`social-publishing-promo.md`. Replace `<insert link to the full video>` with the YouTube URL once it is up (see `youtube-publishing-full.md`).

The talk this video follows may already have happened, so the copy says "I made a video" and doesn't say "tomorrow". If you post it
around a talk, add the date and event link yourself.

Files (in `workspace/export/` after `./render-full.sh final`, or `workspace/full/preview/<version>/`):

| Where | File |
|---|---|
| YouTube | `tracing-llm-api-request-<version>-16x9-4k.mp4` (the one with music) |
| X, LinkedIn, Bluesky (native upload) | `tracing-llm-api-request-<version>-16x9-1080p.mp4` |
| Remixers, voice-over | `tracing-llm-api-request-<version>-16x9-4k-silent.mp4` |

**Check each platform's video length limit before uploading the 5-minute file.** Some (X for regular accounts, Bluesky) cap
video length. Where it doesn't fit, post the promo (0:43) there instead and put the full video's YouTube link in the reply or
the first comment. LinkedIn takes videos this long.

The promo Short is the YouTube Short for this story. Post it (or the promo's 1080p file) alongside, and in its description or reply
link to this video.

## X

The post, then the link as a reply (X shows posts with links to fewer people). Attach the promo (0:43) if the full video is
too long for your account. The post fits in 280 characters.

```text
What actually happens when you call an LLM API?

I traced one request from your code to the GPU and back, and made it into a 5-minute video: gateway, tokenizer, routing, the queue, prefill, decode, streaming.

Plus 5 ideas that make it fast ⚡

link below 👇
```

```text
Full video (5 min): <insert link to the full video>

Covers prompt caching, continuous batching, the KV cache, disaggregated prefill and speculative decoding.
```

## LinkedIn

The post with the video attached, then the YouTube link as the first comment (LinkedIn shows posts with links to fewer people).

```text
Where does the time go when you call an LLM API?

I made a 5-minute animated video that follows one request from your code to the GPU and back, and shows the stopwatch at every stop:

Client → gateway → tokenizer → cache-aware router → queue → prefill → decode → streamed back to you.

Along the way, five ideas that make LLM serving fast ⚡

• Prompt caching in blocks: why one changed word shouldn't throw away the whole cache
• Continuous batching: keep the GPU busy instead of waiting for the slowest request
• The KV cache: compute keys and values once, reuse them for every token
• Disaggregated prefill: stop long prompts from stalling everyone else's replies
• Speculative decoding: a small model guesses, the big model checks, and it's the same answer, faster

All timings are illustrative. The video is open source: you can reproduce it and remix it.
```

First comment:

```text
Watch (5 min): <insert link to the full video>

Source and how to remix it: https://github.com/sujee/visual-stories/tree/main/projects/tracing-llm-api-request
```

## Bluesky

(fits in 300 characters)

```text
Ever wondered where the time goes when you call an LLM API?

I made a 5-minute video following one request from your code to the GPU and back: queue, prefill, KV cache, decode, streaming, and 5 tricks that make it fast ⚡

<insert link to the full video>
```

## YouTube community post (optional)

For people who watched the promo Short:

```text
The full version is up: one LLM request, traced from your code to the GPU and back (5 min), with the five ideas that make it fast.
<insert link to the full video>
```

## A note on the promo Short

The promo Short already exists. When this video is published, put its link in the Short's description and set the Short's
**Related video** to this video (see `youtube-publishing-full.md`). Nothing else about the Short changes.
