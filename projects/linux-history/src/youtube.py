"""Refresh the chapter timestamps in youtube-publishing.md from the render's own timeline.

youtube-publishing.md is written by hand (or by an agent) and is freely editable: title, description, steps.
This script only replaces the lines between a line reading "Chapters:" and the next line reading "---", so the
chapters always match the video, and checks YouTube's chapter rules (first at 0:00, at least 3, each at least 10 s).
render.sh runs it.

    python src/youtube.py youtube-publishing.md

Chapter titles and where each one starts are below: edit CHAPTERS to rename, add or remove chapters.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import video as V

# (year the chapter starts, title). The first chapter starts at 0:00 and covers the intro.
CHAPTERS = [
    (None, 'Before Linux: Unix, BSD & GNU (1969–1990)'),
    (1991, '1991: "just a hobby" & the first distros (1991–1995)'),
    (1996, 'Open source goes mainstream (1996–2003)'),
    (2004, 'Ubuntu, Git, the cloud & Android (2004–2012)'),
    (2013, 'Containers, Kubernetes & the TOP500 (2013–2019)'),
    (2020, 'Mars, Rust & Linux today (2020–2026)'),
]
START, END = 'Chapters:', '---'


def mmss(sec):
    sec = int(sec)
    return f'{sec // 60}:{sec % 60:02d}'


def chapter_lines():
    # 1991 starts at the announcement scene; later chapters where their year reaches the playhead
    starts = [0] + [int(V.ANN_T0 if y == 1991 else V.t_of(y)) for y, _ in CHAPTERS[1:]]
    ends = starts[1:] + [int(V.DUR)]
    assert len(starts) >= 3, 'YouTube needs at least 3 chapters'
    for (_, title), a, b in zip(CHAPTERS, starts, ends):
        assert b - a >= 10, f'chapter "{title}" is {b - a}s; YouTube needs at least 10s per chapter'
    return [f'{mmss(a)} {title}' for (_, title), a in zip(CHAPTERS, starts)]


def main(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    starts = [k for k, line in enumerate(lines) if line.strip() == START]
    if len(starts) != 1:
        sys.exit(f'{path}: expected exactly one line reading "{START}" (found {len(starts)}). In the video description, '
                 f'add "{START}", then a line reading "{END}"; render.sh fills in the chapters between them.')
    i = starts[0]
    j = next((k for k in range(i + 1, len(lines)) if lines[k].strip() == END), None)
    if j is None:
        sys.exit(f'{path}: no line reading "{END}" after "{START}"; add one to mark where the chapters end.')
    old_block, new_block = lines[i + 1:j], chapter_lines()
    if old_block and old_block != new_block:      # warn, so a hand edit that gets replaced is visible
        print(f'warning: {path}: replacing chapter lines (rename chapters in CHAPTERS in src/youtube.py, '
              'not in the guide):', file=sys.stderr)
        for k in range(max(len(old_block), len(new_block))):
            o = old_block[k] if k < len(old_block) else ''
            n = new_block[k] if k < len(new_block) else ''
            if o != n:
                print(f'  - {o}\n  + {n}', file=sys.stderr)
    new = lines[:i + 1] + new_block + lines[j:]
    if new != lines:
        open(path, 'w', encoding='utf-8').write('\n'.join(new))
        print(f'{path}: chapters updated')
    else:
        print(f'{path}: chapters already current')


if __name__ == '__main__':
    main(sys.argv[1])
