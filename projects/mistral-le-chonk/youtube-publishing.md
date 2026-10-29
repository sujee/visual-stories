# Publishing on YouTube: Le Chonk-Off

Written by your agent for the approved version; edit it freely. There are no chapters in this guide on purpose: both videos are about 15 seconds, and YouTube only shows chapters for videos with at least three of them, each at least 10 seconds long. `render.sh` does not touch this file.

Publish the full video first, because the Short links to it.

## Replacing the first version

The first upload (v1, Oct 2026: the Watch links in `README.md` before this update) showed Mistral Large 4's open weights as
*expected Oct 31*, with a separate API date. They came out on Oct 29, so the second version (v2) shows Mistral once, on
Oct 29. YouTube can't swap the file behind an existing URL, so the new version is a new upload. Unlist the old one rather
than deleting it: unlisted videos keep their URL (old posts and links still play) and their views and comments, but drop
out of search and the channel page.

1. **Upload the new full video** with the steps under "Full video" below, as **Unlisted**. Watch it once on YouTube.
2. **Upload the new Short** with the steps under "Short" below (Related video: the new full video), also **Unlisted**.
3. **Link the new pair both ways** (see "After publishing"), then set both to **Public**.
4. **Point the old full video to the new one.** In YouTube Studio, open the old video:
   - Put this line at the top of its description:

     ```text
     Updated version (Mistral Large 4's open weights came out on Oct 29): <insert link to the new full video>
     ```

   - Post the same line as a comment, pin it, and unpin the old pinned comment.
   - Set **Visibility** to **Unlisted**. Save.
5. **Point the old Short to the new one.** Same description line, with `<insert link to the new Short>`; set its
   **Related video** to the new full video; set it to **Unlisted**.
6. **Back in the repo**, as under "After publishing": the new links in both READMEs, and a new release
   `mistral-le-chonk-v2` with the new 4K masters. Leave the first release, `le-chonk-off-v1`, as it is.

## Full video (0:15)

### Upload steps

1. In YouTube Studio, choose **Create → Upload videos** and pick
   `workspace/export/mistral-le-chonk-<version>-16x9-4k.mp4` (the version with the quiet piano).
2. Paste the **Title** and **Description** below.
3. **Thumbnail:** `thumbnails/mistral-le-chonk-thumbnail-question-16x9.png` (the hook design). The other design, `…-lineup-16x9.png`,
   is a good one to A/B test against it.
4. **Audience:** No, it's not made for kids.
5. **Show more:** License **Creative Commons – Attribution**; Category **Science & Technology**;
   Altered or synthetic content **No** (a cartoon animation of public numbers, nothing realistic); **Tags:** see below.
6. **End screen:** skip it. The video is only 15 seconds and has no outro to put elements over.
7. **Visibility:** Public (or Unlisted to check it first). Publish.
8. **Pin a comment:** post the **Pinned comment** below and pin it.
9. **Copy the video's URL:** the Short needs it. Once the Short is up, replace `<insert link to the Short>` in the
   description on YouTube.

### Title

```text
Le Chonk-Off: recent 1T+ open models compared as cats
```

### Description

```text
Five recent open models with 1 trillion or more parameters, compared.

(Inspired by Mistral Large 4, nicknamed "Le Chonk" :-)
The newest, Mistral Large 4, joined with its open weights, released on Oct 29, 2026.

In release order: Kimi K3, Qwen3.8, DeepSeek-V4-Pro, MiMo-V2.6-Pro and Mistral Large 4.

Cat size is total parameters. The red smile is how much of the model is active at a time. Perch height is the Artificial Analysis Intelligence Index.

Short version (0:15): <insert link to the Short>

Data: Artificial Analysis Intelligence Index v4.3.2 (since replaced by v5.0); Mistral Large 4's score is for its API preview.
Source, brief and how to reproduce or remix it: https://github.com/sujee/visual-stories/tree/main/projects/mistral-le-chonk

Created by https://sujee.dev

#OpenSourceAI #LLM #AIModels #MotionGraphics
```

### Pinned comment

```text
Which of these 1T+ models do you actually use, and does its size matter to you more than its score?
```

### Tags

```text
open source AI, open weights, LLM, large language models, Kimi K3, Qwen3.8, DeepSeek V4, MiMo, Mistral Large 4, parameters, mixture of experts, Artificial Analysis, intelligence index, AI model comparison
```

## Short (0:15)

### Upload steps

1. Upload `workspace/export/mistral-le-chonk-<version>-9x16-4k.mp4`. It's vertical and under 3 minutes, so YouTube
   treats it as a Short.
2. Paste the **Title** and **Description** below, with the full video's URL in place of `<insert link to the full video>`.
3. **Related video:** set it to the full video, so viewers can tap through from the Short; links typed into a Short's
   description aren't clickable.
4. **Thumbnail:** if your YouTube app offers a custom Short thumbnail, use `thumbnails/mistral-le-chonk-thumbnail-question-9x16.png`;
   otherwise pick a cover frame from the final scene.
5. Same audience, license, category and tags as the full video. Publish.

### Title

```text
Recent 1T+ open AI models, as cats
```

### Description

```text
Cat size = total parameters. Perch height = Artificial Analysis Intelligence Index.

Full video: <insert link to the full video>

#Shorts #OpenSourceAI #LLM
```

## After publishing

### Link them both ways

- On the full video, make sure the description's "Short version" line has the Short's URL.
- On the Short, check that **Related video** points to the full video.

### Back in the repo

- `README.md`: replace the Watch links (video and Short) with the new ones.
- Root `README.md`: update the row in the Stories table.
- A GitHub release `mistral-le-chonk-v2` with the four 4K masters (`mistral-le-chonk-v2-16x9-4k.mp4`, `…-16x9-4k-silent.mp4`, `…-9x16-4k.mp4`, `…-9x16-4k-silent.mp4`; see "GitHub Release" in `AGENTS.md`), linked from both READMEs in place of the first release (`le-chonk-off-v1`).
- The files in `workspace/export/` are not committed. A final render puts its deliverables there automatically (hard links, same names).
