"""YouTube thumbnails for the Short: 3 designs at 1080x1920, built from the Short's own frames.

    python src/short_thumbnails.py <out_dir>
"""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['SCALE'] = '1'   # thumbnails are 1080x1920
import short as S

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
W, H = S.W, S.H


def overlay(frame, draw_fn, strength=1.5):
    neon = Image.new('RGB', (W, H))
    draw_fn(ImageDraw.Draw(frame), ImageDraw.Draw(neon))
    return S.glow(frame, neon, strength)


def ctext(d, y, s, size, fill, bold=True):
    f = S.F(size, bold)
    w = d.textlength(s, font=f)
    d.text(((W - w) / 2, y), s, font=f, fill=fill)


def shadow_title(n, y, s, size, col):
    f = S.F(size)
    w = n.textlength(s, font=f)
    n.text(((W - w) / 2 - 8, y - 8), s, font=f, fill=S.scale(S.MAG, 0.6))
    n.text(((W - w) / 2, y), s, font=f, fill=col)


def save(im, name):
    im.save(os.path.join(OUT, name), optimize=True)
    print(name, os.path.getsize(os.path.join(OUT, name)) // 1024, 'KB')


# 1 ── "just a hobby" → IT GOT BIG.   (matches the drop frame at ~0:12.9)
def t1(d, n):
    ctext(d, 300, '1991:', 64, S.DIM, bold=False)
    ctext(n, 380, '"just a hobby"', 96, S.TERM)
save(overlay(S.render(12.9), t1), 'linux-history-thumbnail-got-big-9x16.png')


# 2 ── the quote, struck through, on a clean background   (matches ~0:11.3 without the dimmed post)
base, neon = S.background(11.3)
d, n = ImageDraw.Draw(base), ImageDraw.Draw(neon)
ctext(d, 330, 'HE SAID THIS', 80, S.TEXT)
ctext(d, 430, 'IN 1991…', 80, S.TEXT)
S.zoom_quote(11.3, d, n)
shadow_title(n, 1150, 'IT GOT BIG.', 130, S.YEL)
save(S.glow(base, neon, 1.5), 'linux-history-thumbnail-quote-9x16.png')


# 3 ── what the hobby became: headline on top, the 2026 dashboard below   (matches ~0:23.5)
base, neon = S.background(23.5)
dash = S.render(23.5).crop((0, 150, W, 1480))
dash = dash.resize((int(W * 0.86), int(1330 * 0.86)), Image.LANCZOS)
base.paste(dash, ((W - dash.width) // 2, 440))
n = ImageDraw.Draw(neon)
ctext(n, 190, 'FROM A HOBBY', 112, S.YEL)
ctext(n, 320, 'TO ALL OF THIS', 88, S.TEXT)
save(S.glow(base, neon, 1.2), 'linux-history-thumbnail-takeover-9x16.png')


# 4 ── birthday: $ uptime → up 35 years, LINUX TURNS 35 with a candle (text kept in the middle band)
base, neon = S.background(23.5)
d, n = ImageDraw.Draw(base), ImageDraw.Draw(neon)
ctext(d, 360, '$ uptime', 64, S.TERM)
ctext(d, 450, 'up 35 years, 1 hobby', 60, S.TEXT, bold=False)
ctext(n, 610, 'LINUX TURNS', 120, S.TEXT)
f = S.F(440)
w = n.textlength('35', font=f)
x0 = (W - w) / 2 - 50                                  # shift left to make room for the candle
n.text((x0 - 10, 730 - 10), '35', font=f, fill=S.scale(S.MAG, 0.6))
n.text((x0, 730), '35', font=f, fill=S.YEL)
cx, top = x0 + w + 70, 890                             # candle
d.rectangle((cx - 22, top, cx + 22, top + 280), fill=(255, 120, 170))
for k in range(5):
    y = top + 18 + k * 54
    d.polygon([(cx - 22, y), (cx + 22, y - 22), (cx + 22, y - 4), (cx - 22, y + 18)], fill=(255, 235, 245))
d.line((cx, top, cx, top - 28), fill=(60, 50, 60), width=7)
n.ellipse((cx - 26, top - 120, cx + 26, top - 26), fill=(255, 190, 60))
n.ellipse((cx - 12, top - 82, cx + 12, top - 34), fill=(255, 250, 220))
ctext(d, 1230, '"just a hobby" · 1991 → 2026', 50, S.TERM)
save(S.glow(base, neon, 1.5), 'linux-history-thumbnail-birthday-9x16.png')
