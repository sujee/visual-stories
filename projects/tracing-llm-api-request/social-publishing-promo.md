# Promo: social and YouTube copy

Copy for posting the promo (a 43 s teaser for the talk "What Happens When You Call a Model API" at Hacktoberfest 2026, online, Thu, Oct 22, 2026, 10am PT / 1pm ET). The posts say "tomorrow": change that if you post on the day of the talk.

Files (in `workspace/export/` after `./render.sh final`, or `workspace/preview/<version>/`):

| Where | File |
|---|---|
| X, LinkedIn, Bluesky | `tracing-llm-api-request-promo3d-<version>-16x9-1080p.mp4` (or `promo2d` for a second post) |
| YouTube (regular video) | `tracing-llm-api-request-promo3d-<version>-16x9-4k.mp4` |
| YouTube Short (optional) | `tracing-llm-api-request-promo3d-<version>-9x16-1080p.mp4` |

Upload the video file directly to X, LinkedIn and Bluesky rather than sharing a YouTube link: feeds autoplay uploads and push links down.

## X

The post, then the link as a reply (X shows posts with links to fewer people). The post fits in 280 characters.

```text
What actually happens when you send a request to an LLM?

Gateway → tokenizer → router → queue → prefill → decode → streamed back to you, one token at a time.

I'm tracing the whole trip tomorrow at Hacktoberfest 2026.

Thu, Oct 22 online @ 10am PT / 1pm ET

link below 👇
```

```text
"What Happens When You Call a Model API"
👉 https://dev.to/events/hacktoberfest-sujee-model-api/october-22-2026

More Hacktoberfest talks: https://hacktoberfest.com/schedule/
```

## LinkedIn

The post, then the event link as the first comment (LinkedIn shows posts with links to fewer people).

```text
What actually happens when you send a request to an LLM?

Client → Gateway → tokenizer → router → queue → prefill → decode → streamed back to you, one token at a time.

Your request is checked at a gateway and turned into tokens. A cache-aware router then sends it to a GPU that probably already holds your prompt in its cache, where it's batched with other people's requests. Then it's processed in two very different phases:

⚡ Prefill reads your whole prompt in one parallel pass. Much of your wait for the first token is spent here and in the queue.
🐢 Decode writes the reply one token at a time. That's part of why output tokens cost more than input tokens.

Tomorrow at Hacktoberfest 2026 I'm giving a talk, "What Happens When You Call a Model API", that follows a single request from your code to the GPU and back, and shows where the time goes.

📍 Online, Thu, Oct 22, 10am PT / 1pm ET
https://dev.to/events/hacktoberfest-sujee-model-api/october-22-2026

More Hacktoberfest talks: https://hacktoberfest.com/schedule/
```

First comment:

```text
Event page: https://dev.to/events/hacktoberfest-sujee-model-api/october-22-2026

More Hacktoberfest talks: https://hacktoberfest.com/schedule/
```

## Bluesky

(fits in 300 characters)

```text
Ever wondered where the time goes when you call an LLM API?

Queue, prefill, KV cache, decode, streaming: I'm following one request from your code to the GPU and back.

Talk tomorrow at Hacktoberfest 2026 (10am PT) ✨
https://dev.to/events/hacktoberfest-sujee-model-api/october-22-2026
```

## YouTube

Playlist: Promos (or a viewer-facing name such as "Talk teasers").

**Title**

```text
What Happens When You Call an LLM API? | Hacktoberfest 2026 talk teaser
```

**Description**

```text
Follow one LLM API request from your code to the GPU and back: gateway, tokenizer, cache-aware router, batching, prefill, decode, and the tokens streaming back to you.

This is a teaser for my talk
"What Happens When You Call a Model API - tracing the request from the client to GPU and back"
at Hacktoberfest 2026 on October 22, 2026.
🔗 https://dev.to/events/hacktoberfest-sujee-model-api/october-22-2026

Timings shown are illustrative. Created by sujee.dev.
Music: original, generated in code. Video and soundtrack licensed under CC BY 4.0.

#LLM #AI #GPU
```

**Tags**

```text
LLM, LLM inference, KV cache, prefill, decode, time to first token, AI engineering, GPU, API
```

## YouTube Short (if you post the vertical version)

**Title**

```text
What happens when you call an LLM API? #shorts
```

**Description** (after the talk: it points to the full video)

```text
One LLM request, from your code to the GPU and back, in 43 seconds: gateway, tokenizer, cache-aware router, queue, prefill, decode and the tokens streaming back to you.

Watch the full 5-minute explainer, with chapters: <insert link to the full video>

From my Hacktoberfest 2026 talk "What Happens When You Call a Model API". Event page: https://dev.to/events/hacktoberfest-sujee-model-api/october-22-2026

Timings are illustrative. Created by sujee.dev. Music: original, generated in code. Video and music: CC BY 4.0.

#LLM #AI #GPU #Shorts
```
