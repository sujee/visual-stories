"""YouTube thumbnails for the landscape video: 4 designs, drawn at 2560x1440, saved at 1280x720.

    python src/thumbnails.py <out_dir>
"""
import os, sys
os.environ['SCALE'] = '2'
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import video as V

TW, TH = 2560, 1440
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)


def font(size):
    return ImageFont.truetype(V.FONT_BOLD, size)


def compose(base, neon, strength=1.5, radius=10):
    small = neon.resize((TW // 4, TH // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius))
    glow = small.resize((TW, TH), Image.BILINEAR)
    a = (np.asarray(base, np.float32) + np.asarray(neon, np.float32) + np.asarray(glow, np.float32) * strength)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def shade(im, alpha_fn):
    """Darken towards BG; alpha_fn(xx, yy) -> 0..1 darkness (normalized coords)."""
    yy, xx = np.mgrid[0:TH, 0:TW] / np.array([TH, TW])[:, None, None]
    a = np.clip(alpha_fn(xx, yy), 0, 1)[..., None]
    arr = np.asarray(im, np.float32) * (1 - a) + np.array(V.BG, np.float32) * a
    return Image.fromarray(arr.astype(np.uint8))


def title(n, xy, text, size, color, shadow=V.MAG):
    f = font(size)
    off = max(4, size // 40)
    n.text((xy[0] - off, xy[1] - off), text, font=f, fill=V.scale(shadow, 0.6))
    n.text(xy, text, font=f, fill=color)


def grid(n, hy=1000):
    for k in range(-24, 25):
        n.line((TW / 2 + k * 55, hy, TW / 2 + k * 360, TH), fill=(45, 12, 70), width=2)
    for k in range(1, 12):
        y = hy + (TH - hy) * (k / 12) ** 2
        n.line((0, y, TW, y), fill=(45, 12, 70), width=2)


def chip(d, xy, text, size, color):
    f = font(size)
    w = d.textlength(text, font=f)
    x, y = xy
    d.rounded_rectangle((x, y, x + w + 60, y + size + 44), 22, fill=(22, 15, 40), outline=V.scale(color, 0.8), width=4)
    d.text((x + 30, y + 18), text, font=f, fill=color)
    return x + w + 60


def save(im, name):
    im.resize((1280, 720), Image.LANCZOS).save(os.path.join(OUT, name), optimize=True)


END = V.render_main(116)                          # 3840x2160 final frame, after all pop animations

# 1 ── LINUX 1991 → 2026 over the distro tree
bg = END.crop((1980, 144, 3760, 1146)).resize((TW, TH), Image.LANCZOS)
bg = shade(bg, lambda x, y: 0.93 - np.clip((x - 0.38) / 0.3, 0, 1) * 0.85)
neon = Image.new('RGB', (TW, TH)); n = ImageDraw.Draw(neon)
title(n, (110, 300), 'LINUX', 360, V.YEL)
d = ImageDraw.Draw(bg)
d.text((120, 720), '1991 → 2026', font=font(150), fill=V.TEXT)
d.text((124, 950), '$ 35 years in 2 minutes', font=font(72), fill=(90, 200, 140))
save(compose(bg, neon), 'linux-history-thumbnail-tree-16x9.png')

# 2 ── "just a hobby" → runs the world
bg = Image.new('RGB', (TW, TH), V.BG)
neon = Image.new('RGB', (TW, TH)); n = ImageDraw.Draw(neon)
grid(n)
d = ImageDraw.Draw(bg)
d.text((160, 150), '$ linus --1991', font=font(70), fill=V.DIM)
n.text((160, 260), '"just a hobby"', font=font(170), fill=(90, 220, 150))
title(n, (160, 520), 'RUNS THE', 250, V.YEL)
title(n, (160, 780), 'WORLD', 250, V.YEL)
x = 160
for txt, col in (('100% supercomputers', V.CYAN), ('billions of phones', V.GREEN), ('Mars', V.ORANGE)):
    x = chip(d, (x, 1130), txt, 62, col) + 40
save(compose(bg, neon), 'linux-history-thumbnail-hobby-16x9.png')

# 3 ── 10K → 40M lines of code
bg = Image.new('RGB', (TW, TH), V.BG)
neon = Image.new('RGB', (TW, TH)); n = ImageDraw.Draw(neon)
d = ImageDraw.Draw(bg)
x0, x1, y0, y1 = 120, 2440, 1340, 560
for v in (10, 20, 30, 40):
    y = y0 - v / 42 * (y0 - y1)
    d.line((x0, y, x1, y), fill=(40, 30, 70), width=3)
    d.text((x0, y - 50), f'{v}M', font=font(40), fill=V.DIM)
ys = np.linspace(V.LOC_Y[0], 2026.5, 200)
pts = [(x0 + (a - 1991.7) / 34.8 * (x1 - x0), y0 - V.loc_at(a) / 42 * (y0 - y1)) for a in ys]
d.polygon(pts + [(x1, y0), (x0, y0)], fill=(48, 36, 10))
n.line(pts, fill=V.YEL, width=12, joint='curve')
for ky, ver in V.KERNEL:
    if ver in ('1.0', '2.6', '3.0', '4.0', '5.0', '6.0'):
        px, py = x0 + (ky - 1991.7) / 34.8 * (x1 - x0), y0 - V.loc_at(ky) / 42 * (y0 - y1)
        n.ellipse((px - 16, py - 16, px + 16, py + 16), fill=(255, 255, 255))
        d.text((px - 40, py - 100), 'v' + ver, font=font(48), fill=V.TEXT)
n.ellipse((pts[-1][0] - 22, pts[-1][1] - 22, pts[-1][0] + 22, pts[-1][1] + 22), fill=(255, 255, 255))
title(n, (120, 90), '10K → 40M', 270, V.YEL)
d.text((130, 400), 'lines of Linux kernel code · 1991 → 2026', font=font(68), fill=V.TEXT)
save(compose(bg, neon), 'linux-history-thumbnail-lines-16x9.png')

# 4 ── HOW LINUX TOOK OVER, tree on top, headline band below
bg = END.crop((60, 144, 3780, 1160)).resize((TW, int(TW * 1016 / 3720)), Image.LANCZOS)
canvas = Image.new('RGB', (TW, TH), V.BG)
canvas.paste(bg, (0, 40))
canvas = shade(canvas, lambda x, y: np.clip((y - 0.42) / 0.12, 0, 1) * 0.97)
neon = Image.new('RGB', (TW, TH)); n = ImageDraw.Draw(neon)
d = ImageDraw.Draw(canvas)
d.text((120, 830), 'HOW', font=font(130), fill=V.TEXT)
title(n, (120, 950), 'LINUX TOOK OVER', 250, V.YEL)
d.text((126, 1240), '1969 → 2026 · Unix → GNU → Linux → every distro', font=font(62), fill=(90, 200, 140))
save(compose(canvas, neon), 'linux-history-thumbnail-takeover-16x9.png')
print('done')

# 5 ── birthday: $ uptime → up 35 years, a giant 35 with a candle, over the distro tree
bg = END.crop((1980, 144, 3760, 1146)).resize((TW, TH), Image.LANCZOS)
bg = shade(bg, lambda x, y: 0.94 - np.clip((x - 0.45) / 0.3, 0, 1) * 0.8)
neon = Image.new('RGB', (TW, TH)); n = ImageDraw.Draw(neon)
d = ImageDraw.Draw(bg)
d.text((120, 120), '$ uptime', font=font(80), fill=(90, 200, 140))
d.text((120, 230), ' up 35 years, 1 hobby', font=font(80), fill=V.TEXT)
n.text((120, 390), 'LINUX TURNS', font=font(150), fill=V.TEXT)
title(n, (100, 540), '35', 560, V.YEL)
cx, top = 850, 760                                     # birthday candle next to the 35
d.rectangle((cx - 26, top, cx + 26, top + 330), fill=(255, 120, 170))
for k in range(6):                                     # stripes
    y = top + 20 + k * 55
    d.polygon([(cx - 26, y), (cx + 26, y - 26), (cx + 26, y - 6), (cx - 26, y + 20)], fill=(255, 235, 245))
d.line((cx, top, cx, top - 34), fill=(60, 50, 60), width=8)
n.ellipse((cx - 30, top - 140, cx + 30, top - 30), fill=(255, 190, 60))
n.ellipse((cx - 14, top - 95, cx + 14, top - 40), fill=(255, 250, 220))
d.text((124, 1180), '"just a hobby" · 1991 → 2026', font=font(76), fill=(90, 200, 140))
save(compose(bg, neon), 'linux-history-thumbnail-birthday-16x9.png')
