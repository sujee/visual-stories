"""The Short (9:16, 30 s): 'just a hobby' (1991) -> IT GOT BIG -> watch the full story.

Layout is in 1080x1920 logical coordinates; SCALE=2 renders 2160x3840. FPS sets the frame rate.
The end card shows the landscape thumbnail thumbnails/linux-history-thumbnail-tree-16x9.png.

    python src/short.py chunk <first_frame> <end_frame> <out.mp4>
    python src/short.py still <out_dir> <t> [<t> ...]
"""
import os, sys, math, random, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import video as V

W, H, DUR = 1080, 1920, 30.0          # logical layout space
S, FPS = V.S, V.FPS                   # from the SCALE and FPS environment variables
RW, RH = W * S, H * S
BG, TEXT, DIM, YEL, MAG, CYAN, GREEN, ORANGE, RED = V.BG, V.TEXT, V.DIM, V.YEL, V.MAG, V.CYAN, V.GREEN, V.ORANGE, V.RED
TERM = (90, 220, 150)
scale = V.scale
THUMB_PATH = Path(__file__).resolve().parents[1] / 'thumbnails' / 'linux-history-thumbnail-tree-16x9.png'
_thumb = []


def thumb():
    if not _thumb:
        _thumb.append(Image.open(THUMB_PATH).convert('RGB'))
    return _thumb[0]

_fonts = {}


def F(size, bold=True):
    k = (size, bold)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(V.FONT_BOLD if bold else V.FONT_REG, size * S)
    return _fonts[k]


def glow(base, neon, strength=1.5, radius=6):
    small = neon.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius))
    g = small.resize((RW, RH), Image.BILINEAR)
    a = np.asarray(base, np.int16) + np.asarray(neon, np.int16) + (np.asarray(g, np.float32) * strength).astype(np.int16)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def ease(x):
    x = min(1, max(0, x))
    return 1 - (1 - x) ** 3


def pulse(t):
    on = 4 <= t < 11.5 or 12 <= t < 28
    return math.exp(-((t * 2) % 1.0) * 6) if on else 0.0


def ctext(d, y, s, font, fill):
    w = d.textlength(s, font=font)
    d.text(((W - w) / 2, y), s, font=font, fill=fill)
    return (W - w) / 2, w


def typed(s, t, t0, cps):
    return s[:max(0, int((t - t0) * cps))]


def cursor(d, x, y, size, t):
    if int(t * 3) % 2 == 0:
        d.rectangle((x + 4, y + 6, x + 4 + size * 0.55, y + size * 1.05), fill=TERM)


def background(t):
    base = Image.new('RGB', (RW, RH), BG)
    neon = Image.new('RGB', (RW, RH))
    n = V.SD(neon)
    hy = 1560
    c = scale((45, 12, 70), 1 + 0.8 * pulse(t))
    for k in range(-14, 15):
        n.line((W / 2 + k * 40, hy, W / 2 + k * 230, H), fill=c, width=2)
    for k in range(1, 10):
        y = hy + (H - hy) * ((k + (t * 1.2) % 1) / 10) ** 2
        n.line((0, y, W, y), fill=c, width=2)
    return base, neon


# ---------------- 0-3s hook ----------------
def hook(t, d, n):
    if t > 0.15:
        a = ease((t - 0.15) / 0.3)
        j = int(10 * math.exp(-(t - 0.15) * 6) * math.sin(t * 80))
        f = F(300)
        w = n.textlength('1991.', font=f)
        n.text(((W - w) / 2 - 8 - j, 492), '1991.', font=f, fill=scale(MAG, 0.6 * a))
        n.text(((W - w) / 2 + j, 500), '1991.', font=f, fill=scale(YEL, a))
    lines = [('A 21-year-old student', 0.9), ('in Helsinki posts a', 1.6), ('message online…', 2.2)]
    for i, (s, t0) in enumerate(lines):
        if t >= t0:
            sub = typed(s, t, t0, 32)
            x = (W - d.textlength(s, font=F(58))) / 2   # center on the full line so typing doesn't shift
            d.text((x, 900 + i * 85), sub, font=F(58), fill=TEXT)


# ---------------- 3-11s the post ----------------
HEADER = [('From: ', 'torvalds@klaava.Helsinki.FI'), ('Newsgroups: ', 'comp.os.minix'),
          ('Subject: ', 'What would you like to see'), ('', '         most in minix?'),
          ('Date: ', '25 Aug 91 20:57:08 GMT')]
BODY = [("Hello everybody out there using", None), ("minix -", None), ("", None),
        ("I'm doing a (free) operating", None), ("system (", "just a hobby, won't"), ("", "be big and professional"),
        (" like gnu) for 386(486) AT", None), ("clones.", None)]


def body_runs():
    """[(line_index, text, highlighted)] in order, for typing."""
    runs = []
    for i, (plain, hl) in enumerate(BODY):
        if plain:
            runs.append((i, plain, False))
        if hl:
            runs.append((i, hl, True))
    return runs


RUNS = body_runs()
NCH = sum(len(r[1]) for r in RUNS)


def post(t, d, n, card_alpha=1.0):
    k = card_alpha
    x0, y0, x1, y1 = 50, 330, 1030, 1420
    d.rounded_rectangle((x0, y0, x1, y1), 24, fill=scale((18, 13, 34), k), outline=scale((70, 50, 120), k), width=3)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((x0 + 30 + i * 36, y0 + 26, x0 + 52 + i * 36, y0 + 48), fill=scale(c, k))
    d.text((x0 + 150, y0 + 22), 'comp.os.minix — Usenet', font=F(30, False), fill=scale(DIM, k))
    f = F(36, False)
    fb = F(36)
    # header types fast
    nh = int(max(0, t - 3.2) * 160)
    y = y0 + 100
    for key, val in HEADER:
        full = key + val
        sub = full[:nh]
        nh -= len(full)
        d.text((x0 + 40, y), sub[:len(key)], font=fb, fill=scale(CYAN, k))
        d.text((x0 + 40 + d.textlength(key, font=fb), y), sub[len(key):], font=f, fill=scale(TEXT, k * 0.85))
        y += 52
        if nh <= 0:
            break
    # body types at a readable pace
    shown = int(max(0, t - 4.2) * 44)        # fully typed by ~7.6 s, then held until 9.5 s
    ybase = y0 + 400
    xs = {}
    last = None
    for li, s, hl in RUNS:
        if shown <= 0:
            break
        sub = s[:shown]
        shown -= len(s)
        x = xs.get(li, x0 + 40)
        yy = ybase + li * 72
        if hl:
            n.text((x, yy), sub, font=F(40), fill=scale(YEL, k))
            xs[li] = x + n.textlength(sub, font=F(40))
        else:
            d.text((x, yy), sub, font=F(40, False), fill=scale(TEXT, k))
            xs[li] = x + d.textlength(sub, font=F(40, False))
        last = (xs[li], yy)
    if last and k > 0.9:
        cursor(d, last[0], last[1], 40, t)


# ---------------- 11-13s: won't be big ... IT GOT BIG ----------------
def zoom_quote(t, d, n):
    lines = [('just a hobby,', 9.7), ("won't be big", 10.05), ('and professional', 10.4)]
    for i, (s, t0) in enumerate(lines):
        if t >= t0:
            a = ease((t - t0) / 0.25)
            f = F(96)
            w = n.textlength(s, font=f)
            x, y = (W - w) / 2, 640 + i * 140 + (1 - a) * 30
            n.text((x, y), s, font=f, fill=scale(YEL, a))
            if i == 1 and t >= 11.0:
                k = ease((t - 11.0) / 0.3)
                n.line((x - 10, y + 62, x - 10 + (w + 20) * k, y + 62), fill=RED, width=12)


def got_big(t, d, n):
    a = ease((t - 12) / 0.12)
    s = 1 + 0.25 * math.exp(-(t - 12) * 10)
    for i, (txt, col) in enumerate([('IT GOT', TEXT), ('BIG.', YEL)]):
        f = F(int(200 * s) if i == 0 else int(300 * s))
        w = n.textlength(txt, font=f)
        y = 560 + i * 260
        if i == 1:
            n.text(((W - w) / 2 - 10, y - 10), txt, font=f, fill=scale(MAG, 0.6 * a))
        n.text(((W - w) / 2, y), txt, font=f, fill=scale(col, a))


# ---------------- 13-24s: the takeover ----------------
DISTROS = [('Slackware', 1993.5), ('Debian', 1993.6), ('Red Hat', 1994.8), ('SUSE', 1994.3), ('Mandrake', 1998.5),
           ('Knoppix', 2000.5), ('Gentoo', 2002.2), ('Arch', 2002.2), ('RHEL', 2002.3), ('Fedora', 2003.9),
           ('NixOS', 2003.5), ('CentOS', 2004.4), ('Ubuntu', 2004.8), ('openSUSE', 2005.8), ('Alpine', 2005.6),
           ('Mint', 2006.6), ('Android', 2008.8), ('Tails', 2009.5), ('Manjaro', 2011.5), ('elementary', 2011.3),
           ('ChromeOS', 2011.4), ('Raspbian', 2012.5), ('Kali', 2013.2), ('SteamOS', 2013.9), ('Pop!_OS', 2017.8),
           ('EndeavourOS', 2019.5), ('Rocky', 2021.45), ('AlmaLinux', 2021.2)]
PAL = [CYAN, MAG, YEL, GREEN, ORANGE, (157, 107, 255), (90, 180, 255), (255, 90, 120), (120, 220, 160)]
rnd = random.Random(4)
_order = list(range(len(DISTROS)))
rnd.shuffle(_order)
WALL = []                      # flow layout: pack names into centered rows, no overlaps
_rows, _row, _rw = [], [], 0
for i in _order:
    name, yr = DISTROS[i]
    size = rnd.choice([32, 36, 40, 46])
    w = len(name) * size * 0.602
    if _row and _rw + 30 + w > 980:
        _rows.append((_row, _rw)); _row, _rw = [], 0
    _rw += (30 if _row else 0) + w
    _row.append((name, yr, PAL[i % len(PAL)], size, w))
_rows.append((_row, _rw))
for r, (row, rw) in enumerate(_rows):
    x = (W - rw) / 2
    for name, yr, col, size, w in row:
        WALL.append((name, yr, col, size, x, 680 + r * 58 + (46 - size) * 0.6))
        x += w + 30

CARDS = [('runs most of the cloud', 2006.65, CYAN), ('powers billions of phones', 2008.8, GREEN),
         ('100% of top 500 supercomputers', 2017.85, YEL), ('flew a helicopter on Mars', 2021.3, ORANGE)]
TS0, TS1 = 13.0, 23.2


def year_of(t):
    return 1991.6 + (2026.4 - 1991.6) * min(1, max(0, (t - TS0) / (TS1 - TS0)))


def t_of_year(y):
    # invert the eased mapping numerically
    lo, hi = TS0, TS1
    for _ in range(30):
        m = (lo + hi) / 2
        if year_of(m) < y: lo = m
        else: hi = m
    return lo


def takeover(t, d, n):
    yr = year_of(t)
    d.text((70, 170), '$ linux --since 1991', font=F(40, False), fill=DIM)
    f = F(250)
    n.text((60, 230), str(int(yr)), font=f, fill=YEL)
    kv = '0.01'
    for ky, v in V.KERNEL:
        if yr >= ky: kv = v
    loc = max(10239, int(V.loc_at(yr) * 1e6))
    d.text((680, 280), 'kernel', font=F(34, False), fill=DIM)
    d.text((680, 320), f'v{kv}', font=F(52), fill=TEXT)
    d.text((680, 400), 'lines', font=F(34, False), fill=DIM)
    d.text((680, 440), f'{loc / 1e6:.1f}M' if loc >= 1e6 else f'{loc:,}', font=F(52), fill=TEXT)
    # distro wall
    cnt = 0
    for name, y0, col, size, x, y in WALL:
        if yr >= y0:
            cnt += 1
            age = t - t_of_year(y0)
            a = ease(age / 0.25)
            pop = 1 + 0.6 * math.exp(-age * 12)
            fs = F(int(size * pop))
            n.text((x, y - (pop - 1) * size * 0.5), name, font=fs, fill=scale(col, a * 0.9))
    d.text((70, 610), f'distros: {cnt}', font=F(38, False), fill=DIM)
    # cards
    for i, (txt, y0, col) in enumerate(CARDS):
        if yr >= y0:
            age = t - t_of_year(y0)
            a = ease(age / 0.2)
            x = 60 - (1 - a) * 400
            yy = 1120 + i * 90
            d.rounded_rectangle((x, yy, x + 960, yy + 78), 18, fill=(22, 15, 40), outline=scale(col, a), width=4)
            n.text((x + 30, yy + 17), '▸ ' + txt, font=F(42), fill=scale(col, a))


# ---------------- 24-30s end card ----------------
def endcard(t, d, n, base):
    a = ease((t - 24) / 0.4)
    ctext(d, 170, 'Created by sujee.dev', F(34, False), scale(DIM, a))   # credit (see brief.md)
    ctext(d, 260, 'the full story', F(56, False), scale(TEXT, a))
    f = F(104)
    w = n.textlength('LINUX', font=f)
    n.text(((W - w) / 2, 340), 'LINUX', font=f, fill=scale(YEL, a))
    w = n.textlength('TURNS 35', font=f)
    n.text(((W - w) / 2, 460), 'TURNS 35', font=f, fill=scale(YEL, a))
    ctext(d, 600, 'in 2 minutes', F(56, False), scale(TEXT, a))
    # thumbnail card
    tw, th = 960, 540
    k = ease((t - 24.3) / 0.5)
    if k > 0:
        im = thumb().resize((tw * S, th * S), Image.LANCZOS)
        y = int(720 + (1 - k) * 80)
        base.paste(Image.blend(Image.new('RGB', (tw * S, th * S), BG), im, k), (60 * S, y * S))
        n.rounded_rectangle((52, y - 8, 60 + tw + 8, y + th + 8), 16, outline=scale(CYAN, k), width=5)
        # play button
        cx, cy = 60 + tw / 2, y + th / 2
        n.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=scale((200, 30, 60), k))
        d.polygon([(cx - 22, cy - 35), (cx - 22, cy + 35), (cx + 38, cy)], fill=scale((255, 255, 255), k))
    if t >= 25.0:
        b = ease((t - 25.0) / 0.3)
        p = 0.75 + 0.25 * math.sin(t * 6)
        ctext(n, 1310, '▶ WATCH THE FULL VIDEO', F(64), scale(YEL, b * p))
        bob = 14 * math.sin(t * 5)
        ctext(d, 1410, 'tap the link below', F(46, False), scale(TEXT, b))
        cx = W / 2
        yb = 1490 + bob
        n.polygon([(cx - 40, yb), (cx + 40, yb), (cx, yb + 50)], fill=scale(CYAN, b))


def render(t):
    base, neon = background(t)
    d, n = V.SD(base), V.SD(neon)
    if t < 3.0:
        hook(t, d, n)
        if t > 2.7:  # fade out
            k = (t - 2.7) / 0.3
            base = Image.blend(base, Image.new('RGB', (RW, RH), BG), k); neon = Image.blend(neon, Image.new('RGB', (RW, RH)), k)
    elif t < 9.5:
        post(t, d, n, ease((t - 3.0) / 0.3))
    elif t < 12.0:
        post(t, d, n, max(0.12, 1 - ease((t - 9.5) / 0.4) * 0.88))
        zoom_quote(t, d, n)
        if t >= 11.7:  # blackout with the silence
            k = min(1, (t - 11.7) / 0.08)
            base = Image.blend(base, Image.new('RGB', (RW, RH), (0, 0, 0)), k)
            neon = Image.blend(neon, Image.new('RGB', (RW, RH)), k)
    elif t < 13.0:
        got_big(t, d, n)
    elif t < 24.0:
        if t < 13.3:
            got_big(t, d, n)
            k = ease((t - 13.0) / 0.3)
            neon = Image.blend(neon, Image.new('RGB', (RW, RH)), k)
            n = V.SD(neon)
        takeover(t, d, n)
    else:
        if t < 24.4:
            k = 1 - ease((t - 24.0) / 0.4)
            takeover(t, d, n)
            base = Image.blend(Image.new('RGB', (RW, RH), BG), base, k)
            neon = Image.blend(Image.new('RGB', (RW, RH)), neon, k)
            d, n = V.SD(base), V.SD(neon)
        endcard(t, d, n, base)
    im = glow(base, neon)
    # drop: white flash + shake
    if 12.0 <= t < 12.6:
        k = math.exp(-(t - 12.0) * 9)
        im = Image.blend(im, Image.new('RGB', (RW, RH), (255, 255, 255)), 0.7 * k)
        dx, dy = int(26 * k * math.sin(t * 97)), int(26 * k * math.cos(t * 83))
        im = im.transform((RW, RH), Image.AFFINE, (1, 0, -dx * S, 0, 1, -dy * S), fillcolor=BG)
    if t < 0.15:
        im = Image.blend(Image.new('RGB', (RW, RH)), im, t / 0.15)
    if t > 29.3:
        im = Image.blend(im, Image.new('RGB', (RW, RH)), (t - 29.3) / 0.7)
    return im


def run_chunk(a, b, out):
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{RW}x{RH}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
                          '-crf', '16', '-g', str(FPS * 2), '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(a, b):
        p.stdin.write(render(f / FPS).tobytes())
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    if sys.argv[1] == 'still':
        for ts in sys.argv[3:]:
            render(float(ts)).save(os.path.join(sys.argv[2], f'short_{ts}.png'))
    else:
        run_chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
