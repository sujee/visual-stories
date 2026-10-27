# What Happens When We Call an LLM API?

The full-length explainer. The 30–45 second promos (2D and 3D) have their own brief: [brief-promo.md](brief-promo.md).

## Goal
Follow one LLM API request from the client all the way to the GPU and back, until the response is received, and explain why each hop is there and what the major optimizations do. A viewer who has never looked inside an inference provider should come away able to say where the time goes.

## Audience
Developers who call LLM APIs (send messages, get a streamed reply, pay per token) but have never looked at what happens on the provider's side.

## Story
About 5 minutes, one running example: a short prompt ("Why is the sky blue?", 6 tokens) and a reply of 20 tokens. Beats in order; the approximate length of each chapter is a guide, not a script. The YouTube chapters follow these beats (a beat can become two chapters). Each optimization is introduced the same way: a title card with a lightning "OPTIMIZATION" badge, the problem it solves, then the fix.

1. **Hook and the send (0:00–0:11).** "What happens when we call an LLM API?" A short prompt leaves the developer's code as an HTTPS request, and the timer and the stage time bar along the bottom start. The time bar is the map the rest of the video follows.
2. **Gateway and tokenizer (0:11–0:30).** The gateway checks the API key, rate limits and request validity (about 30 ms of network and 15 ms at the gateway in the example); over the limit, a 429. Then text becomes token IDs on the CPU: the model never sees text, and providers bill by tokens.
3. **Routing (0:30–0:45).** Inference routing is not web routing: the router picks a replica (one full copy of the model, with its own queue and GPU). Each replica keeps recent prompts in its cache, and the router sends the request to one that already holds the start of it: a cache hit.
4. **Efficient prompt caching (0:45–1:24).** Optimization. Hash the whole prompt and one changed word gives a different hash and no match. So caches work in hashed blocks that each include the block before them: the first matching blocks are reused. The router's table of who holds which blocks is a hint, not a promise.
5. **The replica's queue and continuous batching (1:24–1:56).** The request waits in the replica's queue. Optimization: static batching waits for the slowest request, while continuous batching lets finished requests leave and new ones join at every step, so the GPU stays busy and our request starts sooner.
6. **Prefill (1:56–2:07).** The whole prompt in one parallel, compute-bound pass; the cached start is reused and only the new tokens are computed; the first token comes out (about 0.42 s after the send in the example). Time to first token is queue plus prefill.
7. **The KV cache (2:07–2:44).** Optimization. Each token makes a key and a value; the next token looks back at all of them. Without a cache, every new token recomputes all the tokens before it (51 key/value cells against 11 in the example). The cache grows by one entry per pass, which is also its cost: GPU memory.
8. **Decode (2:44–2:58).** One token per pass, memory-bound (every pass re-reads the KV cache), streamed back as it is made, which is why output tokens cost more than input tokens.
9. **Disaggregated prefill (2:58–3:40).** Optimization. The problem: on one GPU a long prefill is a compute burst that makes everyone else's decode stall. The fix: give prefill and decode their own GPU pools, hand the KV cache across a fast link, and tune each pool for its own job.
10. **Speculative decoding (3:40–4:20).** Optimization. The problem: a big model writes one token per slow pass. The fix: a smaller draft model guesses several tokens quickly and the big model checks them all in one pass. Right guesses are kept, the first wrong one is replaced, and the output is identical to the big model alone, in less time.
11. **Streaming back (4:22–4:52).** The model keeps going until it emits a stop token. Each token ID is turned back into text and streamed (server-sent events) as it is made, which is why the reply appears word by word, until the stream closes.
12. **Where did the time go? (4:52–5:18).** The whole trip on one line on one time scale: network and gateway, tokenize and route, queue, prefill, first token back (about 0.42 s) and then decode (about 1.7 s; 2.14 s end to end in the example). Where each of the five ideas helps. Then the end card.

## Must communicate
- **Time to first token** is mostly queueing plus prefill; after that, speed is decode's **tokens per second**. Long prompts delay the first token; long replies stretch the total (E2E = TTFT + (tokens − 1) / speed).
- Prefill is parallel and compute-bound; decode is sequential and memory-bound. That's why output tokens cost more than input tokens.
- The **KV cache** spares decode from recomputing the prompt; **prompt caching** reuses it across requests, which is why cache-aware routing pays off.
- **Why each optimization works:** speculative decoding trades spare compute for fewer sequential passes (the output is the same as without it); disaggregation removes the interference between a compute-bound and a memory-bound job; continuous batching keeps the GPU busy.
- **Streaming** (server-sent events) is why the reply appears word by word.

## Style
Technical but approachable, clean and modern, dark background. One continuous journey, not slides, in 2D (a 3D version was tried in an early draft: it was striking, but you never saw the whole picture). No voiceover; concepts are explained by animation and brief labels.
- **One map of the whole route:** your code, gateway, tokenizer, router, three replicas (each with a queue and a GPU) and the way back, all on one canvas. The full picture is always one zoom-out away.
- **A camera zooms in on each stop,** following the request (a glowing packet, then a row of tokens) and showing what happens there: the checks at the gateway, the tokens and their ids, the router's choice between replicas, the queue, the GPU.
- **Every stop starts with a transition card:** the time bar comes to the middle of the screen with the stop highlighted ("entering the router"), then drops back down along the bottom as the camera zooms in.
- **Each explainer has one idea and one picture**, built up step by step (blocks and hashes for prompt caching; a draft row checked in one pass for speculative decoding), then released back to the map.

A time bar along the bottom shows the stages (network, gateway, tokenizer, router, queue, prefill, decode) with a timer: the current stage is highlighted, a small marker moves along it, and each stage's segment grows to show how long the request spent there; it is hidden during an explainer. Each explainer opens with a black fade and a title card, like a slide; the optimization cards carry a gold lightning badge. Visuals over text; brief labels at each stop. Calm, minimal original music behind the visuals, with room for the pace to breathe in the explainers.

## Constraints
- Provider-neutral: no logos or branding, and no claim that a particular provider works exactly this way.
- Timings, token counts and sizes are illustrative; label them as examples.
- Keep to the chapters above. Material that is deliberately left out: quantization, sharding across GPUs, mixture of experts, GQA, CUDA graphs, sampling, observability.

## Deliverables
All at 30 fps, each in 4K with music, 4K silent, and a 1080p copy with music (for X, LinkedIn, Bluesky).
- **Full video, 16:9**, about 5 minutes (the current draft is 5:18), with YouTube chapters.
- **No separate Short:** the promo's Short (`brief-promo.md`) is the Short for this story and links to the full video.
- YouTube publishing guide (`youtube-publishing-full.md`), with chapters for the full video, and social copy (`social-publishing-full.md`).
- YouTube thumbnails: a few designs for the full video.

## Credit
End card, small and quiet, away from the right side (YouTube's end-screen buttons). Word for word:

**Full video:**
```text
Created by sujee.dev
Liked this? A 👍 helps others discover it.
```

**Short:**
```text
Created by sujee.dev
```

## Creative freedom
You choose the visuals, metaphors and pacing, within the chapters above. This is a set of goals, not a scene-by-scene script.
