"""Landscape video: Linux history 1969-2026, 120 s.

Layout is in 1920x1080 logical coordinates; SCALE=2 renders 3840x2160. FPS sets the frame rate.

    python src/video.py chunk <first_frame> <end_frame> <out.mp4>   # render a frame range (render.sh runs these in parallel)
    python src/video.py still <out_dir> <t> [<t> ...]               # save stills at times t (seconds), for checking frames
"""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import os
from pathlib import Path
W, H, DUR = 1920, 1080, 120.0          # logical layout space (all coordinates below)
S = int(os.environ.get('SCALE', 1))      # 2 -> 3840x2160
FPS = int(os.environ.get('FPS', 30))
RW, RH = W * S, H * S


class SD:
    """ImageDraw wrapper: takes 1080p logical coordinates, draws at S x resolution."""
    def __init__(self, im):
        self.d = ImageDraw.Draw(im)

    def _p(self, xy):
        if xy and isinstance(xy[0], (tuple, list)):
            return [(x * S, y * S) for x, y in xy]
        return [v * S for v in xy]

    def line(self, xy, fill=None, width=1, joint=None):
        self.d.line(self._p(xy), fill=fill, width=int(round(width * S)), joint=joint)

    def ellipse(self, xy, fill=None, outline=None, width=1):
        self.d.ellipse(self._p(xy), fill=fill, outline=outline, width=width * S)

    def rectangle(self, xy, fill=None, outline=None, width=1):
        self.d.rectangle(self._p(xy), fill=fill, outline=outline, width=width * S)

    def rounded_rectangle(self, xy, radius, fill=None, outline=None, width=1):
        self.d.rounded_rectangle(self._p(xy), radius * S, fill=fill, outline=outline, width=width * S)

    def polygon(self, xy, fill=None):
        self.d.polygon(self._p(xy), fill=fill)

    def point(self, xy, fill=None):
        x, y = xy
        self.d.rectangle((x * S, y * S, x * S + S - 1, y * S + S - 1), fill=fill)

    def text(self, xy, s, font=None, fill=None):
        self.d.text((xy[0] * S, xy[1] * S), s, font=font, fill=fill)

    def textlength(self, s, font=None):
        return self.d.textlength(s, font=font) / S
FONTS = Path(__file__).resolve().parents[1] / 'assets' / 'fonts'
FONT_REG = str(FONTS / 'DejaVuSansMono.ttf')
FONT_BOLD = str(FONTS / 'DejaVuSansMono-Bold.ttf')
FONT_EMOJI = str(FONTS / 'NotoEmoji-Variable.ttf')   # monochrome emoji (OFL), for the end card's 👍


def F(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size * S)


f13, f15, f18, f20, f24, f28 = F(13), F(15), F(18), F(20), F(24), F(28, True)
f18b = F(18, True)
f15b, f20b, f22b = F(15, True), F(20, True), F(22, True)
fYear = F(150, True)
fBanner = F(110, True)
fTitle = F(220, True)

BG = (10, 6, 20)
PANEL = (16, 11, 30)
BORDER = (60, 40, 100)
DIM = (120, 105, 160)
TEXT = (225, 220, 240)
CYAN, MAG, YEL = (0, 229, 255), (255, 62, 200), (255, 210, 63)
GREEN, ORANGE, PURPLE, RED = (57, 255, 136), (255, 138, 61), (157, 107, 255), (255, 70, 90)

# ---------------- timeline mapping ----------------
T0, T1 = 8.0, 112.0          # dashboard section
PRE_END = 27.5               # end of "Before Linux" (1969-1990)
ANN_T0, ANN_T1 = 27.5, 37.0  # scene change: Linus's 1991 announcement; "1991" lands on the music's drop at 30.0
DROP = 30.0
PRE_RATE = (PRE_END - T0) / 22    # seconds per year before Linux
SLOW_Y0, SLOW_Y1, SLOW_T1 = 1991.60, 1991.96, 41.5   # slow motion through autumn 1991 (0.01 and the 0.02 announcement)
ERA_RATE = (T1 - SLOW_T1) / (2026.5 - SLOW_Y1)       # seconds per year for the rest of the Linux era
PAUSE = ANN_T1 - PRE_END                             # the announcement scene; the tree's x axis skips it


def year_at(t):
    if t <= T0: return 1969.0
    if t <= PRE_END: return 1969 + (t - T0) / PRE_RATE
    if t <= ANN_T1: return 1991.0                    # the timeline holds during the announcement scene
    if t <= SLOW_T1: return SLOW_Y0 + (t - ANN_T1) / (SLOW_T1 - ANN_T1) * (SLOW_Y1 - SLOW_Y0)
    return min(2026.5, SLOW_Y1 + (t - SLOW_T1) / ERA_RATE)


def t_of(year):
    if year <= 1991: return T0 + (year - 1969) * PRE_RATE
    if year <= SLOW_Y0: return ANN_T1                # Jan-Aug 1991: skipped by the scene change
    if year <= SLOW_Y1: return ANN_T1 + (year - SLOW_Y0) / (SLOW_Y1 - SLOW_Y0) * (SLOW_T1 - ANN_T1)
    return SLOW_T1 + (year - SLOW_Y1) * ERA_RATE


X0, X1 = 100, 1660


def X(year):
    """x position on the tree: timeline time without the announcement pause, so the axis has no gap."""
    xt = t_of(year) - T0 - (PAUSE if year > 1991 else 0)
    return X0 + xt / (T1 - T0 - PAUSE) * (X1 - X0)


# ---------------- lanes ----------------
LANES = [  # name, start, parent, color, end
    ('Unix', 1969.5, None, PURPLE, None),
    ('BSD', 1977.5, 'Unix', (190, 140, 255), None),
    ('MINIX', 1987.1, 'Unix', (130, 150, 200), None),
    ('GNU', 1983.75, None, RED, None),
    ('Linux', 1991.71, None, YEL, None),
    ('Android', 2008.8, 'Linux', GREEN, None),
    ('Alpine', 2005.6, 'Linux', (90, 180, 255), None),
    ('Slackware', 1993.5, 'Linux', (120, 220, 160), None),
    ('SUSE', 1994.3, 'Slackware', (115, 255, 80), None),
    ('Debian', 1993.62, 'Linux', MAG, None),
    ('Ubuntu', 2004.8, 'Debian', ORANGE, None),
    ('Mint', 2006.6, 'Ubuntu', (140, 230, 90), None),
    ('Pop!_OS', 2017.8, 'Ubuntu', (72, 210, 220), None),
    ('Red Hat', 1994.83, 'Linux', (255, 60, 60), None),     # Oct 31, 1994: the 'Halloween' beta
    ('Fedora', 2003.9, 'Red Hat', (80, 140, 255), None),
    ('CentOS', 2004.4, 'Red Hat', (200, 120, 255), 2021.95),
    ('Rocky', 2021.45, 'CentOS', (16, 200, 140), None),
    ('Arch', 2002.2, 'Linux', CYAN, None),
    ('Gentoo', 2002.25, 'Linux', (180, 160, 255), None),
    ('ChromeOS', 2011.4, 'Gentoo', (255, 200, 90), None),
]
LANE_IDX = {l[0]: i for i, l in enumerate(LANES)}
LY0, LDY = 112, 21.6


def LY(i):
    return LY0 + i * LDY


# ---------------- events ----------------
EVENTS = [
    (1969.5, 'Unix', 'Ken Thompson & Dennis Ritchie create Unix at Bell Labs'),
    (1973.8, 'Unix', 'Unix is rewritten in C — an OS becomes portable'),
    (1977.5, 'BSD', 'Berkeley Software Distribution (BSD) appears'),
    (1983.75, 'GNU', 'Richard Stallman announces the GNU Project'),
    (1985.8, 'GNU', 'Free Software Foundation is founded'),
    (1987.1, 'MINIX', 'Andrew Tanenbaum releases MINIX for teaching'),
    (1989.1, 'GNU', 'GNU General Public License v1 is published'),
    (1991.65, 'Linux', 'Linus: "just a hobby, won\'t be big and professional"'),
    (1991.71, 'Linux', 'Linux 0.01 released — 10,239 lines of code'),
    (1991.76, 'Linux', 'Oct 5: Linux 0.02 announced publicly on comp.os.minix'),
    (1992.1, 'Linux', 'Linux adopts the GPL → GNU + Linux = a full OS'),
    (1993.5, 'Slackware', 'Slackware — today the oldest living distro'),
    (1993.62, 'Debian', 'Ian Murdock founds Debian'),
    (1994.2, 'Linux', 'Linux 1.0 — 176,250 lines of code'),
    (1994.3, 'SUSE', 'S.u.S.E. ships its Slackware-based Linux'),
    (1994.83, 'Red Hat', 'Red Hat Linux debuts with its "Halloween" beta'),
    (1996.45, 'Linux', 'Linux 2.0 — multiprocessor support; Tux is born'),
    (1998.1, 'Linux', 'The term "open source" is coined'),
    (1999.07, 'Linux', 'Linux 2.2 · KDE & GNOME bring the desktop'),
    (1999.6, 'Red Hat', 'Red Hat IPO — one of the hottest of the dot-com era'),
    (2001.0, 'Linux', 'Linux 2.4 · IBM pledges $1 billion to Linux'),
    (2002.2, 'Arch', 'Arch Linux 0.1 — keep it simple'),
    (2002.25, 'Gentoo', 'Gentoo 1.0 — compile all the things'),
    (2003.9, 'Fedora', 'Fedora Core 1 — community-driven Red Hat'),
    (2003.96, 'Linux', 'Linux 2.6 released'),
    (2004.4, 'CentOS', 'CentOS — a free rebuild of RHEL'),
    (2004.8, 'Ubuntu', 'Ubuntu 4.10 "Warty Warthog" — Linux for human beings'),
    (2005.3, 'Linux', 'Linus writes Git in about ten days'),
    (2005.6, 'Alpine', 'Alpine Linux — tiny & secure, later a container staple'),
    (2006.6, 'Mint', 'Linux Mint debuts'),
    (2006.65, 'Linux', 'Amazon EC2 launches — the cloud runs on Linux'),
    (2008.8, 'Android', 'Android 1.0 ships on the HTC Dream'),
    (2011.4, 'ChromeOS', 'First Chromebooks ship with Chrome OS'),
    (2011.55, 'Linux', 'Linux 3.0 — the kernel turns 20'),
    (2013.2, 'Linux', 'Docker launches — containers go mainstream'),
    (2014.45, 'Linux', 'Google open-sources Kubernetes'),
    (2015.3, 'Linux', 'Linux 4.0 — live kernel patching'),
    (2016.25, 'Linux', 'Microsoft announces Windows Subsystem for Linux'),
    (2017.8, 'Pop!_OS', 'System76 releases Pop!_OS'),
    (2017.85, 'Linux', 'Linux runs 100% of the TOP500 supercomputers'),
    (2019.2, 'Linux', 'Linux 5.0 released'),
    (2019.5, 'Red Hat', 'IBM closes its $34B acquisition of Red Hat'),
    (2021.3, 'Linux', 'Ingenuity flies on Mars — running Linux'),
    (2021.45, 'Rocky', 'Rocky Linux 8 — a successor to CentOS'),
    (2021.95, 'CentOS', 'CentOS Linux 8 reaches end of life'),
    (2022.15, 'Arch', 'Steam Deck ships with Arch-based SteamOS 3'),
    (2022.75, 'Linux', 'Linux 6.0 released'),
    (2022.95, 'Linux', 'Rust support lands in the kernel (6.1)'),
    (2025.05, 'Linux', 'The kernel passes 40 million lines of code'),
    (2026.2, 'Linux', '35 years on — and still "just a hobby"'),
]
# log display times: event time, but at least 1.0s apart so lines can be read
LOG_T = []
last = -9
for y, lane, msg in EVENTS:
    tt = max(t_of(y), last + 1.0)
    LOG_T.append(tt)
    last = tt

KERNEL = [(1991.71, '0.01'), (1991.76, '0.02'), (1992.2, '0.95'), (1994.2, '1.0'), (1995.2, '1.2'),
          (1996.45, '2.0'), (1999.07, '2.2'), (2001.0, '2.4'), (2003.96, '2.6'),
          (2011.55, '3.0'), (2015.3, '4.0'), (2019.2, '5.0'), (2022.75, '6.0'),
          (2024.9, '6.12')]
# approximate kernel size in millions of lines
LOC = [(1991.71, 0.0102), (1994.2, 0.176), (1996.45, 0.72), (1999.07, 1.8), (2001.0, 3.4),
       (2003.96, 5.9), (2008.0, 9.2), (2011.55, 14.6), (2015.3, 19.5), (2019.2, 26.1),
       (2022.75, 33.0), (2025.05, 40.0), (2026.5, 41.5)]
LOC_Y = np.array([p[0] for p in LOC]); LOC_V = np.array([p[1] for p in LOC])


def loc_at(y):
    if y < LOC_Y[0]: return 0.0
    return float(np.interp(y, LOC_Y, LOC_V))


def beat_pulse(t):
    on = (16 <= t < 28) or (30 <= t < 62) or (78 <= t < 110)
    if not on: return 0.0
    return math.exp(-((t * 2) % 1.0) * 6)


# ---------------- static layer ----------------
TREE_BOX = (40, 72, 1880, 572)
LOG_BOX = (40, 590, 1100, 1048)
STAT_BOX = (1120, 590, 1880, 1048)
CH = (1170, 828, 1840, 1012)   # LOC chart area


def panel(d, box, title):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, 10, fill=PANEL, outline=BORDER, width=2)
    d.text((x0 + 16, y0 + 8), title, font=f15b, fill=DIM)


def make_static():
    im = Image.new('RGB', (RW, RH), BG)
    d = SD(im)
    # window chrome
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((24 + i * 26, 22, 40 + i * 26, 38), fill=c)
    d.text((110, 19), '~/history  ▸  unix (1969) → linux (1991) → today', font=f18, fill=DIM)
    d.text((W - 360, 19), 'tty1 · 120 BPM · 1969→2026', font=f18, fill=DIM)
    panel(d, TREE_BOX, '$ git log --graph --all   # unix → linux → distros')
    panel(d, LOG_BOX, '$ dmesg --follow')
    panel(d, STAT_BOX, '$ uname -r && wc -l kernel/**')
    # year grid
    ticks = [1970, 1980, 1991, 1995, 2000, 2005, 2010, 2015, 2020, 2025]
    for yv in ticks:
        x = X(yv)
        for yy in range(100, 540, 6):
            d.point((x, yy), fill=(38, 28, 64))
        tw = d.textlength(str(yv), font=f15)
        d.text((x - tw / 2, 545), str(yv), font=f15, fill=DIM)
    # compressed-time marker
    xb = X(1991)
    d.text((X(1969), 545), '', font=f15)
    # chart axes
    cx0, cy0, cx1, cy1 = CH
    d.text((cx0, cy0 - 30), 'kernel size (lines of code)', font=f15b, fill=DIM)
    for v in (0, 10, 20, 30, 40):
        y = cy1 - v / 45 * (cy1 - cy0)
        d.line((cx0 + 40, y, cx1, y), fill=(40, 30, 70))
        d.text((cx0, y - 8), f'{v}M', font=f13, fill=DIM)
    for yv in (1991, 2000, 2010, 2020):
        x = cx0 + 40 + (yv - 1991) / 35.5 * (cx1 - cx0 - 40)
        tw = d.textlength(str(yv), font=f13)
        d.text((x - tw / 2, cy1 + 8), str(yv), font=f13, fill=DIM)
    return im


STATIC = make_static()


def bezier(p0, p1, n=16):
    (x0, y0), (x1, y1) = p0, p1
    pts = []
    for i in range(n + 1):
        s = i / n
        e = s * s * (3 - 2 * s)
        pts.append((x0 + (x1 - x0) * s, y0 + (y1 - y0) * e))
    return pts


def lane_path(i):
    name, start, parent, color, end = LANES[i]
    xs, y = X(start), LY(i)
    if parent:
        py = LY(LANE_IDX[parent])
        span = min(46, 12 + abs(py - y) * 0.25)
        return bezier((xs, py), (xs + span, y)) + [(X(end or 2026.5), y)]
    return [(xs, y), (X(end or 2026.5), y)]


PATHS = [lane_path(i) for i in range(len(LANES))]


def clip_path(pts, xmax):
    out = []
    for i, p in enumerate(pts):
        if p[0] <= xmax:
            out.append(p)
        else:
            if out:
                q = out[-1]
                f = (xmax - q[0]) / (p[0] - q[0]) if p[0] != q[0] else 0
                out.append((xmax, q[1] + (p[1] - q[1]) * f))
            break
    return out


def dashed(d, p0, p1, color, w=2, dash=6):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    n = int(L // dash)
    for k in range(0, n, 2):
        a, b = k / n, min(1, (k + 1) / n)
        d.line((x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, x0 + (x1 - x0) * b, y0 + (y1 - y0) * b), fill=color, width=w)


def scale(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def add_glow(base, neon, strength=1.3, radius=5):
    small = neon.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius))
    glow = small.resize((RW, RH), Image.BILINEAR)
    a = np.asarray(base, np.int16) + np.asarray(neon, np.int16) + (np.asarray(glow, np.float32) * strength).astype(np.int16)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ---------------- main frame ----------------
def render_main(t):
    yr = year_at(t)
    xp = X(yr)
    pulse = beat_pulse(t)
    base = STATIC.copy()
    d = SD(base)
    neon = Image.new('RGB', (RW, RH), (0, 0, 0))
    n = SD(neon)

    # dashed "inspired by" links into Linux
    li = LANE_IDX['Linux']
    for src, y0 in (('MINIX', 1991.71), ('GNU', 1992.1)):
        if yr >= y0:
            k = min(1, (t - t_of(y0)) * 2)
            p0 = (X(y0), LY(LANE_IDX[src]))
            p1 = (X(y0) + 14, LY(li))
            p1 = (p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k)
            dashed(n, p0, p1, scale(LANES[LANE_IDX[src]][3], 0.8), 2, 4)

    # lanes
    for i, (name, start, parent, color, end) in enumerate(LANES):
        if yr < start:
            continue
        pts = clip_path(PATHS[i], xp)
        if len(pts) < 2:
            continue
        w = 5 if name == 'Linux' else 3
        ended = end is not None and yr >= end
        col = scale(color, 0.45) if ended else color
        n.line(pts, fill=scale(col, 0.85), width=w, joint='curve')
        tip = pts[-1]
        if ended:
            n.ellipse((tip[0] - 5, tip[1] - 5, tip[0] + 5, tip[1] + 5), outline=col, width=2)
        else:
            r = 4 + 2 * pulse
            n.ellipse((tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r), fill=(255, 255, 255))
        # label follows the tip
        age = t - t_of(start)
        a = min(1, age * 3)
        lab_col = scale(col, a * (0.6 if ended else 1.0))
        font = f15b if name == 'Linux' else f15
        d.text((tip[0] + 12, tip[1] - 9), name, font=font, fill=lab_col)

    # event nodes
    for (ey, lane, msg) in EVENTS:
        if yr < ey:
            continue
        i = LANE_IDX[lane]
        ex, eyy = X(ey), LY(i)
        if LANES[i][2] and abs(ey - LANES[i][1]) < 1e-6:
            ex, eyy = PATHS[i][16]   # branch start: where the curve lands on its lane
        dt = t - t_of(ey)
        col = LANES[i][3]
        n.ellipse((ex - 3.5, eyy - 3.5, ex + 3.5, eyy + 3.5), fill=col)
        if dt < 1.2:
            rr = 4 + dt * 40
            k = max(0, 1 - dt / 1.2)
            n.ellipse((ex - rr, eyy - rr, ex + rr, eyy + rr), outline=scale(col, k), width=2)
            n.ellipse((ex - 6, eyy - 6, ex + 6, eyy + 6), fill=scale((255, 255, 255), k))

    # birthday flame on the Linux node, lit when Linux 0.01 is released
    if yr >= 1991.71:
        k = min(1, (t - t_of(1991.71)) * 3)
        flame(n, X(1991.71), LY(LANE_IDX['Linux']) - 6, 0.7 * k, t)

    # highlighted milestones (see HIGHLIGHTS and brief.md): a callout on the tree, connected to the node
    for hy, lane, when, what, note in HIGHLIGHTS:
        dt = t - t_of(hy)
        if 0 <= dt < CALLOUT_S:
            a = min(1, dt / 0.25) * (1 - max(0, dt - (CALLOUT_S - 0.5)) / 0.5)
            nx, ny = X(hy), LY(LANE_IDX[lane])
            bw = max(d.textlength(what, font=f20), d.textlength(note, font=f18) if note else 0) + 40
            bh = 92 + (30 if note else 0)
            hx, hyy = min(nx + 40, 1860 - bw), ny + 40
            d.rounded_rectangle((hx, hyy, hx + bw, hyy + bh), 10, fill=scale((30, 22, 10), a), outline=scale(YEL, a), width=2)
            n.text((hx + 20, hyy + 12), when, font=F(22, True), fill=scale(YEL, a))
            d.text((hx + 20, hyy + 50), what, font=f20, fill=scale(TEXT, a))
            if note:
                d.text((hx + 20, hyy + 84), note, font=f18, fill=scale(DIM, a))
            n.line((nx, ny + 4, hx, hyy + 46), fill=scale(YEL, 0.7 * a), width=2)
            n.ellipse((nx - 6, ny - 6, nx + 6, ny + 6), outline=scale(YEL, a), width=2)

    # act labels: "BEFORE LINUX" until 1991, then "THE LINUX ERA"
    act, act_col = ('BEFORE LINUX · 1969–1990', PURPLE) if t < ANN_T0 else ('THE LINUX ERA · 1991 →', YEL)
    d.text((1880 - 24 - d.textlength(act, font=f15b), 82), act, font=f15b, fill=scale(act_col, 0.9))
    if T0 <= t < 11.5:                                   # opening title card for the prelude
        a = min(1, (t - T0) / 0.5) * (1 - min(1, max(0, t - 10.8) / 0.7))
        tw = n.textlength('BEFORE LINUX', font=fBanner)
        n.text(((W - tw) / 2, 230), 'BEFORE LINUX', font=fBanner, fill=scale(PURPLE, a))
        sub = '1969 – 1990 · Unix, BSD, GNU'
        d.text(((W - d.textlength(sub, font=f28)) / 2, 350), sub, font=f28, fill=scale(TEXT, a))

    # playhead
    if T0 <= t <= T1 + 0.5:
        pc = scale(CYAN, 0.35 + 0.4 * pulse)
        n.line((xp, 96, xp, 538), fill=pc, width=2)
        n.polygon([(xp - 6, 92), (xp + 6, 92), (xp, 100)], fill=CYAN)

    # ---- dmesg log
    lx, ly0, lx1, ly1 = LOG_BOX
    shown = [(i, LOG_T[i]) for i in range(len(EVENTS)) if LOG_T[i] <= t]
    if t < T0 + 0.01:
        shown = []
    lines = shown[-13:]
    line_h = 31
    ybase = ly1 - 22 - line_h * len(lines)
    for j, (i, lt) in enumerate(lines):
        ey, lane, msg = EVENTS[i]
        age = t - lt
        newest = j == len(lines) - 1
        fade = 0.35 + 0.65 * (j + 1) / len(lines) if not newest else 1.0
        ts = f'[{ey:8.2f}] '
        tag = f'{lane.lower()}: '
        full = ts + tag + msg
        nchar = int(age * 70)
        txt = full[:nchar]
        y = ybase + j * line_h + 4
        x = lx + 20
        seg1 = txt[:len(ts)]
        seg2 = txt[len(ts):len(ts) + len(tag)]
        seg3 = txt[len(ts) + len(tag):]
        d.text((x, y), seg1, font=f18, fill=scale((90, 200, 140), fade))
        x += d.textlength(ts, font=f18)
        d.text((x, y), seg2, font=f18, fill=scale(LANES[LANE_IDX[lane]][3], fade))
        x += d.textlength(tag, font=f18)
        hl = (ey, lane) in HIGHLIGHT_KEYS
        d.text((x, y), seg3, font=f18b if hl else f18, fill=scale(YEL if hl else TEXT, fade))
        if newest:
            cx = lx + 20 + d.textlength(txt, font=f18)
            if nchar < len(full) or int(t * 2.5) % 2 == 0:
                d.rectangle((cx + 2, y + 2, cx + 12, y + 22), fill=(90, 200, 140))
    if not lines and int(t * 2.5) % 2 == 0:
        d.rectangle((lx + 20, ly1 - 50, lx + 30, ly1 - 30), fill=(90, 200, 140))

    # ---- stats panel
    sx0, sy0, sx1, sy1 = STAT_BOX
    ystr = str(int(yr))
    yc = scale(YEL if yr >= 1991.71 else PURPLE, 0.9)
    n.text((sx0 + 36, sy0 + 34), ystr, font=fYear, fill=yc)
    kv = '—'
    for ky, v in KERNEL:
        if yr >= ky: kv = v
    loc = loc_at(yr) * 1e6
    distros = sum(1 for (nm, st, par, c, en) in LANES[5:] if yr >= st and not (en and yr >= en))
    rows = [('kernel', f'v{kv}' if kv != '—' else '—'),
            ('lines', f'{int(loc):,}' if loc else '—'),
            ('distros', str(distros) if yr >= 1993 else '—'),
            ('uptime', (f'{int(yr) - 1991} yr' + ('' if int(yr) - 1991 == 1 else 's')) if yr >= 1991.71 else '—')]   # Linux's age; 35 in 2026
    for k, (a, b) in enumerate(rows):
        yy = sy0 + 58 + k * 40
        d.text((sx0 + 450, yy), a, font=f20, fill=DIM)
        birthday = a == 'uptime' and int(yr) - 1991 >= 35
        (n if birthday else d).text((sx0 + 560, yy), b, font=f22b, fill=YEL if birthday else TEXT)
        if birthday:
            candle(d, n, sx0 + 560 + d.textlength(b, font=f22b) + 18, yy + 22, 0.55, t)
    # LOC chart
    cx0, cy0, cx1, cy1 = CH
    gx0 = cx0 + 40

    def cxy(yv, v):
        return (gx0 + (yv - 1991) / 35.5 * (cx1 - gx0), cy1 - v / 45 * (cy1 - cy0))

    if yr > LOC_Y[0]:
        ys = np.linspace(LOC_Y[0], yr, 80)
        pts = [cxy(a, loc_at(a)) for a in ys]
        poly = pts + [(pts[-1][0], cy1), (pts[0][0], cy1)]
        d.polygon(poly, fill=(40, 30, 10))
        n.line(pts, fill=YEL, width=3, joint='curve')
        px, py = pts[-1]
        r = 4 + 3 * pulse
        n.ellipse((px - r, py - r, px + r, py + r), fill=(255, 255, 255))
    else:
        msg = 'waiting for a hobby project…'
        d.text((gx0 + 150, (cy0 + cy1) / 2 - 10), msg, font=f18, fill=DIM)

    # beat-reactive border flash
    if pulse > 0.05:
        n.rounded_rectangle(TREE_BOX, 10, outline=scale(MAG, 0.25 * pulse), width=2)

    return add_glow(base, neon)


# ---------------- intro / outro ----------------
def type_text(d, xy, s, t, t_start, cps, font, fill, cursor=True):
    k = int(max(0, (t - t_start) * cps))
    d.text(xy, s[:k], font=font, fill=fill)
    if cursor and k <= len(s) and t >= t_start and int(t * 3) % 2 == 0:
        x = xy[0] + d.textlength(s[:k], font=font)
        d.rectangle((x + 3, xy[1] + 4, x + 15, xy[1] + font.size / S), fill=(90, 200, 140))


def render_intro(t):
    base = Image.new('RGB', (RW, RH), BG)
    neon = Image.new('RGB', (RW, RH), (0, 0, 0))
    d, n = SD(base), SD(neon)
    # faint perspective grid
    hy = 700
    for k in range(-20, 21):
        n.line((W / 2 + k * 40, hy, W / 2 + k * 260, H), fill=(40, 10, 60), width=1)
    for k in range(1, 14):
        y = hy + (H - hy) * ((k + (t * 0.8) % 1) / 14) ** 2
        n.line((0, y, W, y), fill=(40, 10, 60), width=1)
    type_text(d, (160, 200), '$ ./linux-history', t, 0.4, 28, f28, (90, 200, 140),
              cursor=t < 2.6)
    if t > 2.6:
        a = min(1, (t - 2.6) / 0.8)
        jitter = int(6 * math.exp(-(t - 2.6) * 4) * math.sin(t * 90))
        tw = n.textlength('LINUX', font=fTitle)
        n.text(((W - tw) / 2 - 6 - jitter, 324), 'LINUX', font=fTitle, fill=scale(MAG, a * 0.6))
        n.text(((W - tw) / 2 + jitter, 330), 'LINUX', font=fTitle, fill=scale(YEL, a))
    if t > 3.8:
        a = min(1, (t - 3.8) / 0.8)
        s = 'from its Unix roots to its 35th birthday · in 2 minutes'
        tw = d.textlength(s, font=f28)
        d.text(((W - tw) / 2, 600), s, font=f28, fill=scale(TEXT, a))
    return add_glow(base, neon, 1.6, 6)


def flame(n, x, y, size, t):
    """A small flickering candle flame centered at (x, y), drawn on the glow layer."""
    if size <= 0:
        return
    f = size * (1 + 0.12 * math.sin(t * 23) + 0.06 * math.sin(t * 41))
    n.ellipse((x - 6 * size, y - 16 * f, x + 6 * size, y + 2), fill=(255, 170, 50))
    n.ellipse((x - 3 * size, y - 10 * f, x + 3 * size, y), fill=(255, 245, 210))


def candle(d, n, x, y, size, t):
    """A striped birthday candle standing on (x, y), its flame on top."""
    w, h = 9 * size, 46 * size
    d.rectangle((x - w, y - h, x + w, y), fill=(255, 120, 170))
    for k in range(4):
        yy = y - h + 6 * size + k * 11 * size
        d.polygon([(x - w, yy + 4 * size), (x + w, yy - 4 * size), (x + w, yy), (x - w, yy + 8 * size)], fill=(255, 235, 245))
    d.line((x, y - h, x, y - h - 6 * size), fill=(70, 60, 70), width=2)
    flame(n, x, y - h - 6 * size, 1.6 * size, t)


OUTRO = [
    (112.6, 'TODAY LINUX RUNS', YEL, f28),
    (113.1, '▸ 100% of the world\'s top 500 supercomputers', TEXT, f24),
    (113.5, '▸ billions of Android phones', TEXT, f24),
    (113.9, '▸ most of the public cloud', TEXT, f24),
    (114.3, '▸ a helicopter on Mars', TEXT, f24),
]
QUOTE_T, BIRTHDAY_T, CARD_T, FADE_T = 114.9, 116.5, 117.3, 119.4
EMOJI = ImageFont.truetype(FONT_EMOJI, 26 * S)
EMOJI.set_variation_by_name('Bold')


def render_outro(t, main_last):
    k = min(1, (t - T1) / 0.8)
    im = Image.blend(main_last, Image.new('RGB', (RW, RH), BG), 0.9 * k)
    neon = Image.new('RGB', (RW, RH), (0, 0, 0))
    d, n = SD(im), SD(neon)
    for i, (ts, s, col, font) in enumerate(OUTRO):
        if t >= ts:
            a = min(1, (t - ts) / 0.4)
            d.text((560, 210 + i * 56 - (1 - a) * 12), s, font=font, fill=scale(col, a))
    if t >= QUOTE_T:
        type_text(d, (560, 520), '"just a hobby, won\'t be big and professional"', t, QUOTE_T, 45, f24,
                  (90, 200, 140), cursor=t < BIRTHDAY_T)
    if t >= QUOTE_T + 1.1:
        a = min(1, (t - QUOTE_T - 1.1) / 0.5)
        d.text((560, 565), '— Linus Torvalds, 1991', font=f20, fill=scale(DIM, a))
    if t >= BIRTHDAY_T:                                  # happy 35th birthday, with a candle
        a = min(1, (t - BIRTHDAY_T) / 0.4)
        n.text((560, 650 + (1 - a) * 14), "Happy 35th birthday, Linux.", font=F(46, True), fill=scale(YEL, a))
        candle(d, n, 560 + n.textlength("Happy 35th birthday, Linux.", font=F(46, True)) + 34, 702, a, t)
    if t >= BIRTHDAY_T + 0.5:
        a = min(1, (t - BIRTHDAY_T - 0.5) / 0.4)
        d.text((562, 722 + (1 - a) * 10), "…and many, many more.", font=f28, fill=scale(TEXT, a))
    if t >= CARD_T:                                      # end card: credit + like prompt (see brief.md, Credit)
        a = min(1, (t - CARD_T) / 0.5)
        d.text((560, 820), 'Created by sujee.dev', font=f20, fill=scale(TEXT, 0.8 * a))
        x = 560
        d.text((x, 856), '$ sudo like ', font=f20, fill=scale((90, 200, 140), a))
        x += d.textlength('$ sudo like ', font=f20)
        n.text((x, 852), '👍', font=EMOJI, fill=scale((90, 220, 150), a))
        x += n.textlength('👍', font=EMOJI) + 18
        d.text((x, 856), '# no password required', font=f20, fill=scale(DIM, a))
    im = add_glow(im, neon, 1.3)
    if t > FADE_T:
        im = Image.blend(im, Image.new('RGB', (RW, RH), (0, 0, 0)), min(1, (t - FADE_T) / (DUR - FADE_T)))
    return im


# Highlighted milestones: a callout on the tree and a bold log line. Exact text is in brief.md (Must communicate).
# (year, lane, date, text, optional note); the year must match the event in EVENTS.
HIGHLIGHTS = [
    (1991.76, 'Linux', 'OCT 5, 1991', 'Linux 0.02 is announced publicly', None),
    (1994.83, 'Red Hat', 'OCT 1994', 'Red Hat Linux debuts with its "Halloween" beta', None),   # 1.0 followed in May 1995
    (1999.6, 'Red Hat', 'AUG 1999', 'Red Hat IPO: one of the biggest first-day gains of the dot-com era', None),
    (2004.8, 'Ubuntu', 'OCT 2004', 'Ubuntu 4.10: "Linux for human beings"', None),
    (2005.3, 'Linux', 'APR 2005', 'Linus writes Git in about 10 days', None),
    (2006.65, 'Linux', 'AUG 2006', 'Amazon EC2 launches: the cloud runs on Linux', None),
    (2008.8, 'Android', 'SEP 2008', 'Android 1.0 ships: Linux heads for billions of phones', None),
    (2013.2, 'Linux', 'MAR 2013', 'Docker launches: containers go mainstream',
     'built on Linux kernel features: cgroups and namespaces'),
]
HIGHLIGHT_KEYS = {(y, lane) for y, lane, *_ in HIGHLIGHTS}
CALLOUT_S = 2.6   # seconds on screen; Ubuntu and Git are 6 months apart, on different lanes


# ---------------- scene change: Linus's announcement, 25 Aug 1991 ----------------
POST_HEADER = [('From: ', 'torvalds@klaava.Helsinki.FI (Linus Benedict Torvalds)'),
               ('Newsgroups: ', 'comp.os.minix'),
               ('Subject: ', 'What would you like to see most in minix?'),
               ('Date: ', '25 Aug 91 20:57:08 GMT')]
POST_BODY = [[('Hello everybody out there using minix -', False)],
             [],
             [("I'm doing a (free) operating system (", False), ('just a hobby,', True)],
             [("won't be big and professional", True), (' like gnu) for 386(486)', False)],
             [('AT clones.', False)]]


def render_announcement(t):
    base = Image.new('RGB', (RW, RH), BG)
    neon = Image.new('RGB', (RW, RH), (0, 0, 0))
    d, n = SD(base), SD(neon)
    hy = 760                                             # faint grid, as in the intro
    for k in range(-20, 21):
        n.line((W / 2 + k * 40, hy, W / 2 + k * 260, H), fill=(40, 10, 60), width=1)
    for k in range(1, 12):
        y = hy + (H - hy) * ((k + (t * 0.8) % 1) / 12) ** 2
        n.line((0, y, W, y), fill=(40, 10, 60), width=1)
    # lead-in, typed large before the drop; on the drop the date moves to the top-left corner and stays
    lead = [('# meanwhile, in Helsinki…', DIM, ANN_T0 + 0.4), ('$ date', (90, 200, 140), ANN_T0 + 1.3),
            ('Sun Aug 25 20:57:08 GMT 1991', TEXT, ANN_T0 + 1.75)]
    if t < DROP + 0.3:
        fade = 1 - min(1, max(0, t - DROP) / 0.3)
        big = F(40, True)
        for i, (s, col, ts) in enumerate(lead):
            if t >= ts:
                shown = s if i == 2 else s[:int((t - ts) * 28)]
                d.text((160, 330 + i * 70), shown, font=big, fill=scale(col, fade))
    if t < DROP:
        return add_glow(base, neon)
    a = min(1, (t - DROP) / 0.3)
    d.text((100, 52), '$ date', font=f20, fill=scale((90, 200, 140), a))
    d.text((100, 80), 'Sun Aug 25 20:57:08 GMT 1991', font=f20, fill=scale(TEXT, a))
    # scene title, then "1991" lands on the drop, with a short glitch
    a = min(1, (t - DROP) / 0.15)
    n.text((100, 150), 'JUST A HOBBY PROJECT', font=F(44, True), fill=scale(PURPLE, a))
    j = int(8 * math.exp(-(t - 30.0) * 6) * math.sin(t * 90))
    n.text((90 - 6 - j, 230 - 6), '1991', font=fTitle, fill=scale(MAG, 0.6 * a))
    n.text((90 + j, 230), '1991', font=fTitle, fill=scale(YEL, a))
    if t > 30.4:
        b = min(1, (t - 30.4) / 0.4)
        d.text((100, 520), 'A 21-year-old student', font=f28, fill=scale(TEXT, b))
        d.text((100, 562), 'in Helsinki posts this.', font=f28, fill=scale(TEXT, b))
    # the post, in a terminal window
    x0, y0, x1, y1 = 690, 150, 1840, 900
    d.rounded_rectangle((x0, y0, x1, y1), 14, fill=(18, 13, 34), outline=(70, 50, 120), width=2)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((x0 + 22 + i * 26, y0 + 18, x0 + 38 + i * 26, y0 + 34), fill=c)
    d.text((x0 + 110, y0 + 14), 'comp.os.minix — Usenet', font=f20, fill=DIM)
    fh = F(24)
    left = int(max(0, t - 30.3) * 160)                   # header types fast
    y = y0 + 70
    for key, val in POST_HEADER:
        sub = (key + val)[:left]
        left -= len(key) + len(val)
        d.text((x0 + 36, y), sub[:len(key)], font=F(24, True), fill=CYAN)
        d.text((x0 + 36 + d.textlength(key, font=F(24, True)), y), sub[len(key):], font=fh, fill=scale(TEXT, 0.85))
        y += 40
        if left <= 0:
            break
    left = int(max(0, t - 31.2) * 52)                    # body types at a readable pace
    fb, fbh = F(30), F(30, True)
    y, last = y0 + 300, None
    for line in POST_BODY:
        x = x0 + 36
        for text, hl in line:
            if left <= 0:
                break
            sub = text[:left]
            left -= len(text)
            (n if hl else d).text((x, y), sub, font=fbh if hl else fb, fill=YEL if hl else TEXT)
            x += d.textlength(sub, font=fbh if hl else fb)
            last = (x, y)
        y += 54
    if last and int(t * 3) % 2 == 0:
        d.rectangle((last[0] + 4, last[1] + 4, last[0] + 18, last[1] + 32), fill=(90, 200, 140))
    return add_glow(base, neon)


MAIN_END = None


def render(t):
    global MAIN_END
    if t < 7.0:
        im = render_intro(t)
        if t < 0.3:
            im = Image.blend(Image.new('RGB', (RW, RH), (0, 0, 0)), im, t / 0.3)
        return im
    if t < 8.0:
        return Image.blend(render_intro(t), render_main(8.0), (t - 7.0))
    if ANN_T0 <= t < ANN_T1:                             # scene change: the 1991 announcement
        im = render_announcement(t)
        if t < ANN_T0 + 0.4:
            im = Image.blend(render_main(ANN_T0 - 0.01), im, (t - ANN_T0) / 0.4)
        if t > ANN_T1 - 0.5:
            im = Image.blend(im, render_main(ANN_T1), (t - (ANN_T1 - 0.5)) / 0.5)
        return im
    if t <= T1:
        return render_main(t)
    if MAIN_END is None:
        MAIN_END = render_main(T1 + 4)
    return render_outro(t, MAIN_END)


def run_chunk(a, b, out):
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{RW}x{RH}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-g', str(FPS * 2),
                          '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for f in range(a, b):
        p.stdin.write(render(f / FPS).tobytes())
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    if sys.argv[1] == 'still':
        for ts in sys.argv[3:]:
            render(float(ts)).save(os.path.join(sys.argv[2], f'landscape_{ts}.png'))
    else:
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        run_chunk(a, b, out)
