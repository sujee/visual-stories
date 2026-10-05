# Publishing on YouTube: <Story title>

Written by hand (or by your agent): edit it freely. The one exception is the chapter lines between `Chapters:` and `---`
in the full video's description: `render.sh` rewrites them from the render's timeline (chapter titles live in the
story's source, e.g. `src/youtube.py`).

Publish the full video first, because the Short links to it.

## Full video (<m:ss>)

### Upload steps

1. In YouTube Studio, choose **Create → Upload videos** and pick
   `workspace/export/<story>-<version>-16x9-4k.mp4` (the version with music).
2. Paste the **Title** and **Description** below. The chapters appear automatically.
3. **Thumbnail:** `thumbnails/<story>-thumbnail-<design>-16x9.png`.
4. **Audience:** No, it's not made for kids.
5. **Show more:** License **Creative Commons – Attribution**; Category **Science & Technology**;
   Altered or synthetic content **No** (<why, e.g. animated explainer, nothing realistic>); **Tags:** see below.
6. **End screen** (Editor → End screen): the outro runs from <m:ss> to <m:ss>. Add a Subscribe element and a
   "Best for viewer" video, kept clear of the end card's text.
7. **Visibility:** Public (or Unlisted to check it first). Publish.
8. **Pin a comment:** post the **Pinned comment** below and pin it.
9. **Copy the video's URL:** the Short needs it. Once the Short is up, replace `<insert link to the Short>` in the
   description on YouTube.

### Title

```text
<title, under 70 characters>
```

### Description

```text
<hook: the first two lines show before "...more">

<what the video covers>

Short version (<m:ss>): <insert link to the Short>

Chapters:
---

<sources and attribution, the way the video credits them>
Source, brief and how to reproduce or remix it: https://github.com/sujee/visual-stories/tree/main/projects/<story>
Video and music: CC BY 4.0. Code: Apache-2.0.

#<Topic> #<Topic> #MotionGraphics
```

### Pinned comment

```text
<a question that invites replies>
```

### Tags

```text
<comma-separated search tags>
```

## Short (<m:ss>)

### Upload steps

1. Upload `workspace/export/<story>-<version>-9x16-4k.mp4`. It's vertical and under 3 minutes, so YouTube
   treats it as a Short.
2. Paste the **Title** and **Description** below, with the full video's URL in place of `<insert link to the full video>`.
3. **Related video:** set it to the full video, so viewers can tap through from the Short; links typed into a Short's
   description aren't clickable.
4. **Thumbnail:** if your YouTube app offers a custom Short thumbnail, use `thumbnails/<story>-thumbnail-<design>-9x16.png`;
   otherwise pick a cover frame from the hook.
5. Same audience, license, category and tags as the full video. Publish.

### Title

```text
<short title; no #Shorts needed: YouTube detects Shorts, and the description carries the hashtag>
```

### Description

```text
<one or two lines>

Full video: <insert link to the full video>

#Shorts #<Topic> #MotionGraphics
```

## After publishing

### Link them both ways

- On the full video, make sure the description's "Short version" line has the Short's URL.
- On the Short, check that **Related video** points to the full video.

### Back in the repo

- `README.md`: replace "coming soon" with the video and Short links.
- Root `README.md`: add or update the row in the Stories table.
- A GitHub release `<story>-v1` with the four 4K masters (see "GitHub Release" in `AGENTS.md`), linked from both READMEs.
