# Le Chonk-Off

## Goal
A quick, playful look at recent open models with a trillion parameters or more: how big they are, how smart they score, and when each one came out. It is a selection of recent releases, not a complete list.

## Audience
Developers and AI-curious people who follow open-model news but don't track the numbers.

## Story
- Cats, one per model, drop in release-date order onto perches. Perch height is how smart the model scores.
- Each cat's size shows how big the model is.
- A fish swims by and the cats get excited. Their red smile shows how much of the model is active at a time.
- The newest cat, Mistral's "Le Chonk", comes last. The credit stays quietly on the final scene.

## Must communicate
- Bigger cat, bigger model.
- Only a small slice of each model is active at a time (the smile).
- Size isn't intelligence: perch height is the Artificial Analysis Intelligence Index.
- Release order, with Mistral Large 4 on the API now and open weights expected on Oct 31, 2026.

## Style
Bright cartoon, plain words, very little text. Each vendor gets its own cat color; Mistral is the orange tabby. Sound is only a very quiet, mellow piano: no effects, no beat.

## Constraints
- Numbers come from `models.csv`.
- Mistral Large 4's intelligence score is from the preview.
- The piano is mixed far quieter than the usual video loudness, on purpose: it should stay an undertone.

## Deliverables
Two videos, 30 fps, each under 20 seconds:
- **Landscape 16:9:** 4K (3840×2160) with piano, 4K silent, and a 1080p (1920×1080) copy with piano.
- **Vertical 9:16 Short:** 4K (2160×3840) with piano, 4K silent, and a 1080p (1080×1920) copy with piano. Laid out for the tall frame, not cropped, and clear of the bottom and right edges where phone apps put their buttons.

The 1080p copies are for posting directly on social media (X, LinkedIn, Bluesky).

Also, for each format:
- **A clean still** of the final scene, without confetti, as a PNG at the 4K size, for screenshots. A final render also copies it, without the version in its name, to `thumbnails/mistral-le-chonk-still-<16x9|9x16>.png`.
- **YouTube thumbnails**, two designs ("lineup" with the title, and "question" with a hook): 1280×720 for 16:9 and 1080×1920 for 9:16, each under 2 MB, in `thumbnails/`.

A YouTube publishing guide (`youtube-publishing.md`, written by the agent once a version is approved, then yours to edit): upload steps, a title and description for each video, a pinned comment and tags. It has no chapters, because the videos are too short for YouTube chapters.

## Credit
Show this in small type on the final scene, word for word, on both videos:
```text
Created by sujee.dev
```

## Creative freedom
You choose the visuals, staging and pacing, within the story above.
