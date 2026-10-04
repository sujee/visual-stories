# How a Neural Network Learns

## Goal
Show how a neural network is trained.

## Audience
Curious non-experts. No math.

## Story
- The network is shown a picture of a cat.
- Try 1: it guesses **dog**. Wrong. The error flows back (backpropagation) and adjusts the weights.
- Try 2: it guesses **rabbit**. Still wrong, so another correction is sent back.
- Try 3: it guesses **cat**. Correct.

## Must communicate
- A network is layers of neurons joined by weighted connections.
- To the network, an image is just numbers (pixels).
- Forward pass: the signal flows through and scores each class; the highest score is the guess.
- Error (loss): how wrong the guess was.
- Backpropagation: the error flows backward and nudges each weight.
- Real training repeats this loop over many images (a brief mention).

## Style
Clean, modern, calm. Motion should explain, not decorate. Plain-language captions.

## Deliverables
- Landscape 16:9, about 2 minutes.
- Short 9:16, under 60 seconds: a condensed version of the full story.

## Credit
End card: **Created by sujee.dev**. Short and understated.

## Creative freedom
The story beats are fixed. You choose the visuals, staging and pacing.
