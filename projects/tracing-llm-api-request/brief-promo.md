# Tracing an LLM API Request

## Goal
Follow one LLM API request from the client all the way to the GPU and back, until the response is received.

## Audience
Developers who call LLM APIs (send messages, get a streamed reply, pay per token) but have never looked at what happens on the provider's side.

## Story
- A short prompt leaves the developer's code as an HTTPS request, and a stopwatch starts.
- The API gateway checks authentication and rate limits.
- The text becomes tokens.
- A cache-aware router picks the replica most likely to already hold this prompt's prefix in its KV cache.
- The request waits in a queue and is batched with other people's requests on a GPU.
- **Prefill:** the whole prompt in one parallel pass, filling the KV cache. The first token comes out.
- **Decode:** one token per pass, each reusing the KV cache, streamed back to the developer as it's made.
- A stop token (or the token limit) ends it, usage is counted, and the stopwatch stops. A recap shows the whole trip on one line, with where the time went.

## Must communicate
- **Time to first token** is mostly queueing plus prefill; after that, speed is decode's **tokens per second**. Long prompts delay the first token; long replies stretch the total.
- Prefill is parallel and compute-bound; decode is sequential and memory-bound. That's why output tokens cost more than input tokens.
- The **KV cache** spares decode from recomputing the prompt; **prompt caching** reuses it across requests, which is why cache-aware routing pays off.
- **Batching:** one GPU serves many requests at once.
- **Streaming** (server-sent events) is why the reply appears word by word.

## Style
Technical but approachable, clean and modern, dark background. One continuous journey, not slides:
- **The camera follows a single packet:** the request (a glowing packet, then a row of tokens) travels through a map of the system, close up.
- **At each decision point it pauses and zooms out** to show the choices: e.g. allowed or rate-limited, which replica, which batch. The chosen path lights up.
- **Then it zooms back in and moves on** with the packet.

A timeline along the bottom shows the stages (gateway, tokenizer, router, queue, prefill, decode, …) with a stopwatch: the current stage is highlighted, and each stage's segment grows to show how long the request spent there. Visuals over text; brief labels at each stop. Calm, minimal original music behind the visuals.

## Constraints
- Provider-neutral: no logos or branding, and no claim that a particular provider works exactly this way.
- Timings, token counts and prices are illustrative; label them as examples.

## Deliverables
All at 30 fps, each in 4K with music, 4K silent, and a 1080p copy with music (for X, LinkedIn, Bluesky).
- **Full video, 16:9**, about 2 minutes.
- **Short, 9:16**, about 40 seconds: a standalone cut of prefill vs. decode and why the first token takes longest, ending with a pointer to the full video.
- **Promo, 16:9, plus a 9:16 Short of the 3D version**, 30–45 seconds: a promo, not an explainer. A hook, a fast montage of the most striking moments (with the stage timeline along the bottom), and a closing title card with the request bouncing from the client to the GPU and back (no call to action: it's for social media). Very little text; house music (120 BPM): four-on-the-floor kick, off-beat hats, chord stabs and a plucked melody. Two versions of the promo: 2D (`promo2d`) and 3D (`promo3d`), same beats and music; the 3D one also as a vertical Short. File names put `promo2d` or `promo3d` after the story name, e.g. `tracing-llm-api-request-promo2d-v1-16x9-4k.mp4`.
- YouTube publishing guide (`youtube-publishing-full.md`), with chapters for the full video.
- YouTube thumbnails: a few designs for the full video and the Short, and for the promo (16:9 and its Short).

## Credit
End card, small and quiet, away from the right side (YouTube's end-screen buttons). Word for word:

**Full video:**
```text
Created by sujee.dev
Liked this? A 👍 helps others discover it.
```

**Short and promo:**
```text
Created by sujee.dev
```

## Creative freedom
You choose the visuals, story and pacing, within the Story beats above. This is a set of goals, not a scene-by-scene script.
