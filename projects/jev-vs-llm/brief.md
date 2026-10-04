# Jev: A System One Model

## Goal
The viewer understands what makes Jev, TypeSafe AI's "System One" model, different from a chat LLM. It doesn't generate text. It reads a program's state and returns typed decisions with calibrated probabilities that code can act on directly. That trade is why it can be so much faster and cheaper on narrow, fast decisions.

## Audience
Developers who have used LLM APIs (prompts, tokens, JSON output) but haven't heard of Jev or "System One models".

## Story
The core idea, which everything else follows from: an LLM's possible outputs are *every string*, built one model pass per token; Jev's possible outputs are only the options you define, filled with probability in one pass. Tell it in six titled sections, in this order:

1. **System 1 decisions:** software is full of quick, intuitive decisions (e.g. routing a support ticket to refund, billing, shipping or other).
2. **Jev vs. LLM:** the same ticket goes to an LLM, which builds a string token by token, one model pass each. Point out which part of the string is its answer. That string could be anything, and here it invents a label that isn't one of the options the code expects. Then Jev: the space of possible answers collapses to the options you defined, and one pass gives a probability for each.
3. **Typed answers:** pick one, score on a scale, yes/no. Every answer is a set of probabilities.
4. **Why it's fast:** one pass instead of one per token, then TypeSafe's claimed numbers.
5. **Acting on probabilities:** tickets above a confidence threshold are handled automatically and the rest go to a person; this only works if the probabilities are calibrated, which is what RLCD trains for.
6. **Jev + LLMs:** Jev can't write, so writing stays with an LLM. Together: Jev makes the fast calls, LLMs write the words, people handle the unsure cases.

## Must communicate
- **System 1** is Kahneman's fast, intuitive thinking (vs. slow, deliberate System 2).
- Jev's outputs are fixed in advance: no malformed output, no answer outside the options. The flip side: no paragraphs, code, or refusals.
- **Calibrated** means higher confidence goes with higher accuracy. **RLCD** (Reinforcement Learning for Calibrated Decisions) rewards probabilities that match outcomes; **RLHF** rewards answers human raters prefer.
- TypeSafe's claims: 70–500 ms responses, 40–200× faster and much cheaper than frontier LLMs. Present them as claims.
- Jev is the "smart if-statement" in software (routing, scoring, guardrails); LLMs do open-ended, human-facing work.

## Style
Technical but approachable, clean and modern. Prefer visuals over text: show the shape of the data (unstructured state in, typed values and probabilities out) rather than describing it. One visual motif for Jev's answers throughout, so the idea reads as a single picture rather than a series of slides. Make every section change obvious: a numbered title card for each section, and the current section's name visible while it plays.

Music: simple, minimal modern piano with a soft, felt-like tone. Slow, level and mellow, with no melody line, no percussion and no build-up. Accents only as single soft notes (section changes, Jev's answer). It sits behind the visuals and never competes with them; busier styles were tried and felt distracting.

## Constraints
- Show an LLM and Jev handling the same decision, so the contrast is visible rather than told.
- Stay neutral and factual. This isn't an ad. Attribute performance numbers to TypeSafe AI and don't invent figures. Facts come from TypeSafe's launch post (typesafe.ai/blog/introducing-system-one-models-and-jev, September 2026). Jev is proprietary and in early access, and no independent evaluation had been published at the time of writing.
- Any probabilities, confidences or counts used as examples are illustrative; label them so where they could be mistaken for measurements.
- Don't use TypeSafe AI's logo or branding assets. Name the company and the model in text only.
- When a scene has a lot of text, give the viewer enough time to read it.

## Deliverables
- Landscape 16:9, about 2 minutes.
- Short 9:16, about 35 seconds: a standalone cut of the core idea, not a condensed version of the full story. Hook in the first seconds, then Jev vs. LLM (section 2), one line on why it matters (fast, and the confidence tells code when to act), and a closing pointer to the full video. No section cards.
- 1080p copies of both videos (with music) for posting directly on X and LinkedIn.
- YouTube publishing guide: step-by-step upload instructions (full video first, then the Short linking to it) and a description for each video, with chapter timestamps for the landscape video (one chapter per section).
- YouTube thumbnails: a few designs, each for both videos (16:9 and 9:16), to pick from.

## Credit
End card: **Created by sujee.dev with Claude Code (Opus 5.5)**. Short and understated.

## Creative freedom
You choose the visuals, metaphors and pacing within the Story beats above. This is a set of goals, not a scene-by-scene script.
