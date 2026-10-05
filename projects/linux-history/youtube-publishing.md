# Publishing on YouTube: Linux History

Written by hand (or by your agent): edit it freely. The one exception is the chapter lines between `Chapters:` and `---`
in the full video's description: `render.sh` rewrites them from the render's timeline (chapter titles live in
`src/youtube.py`).

Publish the full video first, because the Short links to it.

## Full video (2:00)

### Upload steps

1. In YouTube Studio, choose **Create → Upload videos** and pick
   `workspace/export/linux-history-<version>-16x9-4k.mp4` (the version with music).
2. Paste the **Title** and **Description** below. The chapters appear automatically.
3. **Thumbnail:** `thumbnails/linux-history-thumbnail-birthday-16x9.png` (it matches the title). Optionally use
   **Test & Compare** (Details → Thumbnail) against `hobby` and `tree` from the same folder.
4. **Audience:** No, it's not made for kids.
5. **Show more:** License **Creative Commons – Attribution**; Category **Science & Technology**;
   Altered or synthetic content **No** (animated infographic, nothing realistic); **Tags:** see below.
6. **End screen** (Editor → End screen): the outro runs from 1:52 to 2:00. Add a Subscribe element and a
   "Best for viewer" video, kept to the sides so they don't cover the closing text.
7. **Visibility:** Public (or Unlisted to check it first). Publish.
8. **Pin a comment:** post the **Pinned comment** below and pin it.
9. **Copy the video's URL:** the Short needs it. Once the Short is up, replace `<insert link to the Short>` in the
   description on YouTube.

### Title

```text
Linux Turns 35: From "Just a Hobby" to Running the World
```

### Description

```text
Linux turns 35. In 1991, a 21-year-old student called his new operating system "just a hobby, won't be big and professional." Today it runs the world. 🎂

Published Oct 5, 2026: 35 years after Linus publicly released Linux 0.02.

The story of Linux in 2 minutes: from its Unix roots at Bell Labs (1969) to GNU, from Linux 0.01 to Debian, Red Hat, Ubuntu, Arch and Android, and on to the cloud, every top supercomputer, and a helicopter on Mars.

Short version (0:30): <insert link to the Short>

Chapters:
0:00 Before Linux: Unix, BSD & GNU (1969–1990)
0:27 1991: "just a hobby" & the first distros (1991–1995)
0:49 Open source goes mainstream (1996–2003)
1:06 Ubuntu, Git, the cloud & Android (2004–2012)
1:24 Containers, Kubernetes & the TOP500 (2013–2019)
1:38 Mars, Rust & Linux today (2020–2026)
---

By the numbers
• Linux 0.01 (1991): ~10,000 lines of code
• The Linux kernel today: 40+ million lines
• Runs 100% of the world's TOP500 supercomputers (since November 2017)
• Powers billions of Android devices
• Flew on Mars aboard NASA's Ingenuity helicopter (2021)

Featured: Unix, BSD, MINIX, GNU, Linux, Slackware, SUSE, Debian, Ubuntu, Linux Mint, Pop!_OS, Red Hat, Fedora, CentOS, Rocky Linux, Arch, Gentoo, ChromeOS, Android, Alpine.
Kernel sizes and some dates are approximate.

Visuals and music are generated entirely in code; the soundtrack is original.
Source, brief and how to reproduce or remix it: https://github.com/sujee/visual-stories/tree/main/projects/linux-history
Video and music: CC BY 4.0. Code: Apache-2.0.

What was your first Linux distro?

#Linux #OpenSource #History #MotionGraphics
```

### Pinned comment

After Oct 5, say "35 years ago" instead of "35 years ago today".

```text
Happy 35th birthday, Linux! 🐧 35 years ago today (Oct 5, 1991), Linus publicly released Linux 0.02. What was your first distro, and when did you install it?
```

### Tags

```text
linux history, history of linux, linux, linus torvalds, open source, unix, gnu, linux distros, debian, ubuntu, red hat, arch linux, android, linux kernel, free software, operating system history, data visualization, motion graphics, synthwave
```

## Short (0:30)

### Upload steps

1. Upload `workspace/export/linux-history-<version>-9x16-4k.mp4`. It's vertical and under 3 minutes, so YouTube
   treats it as a Short.
2. Paste the **Title** and **Description** below, with the full video's URL in place of `<insert link to the full video>`.
3. **Related video:** set it to the full video. This is the link the Short's end card points at ("tap the link below");
   links typed into a Short's description aren't clickable.
4. **Thumbnail:** if your YouTube app offers a custom Short thumbnail, use
   `thumbnails/linux-history-thumbnail-birthday-9x16.png` (or `quote`, `got-big`, `takeover`); otherwise pick a cover
   frame near 0:11.
5. Same audience, license, category and tags as the full video. Publish.

### Title

```text
In 1991, Linux was "just a hobby"… 🐧
```

### Description

```text
Aug 25, 1991: a student in Helsinki posts "just a hobby, won't be big and professional." It got big.

Full 2-minute history: <insert link to the full video>

#Shorts #Linux #OpenSource #MotionGraphics
```

## After publishing

### Link them both ways

- On the full video, make sure the description's "Short version" line has the Short's URL.
- On the Short, check that **Related video** points to the full video.
- Optional: point an end screen element on the full video at the Short.

### Back in the repo

- `README.md`: replace "coming soon" with the video and Short links.
- Root `README.md`: add or update the row in the Stories table.
- A GitHub release `linux-history-v1` with the four 4K masters (see "GitHub Release" in `AGENTS.md`), linked from
  both READMEs.
