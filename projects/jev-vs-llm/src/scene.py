"""Jev: TypeSafe AI's System One model - typed decisions with calibrated probabilities.

Normally rendered through ../render.sh. To run Manim directly, from the story directory:
  JEV_ORIENT=landscape uv run manim -qk --frame_rate 30 src/scene.py JevExplainer
  JEV_ORIENT=portrait  uv run manim -qk --frame_rate 30 src/scene.py JevExplainer
Timeline events (for music sync) are written to workspace/tmp/events_<orient>.json.

The core idea, drawn as one visual motif: an LLM's possible outputs are *every string*, built one
model pass per token; Jev's possible outputs are the options you define (drawn as buckets), filled
with probability in one pass. Everything else (speed, typed shapes, thresholds, calibration, the
trade-off) follows from that.

Each beat builds its layout first, then `stage()` scales it to fill the safe area of the current
format, then it animates. Every probability and count on screen is illustrative; the only real
figures are TypeSafe AI's published claims in `b_speed` (see brief.md for the source).
"""
import json
import os
import re
from pathlib import Path

import manimpango
import numpy as np
from manim import *

# Bundled monospace font, registered for this process only (licence next to the .ttf files).
FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
for _f in ("JetBrainsMono-Regular.ttf", "JetBrainsMono-Bold.ttf"):
    if not manimpango.register_font(str(FONT_DIR / _f)):
        raise RuntimeError(f"could not register font {_f} from {FONT_DIR}")

ORIENT = os.environ.get("JEV_ORIENT", "landscape")
PORTRAIT = ORIENT == "portrait"
SHORT = PORTRAIT   # the vertical deliverable is a standalone ~35 s cut of the core idea (see brief.md)
SPEED = float(os.environ.get("JEV_SPEED", "0.8" if SHORT else "1.0"))

if PORTRAIT:
    q = config.pixel_height
    config.pixel_width = q
    config.pixel_height = int(round(q * 16 / 9 / 2)) * 2
    config.frame_height = 16.0
    config.frame_width = 9.0

# Content area per format: (center, width, height), plus where the kicker and captions go.
# Portrait stays clear of the Shorts UI (roughly the bottom 15% and the right edge).
if PORTRAIT:
    STAGE = (np.array([-0.2, 2.0, 0]), 7.8, 9.6)
    KICKER_POS = np.array([-0.2, 7.25, 0])
    CAPTION_TOP, CAPTION_CHARS, CAPTION_SIZE = -3.45, 24, 38
else:
    STAGE = (np.array([0, 0.3, 0]), 13.0, 5.5)
    KICKER_POS = np.array([-6.6, 3.55, 0])
    CAPTION_TOP, CAPTION_CHARS, CAPTION_SIZE = -2.85, 72, 28

# ---------------------------------------------------------------- palette
BG = "#0C0F14"
PANEL = "#151B24"
PANEL_EDGE = "#263041"
TEXT = "#E7EBF1"
MUTED = "#8C96A8"
LLM_C = "#F2B45A"     # the LLM: amber
JEV_C = "#5EEAD4"     # Jev: mint
ERR = "#FF6B6B"
OK = "#4ADE80"
HUMAN = "#B69CFA"
FONT = "Inter"
MONO = "JetBrains Mono"

config.background_color = BG

# ---------------------------------------------------------------- content (illustrative values)
TICKET = ["I was charged twice", "for order #4417.", "Please fix this!"]
OPTIONS = ["refund", "billing", "shipping", "other"]
JEV_PROBS = [0.94, 0.04, 0.01, 0.01]
LLM_TOKENS = ["Sure!", "Based", "on", "the", "message,", "the", "customer", "wants", "a", "refund.",
              "Here", "is", "the", "JSON:", '{"intent":', '"refund_request"}']
# The space of strings an LLM could return for the same question.
CLOUD = ["refund", "Refund", "REFUND", "refund_request", '"refund"', "refunds", "re-fund", "a refund",
         "Refund.", "billing?", "Billing", "billing_issue", "payment", "double charge", "chargeback",
         "Sure! The intent is", "As an AI model", "I can't be sure", "{intent: refund}", '{"intent": "refund"}',
         "intent=refund", "probably refund", "refund or billing", "Category: Refund", "N/A", "unknown",
         "shipping", "other", "OTHER", "misc", "Based on the", "It seems the", "refund (billing)",
         "duplicate payment", "[refund]", "Refund request", "customer wants money back", "¯\\_(ツ)_/¯"]
SCORE_PROBS = [0.02, 0.05, 0.18, 0.55, 0.20]
ROUTED = [  # (ticket, probabilities over OPTIONS) for the threshold beat
    ("Charged twice for #4417", [0.94, 0.04, 0.01, 0.01]),
    ("Where is my package?", [0.01, 0.02, 0.96, 0.01]),
    ("My bank and your app disagree", [0.30, 0.58, 0.02, 0.10]),
    ("Please update my card", [0.02, 0.93, 0.01, 0.04]),
]
THRESHOLD = 0.90
SECTIONS = [  # (title, subtitle, beat methods) - each gets a numbered title card
    ("System 1 decisions", "the quick calls inside software", ["b_decisions"]),
    ("Jev vs. LLM", "a string vs. a typed answer", ["b_llm", "b_jev"]),
    ("Typed answers", "pick one · score · yes/no", ["b_shapes"]),
    ("Why it's fast", "one pass, not one per token", ["b_speed"]),
    ("Acting on probabilities", "thresholds and calibration", ["b_threshold", "b_calibration"]),
    ("Jev + LLMs", "the trade-off, and working together", ["b_tradeoff", "b_team"]),
]
REPLY_TOKENS = ["Hi!", "Sorry", "about", "the", "double", "charge.", "We've", "refunded", "order",
                "#4417,", "so", "you'll", "see", "it", "in", "3-5", "days."]


def T(x):
    return x * SPEED


def crisp(cls, s, size, **kw):
    """Text/MarkupText rendered at up to 4x and scaled back down: small font sizes get uneven letter
    spacing in Manim. Pango wraps lines wider than its layout box (the frame's pixel width for Text),
    so that box is widened while the text is built; if a render still wrapped, fall back to 2x, then 1x."""
    lines = s.count("\n") + 1
    pw = config.pixel_width
    config.pixel_width = 16000   # Text's Pango layout box; wide enough that 4x never wraps, at any quality
    try:
        for k in (4, 2, 1):
            t = cls(s, font_size=size * k, **kw)
            ref = cls("Hg", font_size=size * k, font=kw.get("font", FONT))
            if t.height <= ref.height * (1.25 * lines + 0.35):
                break
    finally:
        config.pixel_width = pw
    return t.scale(1 / k)


def txt(s, size=28, color=TEXT, weight=NORMAL, font=FONT):
    return crisp(Text, s, size, font=font, color=color, weight=weight)


def mono(s, size=22, color=TEXT, weight=NORMAL):
    return txt(s, size, color, weight, MONO)


HL = {"*": JEV_C, "~": ERR, "^": LLM_C}


def markup(s, width_chars, size, color=TEXT):
    """Wrap text and color *mint*, ~red~, ^amber^ spans (semibold).

    Built as one Text per line via crisp(), so Pango never re-wraps a caption line on its own."""
    plain, spans, cur = "", [], None   # spans: (start, end, color) in `plain`
    for ch in s:
        if ch in HL:
            if cur is None:
                cur = (len(plain), HL[ch])
            else:
                spans.append((cur[0], len(plain), cur[1]))
                cur = None
        else:
            plain += ch
    lines, start, end = [], None, None   # greedy word wrap, keeping character offsets
    for m in re.finditer(r"\S+", plain):
        if start is not None and m.end() - start > width_chars:
            lines.append((start, end))
            start = None
        if start is None:
            start = m.start()
        end = m.end()
    lines.append((start, end))
    out = VGroup()
    for i, (a, b) in enumerate(lines):
        t2c, t2w = {}, {}
        for sa, sb, col in spans:
            lo, hi = max(sa, a), min(sb, b)
            if lo < hi:
                t2c[f"[{lo - a}:{hi - a}]"] = col
                t2w[f"[{lo - a}:{hi - a}]"] = SEMIBOLD
        t = crisp(Text, plain[a:b], size, font=FONT, color=color, t2c=t2c, t2w=t2w)
        # fixed pitch, top-aligned: nearly every line has a capital or ascender, so tops line up
        out.add(t.move_to([0, -i * size * 0.0155, 0], aligned_edge=UL))
    return out


def fit(m, w=None, h=None):
    """Scale a mobject down (never up) to fit a width and/or height."""
    k = 1.0
    if w and m.width > w:
        k = min(k, w / m.width)
    if h and m.height > h:
        k = min(k, h / m.height)
    if k < 1:
        m.scale(k)
    return m


def stage(m, max_up=1.8, h_frac=1.0):
    """Scale a beat's layout to fill the content area (up to max_up) and center it there."""
    c, w, h = STAGE
    k = min(w / m.width, h * h_frac / m.height, max_up)
    return m.scale(k).move_to(c)


def panel(w, h, edge=PANEL_EDGE, r=0.2):
    return RoundedRectangle(width=w, height=h, corner_radius=r, fill_color=PANEL, fill_opacity=1,
                            stroke_color=edge, stroke_width=2)


def pill(s, color=TEXT, size=22, edge=PANEL_EDGE, font=FONT):
    t = txt(s, size, color, font=font)
    p = RoundedRectangle(width=t.width + 0.4, height=t.height + 0.26, corner_radius=(t.height + 0.26) / 2,
                         fill_color=PANEL, fill_opacity=1, stroke_color=edge, stroke_width=2)
    return VGroup(p, t.move_to(p))


def cross_mark(color=ERR, s=0.1):
    return VGroup(Line([-s, -s, 0], [s, s, 0]), Line([-s, s, 0], [s, -s, 0])).set_stroke(color, 4)


def person(color=HUMAN, k=1.0):
    head = Circle(radius=0.13, fill_color=color, fill_opacity=1, stroke_width=0).shift(UP * 0.16)
    body = Arc(radius=0.24, start_angle=0, angle=PI, fill_color=color, fill_opacity=1,
               stroke_width=0).shift(DOWN * 0.22)
    body.add_points_as_corners([body.get_end(), body.get_start()])
    return VGroup(head, body).scale(k)


def gear(color=OK, k=1.0):
    teeth = VGroup(*[Rectangle(width=0.12, height=0.62, fill_color=color, fill_opacity=1, stroke_width=0)
                     .rotate(a) for a in np.arange(0, PI, PI / 4)])
    ring = Circle(radius=0.22, fill_color=color, fill_opacity=1, stroke_width=0)
    hole = Circle(radius=0.09, fill_color=PANEL, fill_opacity=1, stroke_width=0)
    return VGroup(teeth, ring, hole).scale(k)


def ticket_card(lines=TICKET, size=18, head="support ticket"):
    body = VGroup(*[mono(s, size, TEXT) for s in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
    t = VGroup(txt(head, size - 2, MUTED), body).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    p = panel(t.width + 0.6, t.height + 0.5)
    return VGroup(p, t.move_to(p))


def mini_ticket(color=MUTED):
    """A small ticket icon: a card with three text lines."""
    p = RoundedRectangle(width=0.9, height=0.62, corner_radius=0.08, fill_color=PANEL, fill_opacity=1,
                         stroke_color=color, stroke_width=2)
    ls = VGroup(*[Line(LEFT * w / 2, RIGHT * w / 2) for w in (0.56, 0.44, 0.5)]).arrange(DOWN, buff=0.1,
                                                                                         aligned_edge=LEFT)
    ls.set_stroke(color, 3).move_to(p)
    return VGroup(p, ls)


def model_box(name, color, w=2.0, h=1.3):
    p = RoundedRectangle(width=w, height=h, corner_radius=0.22, fill_color=color, fill_opacity=0.10,
                         stroke_color=color, stroke_width=3)
    return VGroup(p, txt(name, 30, color, weight=BOLD).move_to(p))


def token_lines(tokens, max_w, size=18):
    """Wrap tokens into lines of monospace text. Each line is one Text, so every token shares the line's
    baseline; returns (lines, per-token glyph groups in order)."""
    lines, cur = [], []
    for s in tokens:
        if cur and mono(" ".join(cur + [s]), size).width > max_w:
            lines.append(cur)
            cur = []
        cur.append(s)
    lines.append(cur)
    texts, toks = VGroup(), []
    for ln in lines:
        t = mono(" ".join(ln), size)
        i = 0
        for s in ln:
            toks.append(VGroup(*t.submobjects[i:i + len(s)]))  # Text has no glyphs for spaces
            i += len(s)
        texts.add(t)
    texts.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    return texts, toks


class Bucket(VGroup):
    """One possible answer: an open container whose fill level is that answer's probability."""

    def __init__(self, label, w=0.9, h=1.4, color=JEV_C, size=16):
        walls = VMobject().set_points_as_corners([[-w / 2, h / 2, 0], [-w / 2, -h / 2, 0],
                                                  [w / 2, -h / 2, 0], [w / 2, h / 2, 0]])
        walls.set_stroke(MUTED, 3)
        lab = mono(label, size, MUTED).next_to(walls, DOWN, buff=0.14)
        fill = Rectangle(width=w * 0.8, height=0.001, fill_color=color, fill_opacity=0.85, stroke_width=0)
        fill.move_to(walls.get_bottom() + UP * (h * 0.04 + 0.0005))
        super().__init__(walls, lab, fill)
        self.walls, self.lab, self.fill, self.color = walls, lab, fill, color
        self.level = 0.0

    def to(self, p):
        """Animation: fill to probability p (0..1)."""
        self.level = p
        h = max(p * self.walls.height * 0.92, 0.001)
        return self.fill.animate.stretch_to_fit_height(h).align_to(self.walls, DOWN).shift(
            UP * self.walls.height * 0.04)


def buckets(labels, w=0.9, h=1.4, gap=0.35, color=JEV_C, size=16):
    g = VGroup(*[Bucket(l, w, h, color, size) for l in labels]).arrange(RIGHT, buff=gap, aligned_edge=UP)
    return g


# ---------------------------------------------------------------- scene
class JevExplainer(Scene):
    def mark(self, name):
        self.events[name] = round(self.renderer.time, 3)

    def caption(self, s, short=None, wait=None):
        s = short if (PORTRAIT and short) else s
        m = markup(s, CAPTION_CHARS, CAPTION_SIZE).move_to([STAGE[0][0], CAPTION_TOP, 0], aligned_edge=UP)
        floor = -config.frame_height / 2 + (2.4 if PORTRAIT else 0.2)   # portrait: above the Shorts UI
        if m.get_bottom()[1] < floor:
            m.shift(UP * (floor - m.get_bottom()[1]))
        if self.cap is not None:
            self.play(FadeOut(self.cap, shift=UP * 0.1), run_time=T(0.25))
        self.play(FadeIn(m, shift=UP * 0.1), run_time=T(0.4))
        self.cap = m
        if wait is None:
            wait = (0.3 + 0.17 * len(s.split())) if PORTRAIT else (0.4 + 0.18 * len(s.split()))
        if wait:
            self.wait(wait)

    def kicker(self, s):
        """Small section label (top-left in landscape, top-center in portrait)."""
        k = VGroup(Dot(radius=0.05, color=JEV_C), txt(s.upper(), 17, MUTED, weight=SEMIBOLD))
        k.arrange(RIGHT, buff=0.15)
        if PORTRAIT:
            k.scale(1.25).move_to(KICKER_POS)
        else:
            k.move_to(KICKER_POS, aligned_edge=LEFT)
        if self.kick is None:
            self.play(FadeIn(k, shift=RIGHT * 0.1), run_time=T(0.4))
        else:
            self.play(FadeOut(self.kick), FadeIn(k, shift=RIGHT * 0.1), run_time=T(0.4))
        self.kick = k

    def section(self, i, title, sub):
        """Section break: a numbered title card with a progress row, then the section's kicker."""
        if self.kick is not None:
            self.play(FadeOut(self.kick), run_time=T(0.3))
            self.kick = None
        self.mark(f"sec{i + 1}")
        self.events.setdefault("chapters", []).append([self.events[f"sec{i + 1}"], title])   # for src/youtube.py
        num = mono(f"{i + 1:02d}", 26, JEV_C, weight=BOLD)
        bar = Line(LEFT, RIGHT, stroke_color=JEV_C, stroke_width=4).set_width(0.6)
        name = txt(title, 60, TEXT, weight=BOLD)
        tag = txt(sub, 24, MUTED)
        dots = VGroup(*[Dot(radius=0.06, color=JEV_C if j <= i else MUTED,
                            fill_opacity=1 if j <= i else 0.35) for j in range(len(SECTIONS))])
        dots.arrange(RIGHT, buff=0.22)
        card = VGroup(VGroup(num, bar).arrange(RIGHT, buff=0.25), name, tag, dots).arrange(DOWN, buff=0.35)
        card[3].shift(DOWN * 0.25)
        fit(card, w=STAGE[1]).move_to(STAGE[0] + (UP * 0.3 if PORTRAIT else ORIGIN))
        self.play(FadeIn(num, shift=RIGHT * 0.15), GrowFromEdge(bar, LEFT), FadeIn(name, shift=UP * 0.15),
                  FadeIn(dots), run_time=T(0.45))
        self.play(FadeIn(tag, shift=UP * 0.08), dots[i].animate.scale(1.6), run_time=T(0.3))
        self.wait(0.7)   # not sped up in the Short: the card must stay readable
        self.play(FadeOut(card, shift=UP * 0.15), run_time=T(0.35))
        self.kicker(title)

    def clear_all(self, keep=(), rt=0.6):
        keep = set(keep) | {self.bg}
        if self.kick is not None:
            keep.add(self.kick)
        for m in self.mobjects:
            if m not in keep:
                m.clear_updaters()
        mobs = [m for m in self.mobjects if m not in keep]
        if mobs:
            self.play(FadeOut(Group(*mobs)), run_time=T(rt))
        self.remove(*mobs)
        self.cap = None

    def construct(self):
        self.events = {}
        self.cap = None
        self.kick = None
        # faint dot grid
        fw, fh = config.frame_width, config.frame_height
        self.bg = VGroup(*[Dot([x, y, 0], radius=0.012, color=MUTED, fill_opacity=0.18)
                           for x in np.arange(-fw / 2 + 0.25, fw / 2, 0.5)
                           for y in np.arange(-fh / 2 + 0.25, fh / 2, 0.5)])
        self.add(self.bg)
        self.mark("start")
        self.b_title()
        if SHORT:   # hook -> Jev vs. LLM -> why it matters -> pointer to the full video
            self.b_llm()
            self.b_jev()
            self.mark("outro")
        else:
            for i, (title, sub, beats) in enumerate(SECTIONS):
                self.section(i, title, sub)
                for beat in beats:
                    getattr(self, beat)()
        self.b_end()
        self.mark("end")
        out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "tmp")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, f"events_{ORIENT}.json"), "w") as f:
            json.dump(self.events, f, indent=1)

    # ------------------------------------------------------------ title
    def b_title(self):
        icon = buckets(["", "", ""], 0.5, 0.8, 0.18)
        for b, p in zip(icon, (0.9, 0.25, 0.1)):
            b.fill.stretch_to_fit_height(p * 0.8 * 0.92).align_to(b.walls, DOWN).shift(UP * 0.032)
            b.remove(b.lab)
        title = txt("Jev", 130, TEXT, weight=BOLD)
        head = VGroup(icon, title).arrange(RIGHT, buff=0.45)
        icon.align_to(title, DOWN)
        sub = txt("a “System One” model from TypeSafe AI", 30, MUTED)
        note = txt("early access · September 2026", 20, MUTED).set_opacity(0.7)
        g = VGroup(head, sub, note).arrange(DOWN, buff=0.3)
        stage(g, max_up=1.0, h_frac=0.6)
        if SHORT:   # the hook lands in the first second
            self.play(FadeIn(title, shift=UP * 0.2), LaggedStart(*[Create(b.walls) for b in icon], lag_ratio=0.2),
                      LaggedStart(*[GrowFromEdge(b.fill, DOWN) for b in icon], lag_ratio=0.15),
                      FadeIn(sub), FadeIn(note), run_time=0.6)
            self.caption("Most AI models *write*. Jev doesn't.", wait=1.6)
            self.clear_all(rt=0.4)
            return
        self.wait(0.3)
        self.play(FadeIn(title, shift=UP * 0.2), LaggedStart(*[Create(b.walls) for b in icon], lag_ratio=0.2),
                  run_time=T(0.9))
        self.play(LaggedStart(*[GrowFromEdge(b.fill, DOWN) for b in icon], lag_ratio=0.15),
                  FadeIn(sub, shift=UP * 0.1), FadeIn(note), run_time=T(0.8))
        self.caption("Most AI models *write* their answers. Jev doesn't write at all.",
                     "Most AI models *write*. Jev doesn't.")
        self.clear_all()

    # ------------------------------------------------------------ 1. decisions everywhere
    def b_decisions(self):
        diamond = Square(1.0).rotate(PI / 4).set_stroke(TEXT, 3).set_fill(PANEL, 1)
        qm = txt("?", 34, TEXT, weight=BOLD).move_to(diamond)
        dia = VGroup(diamond, qm)
        dests = VGroup(*[pill(o, TEXT, 20, font=MONO) for o in OPTIONS])
        queue = VGroup(*[mini_ticket() for _ in range(2)])
        if PORTRAIT:
            dests.arrange(RIGHT, buff=0.25)
            queue.arrange(RIGHT, buff=0.3)
            g = VGroup(queue, dia, dests).arrange(DOWN, buff=1.4)
        else:
            dests.arrange(DOWN, buff=0.35, aligned_edge=LEFT)
            queue.arrange(RIGHT, buff=0.3)
            g = VGroup(queue, dia, dests).arrange(RIGHT, buff=1.6)
        tag = VGroup(txt("System 1", 22, JEV_C, weight=BOLD), txt("fast · intuitive", 18, MUTED)).arrange(
            DOWN, buff=0.08)
        tag.next_to(dia, UP if not PORTRAIT else LEFT, buff=0.35)
        layout = VGroup(g, tag)
        stage(layout, max_up=1.5, h_frac=0.85)
        branches = VGroup(*[Line(diamond.get_right() if not PORTRAIT else diamond.get_bottom(),
                                 d.get_left() if not PORTRAIT else d.get_top(), buff=0.08)
                            for d in dests]).set_stroke(MUTED, 2.5)
        self.play(FadeIn(dia, scale=0.9), FadeIn(dests), Create(branches), run_time=T(0.8))
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in queue], lag_ratio=0.2), run_time=T(0.6))
        routes = [0, 2]
        for t, r in zip(reversed(queue), routes):
            path = VMobject().set_points_as_corners([t.get_center(), dia.get_center(), branches[r].get_end()])
            self.play(MoveAlongPath(t, path), Indicate(qm, color=JEV_C, scale_factor=1.3),
                      branches[r].animate.set_stroke(JEV_C, 4), run_time=T(0.9), rate_func=smooth)
            self.play(FadeOut(t, scale=0.5), branches[r].animate.set_stroke(MUTED, 2.5),
                      Indicate(dests[r], color=JEV_C, scale_factor=1.08), run_time=T(0.35))
        self.play(FadeIn(tag, shift=UP * 0.1), run_time=T(0.4))
        self.caption("Software is full of quick, intuitive decisions like this. "
                     "Psychologists call that *System 1* thinking.",
                     "Software is full of quick, intuitive *System 1* decisions.")
        self.clear_all()

    # ------------------------------------------------------------ 2. today: ask an LLM
    def b_llm(self):
        self.mark("groove")
        ticket = ticket_card()
        llm = model_box("LLM", LLM_C)
        passes = [txt(f"model passes: {i}", 18, MUTED) for i in range(len(LLM_TOKENS) + 1)]
        strip_w = 6.6 if PORTRAIT else 6.2
        lines, toks = token_lines(LLM_TOKENS, strip_w - 0.5, 18)
        strip = panel(strip_w, lines.height + 0.55)
        lines.move_to(strip, aligned_edge=LEFT).shift(RIGHT * 0.25)
        for i in (-2, -1):
            toks[i].set_color(LLM_C)
        llm_col = VGroup(llm, passes[0]).arrange(DOWN, buff=0.2)
        top = VGroup(ticket, llm_col).arrange(RIGHT, buff=0.7 if PORTRAIT else 0.9)
        layout = VGroup(top, VGroup(strip, lines)).arrange(DOWN, buff=0.55 if PORTRAIT else 0.5)
        stage(layout, max_up=1.4, h_frac=0.75)
        for p in passes[1:]:
            p.match_height(passes[0]).move_to(passes[0], aligned_edge=LEFT)
        loop = CurvedArrow(llm[0].get_corner(UR) + LEFT * 0.35 + UP * 0.08,
                           llm[0].get_corner(UL) + RIGHT * 0.35 + UP * 0.08, angle=PI * 0.75,
                           color=LLM_C, stroke_width=3, tip_length=0.18)
        a_in = Arrow(ticket.get_right(), llm[0].get_left(), buff=0.12, color=MUTED, stroke_width=3)
        a_out = Arrow(passes[0].get_bottom(), [llm[0].get_x(), strip.get_top()[1], 0], buff=0.08,
                      color=MUTED, stroke_width=3)

        self.play(FadeIn(ticket, shift=RIGHT * 0.1), run_time=T(0.5))
        self.play(GrowArrow(a_in), FadeIn(llm), FadeIn(passes[0]), Create(loop), run_time=T(0.7))
        self.play(GrowArrow(a_out), FadeIn(strip), run_time=T(0.4))
        self.mark("llm_start")
        cur = passes[0]
        for i, tok in enumerate(toks):
            nxt = passes[i + 1]
            self.remove(cur)
            self.add(nxt)
            cur = nxt
            self.play(FadeIn(tok), ShowPassingFlash(loop.copy().set_stroke(TEXT, 5), time_width=0.6),
                      llm[0].animate.set_fill(LLM_C, 0.28 if i % 2 == 0 else 0.12), run_time=T(0.2))
        self.play(llm[0].animate.set_fill(LLM_C, 0.10), run_time=T(0.2))
        self.caption("An LLM's answer is a string, built one token at a time: a full pass through "
                     "the model for every token.",
                     "An LLM builds a string: one model pass per token.")

        # point at the answer inside the string, then clear the stage but keep the answer, as its own pill
        src = VGroup(*toks[-1][:-1])   # '"refund_request"' without the JSON's closing brace
        hl = SurroundingRectangle(src, color=LLM_C, buff=0.06, corner_radius=0.05, stroke_width=3)
        hl_lbl = txt("its answer", 16, LLM_C, weight=BOLD).next_to(hl, DOWN, buff=0.1)
        self.play(Create(hl), FadeIn(hl_lbl, shift=UP * 0.05), run_time=T(0.5))
        self.wait(T(0.5))
        slots = VGroup(*[pill(o, TEXT, 20, font=MONO) for o in OPTIONS]).arrange(RIGHT, buff=0.25)
        expects = VGroup(txt("your code expects", 18, MUTED), slots).arrange(DOWN, buff=0.25)
        ans_pill = pill('"refund_request"', LLM_C, 22, edge=LLM_C, font=MONO)
        ans = VGroup(txt("the LLM's answer", 16, MUTED), ans_pill).arrange(DOWN, buff=0.12)
        verdict = VGroup(cross_mark(ERR), txt("doesn't fit", 18, ERR)).arrange(RIGHT, buff=0.12)
        center = VGroup(expects, ans, verdict).arrange(DOWN, buff=0.45)
        fit(center, w=STAGE[1] * 0.9).move_to(STAGE[0])
        moving = VGroup(src.copy(), hl)
        self.add(moving)
        old = [m for m in self.mobjects if m not in (self.bg, self.kick, self.cap, moving)]
        self.play(*[FadeOut(m) for m in old], FadeOut(self.cap), run_time=T(0.5))
        self.remove(*old)
        self.cap = None
        self.play(moving.animate.move_to(ans_pill), run_time=T(0.5))
        self.play(FadeTransform(moving, ans_pill), FadeIn(ans[0], shift=DOWN * 0.05), run_time=T(0.4))

        # the space of possible outputs: any string at all
        rng = np.random.default_rng(3)
        c, w, h = STAGE
        keep_out = [center]
        cloud, placed = VGroup(), []
        for s in CLOUD:
            t = mono(s, int(rng.integers(15, 23)), [TEXT, LLM_C, MUTED][int(rng.integers(0, 3))])
            t.set_opacity(float(rng.uniform(0.3, 0.6)))
            ok = False
            for _ in range(400):   # rejection-sample a spot inside the stage, clear of the middle column
                pos = c + np.array([rng.uniform(-1, 1) * (w / 2 - t.width / 2),   # and the other strings
                                    rng.uniform(-1, 1) * (h / 2 - t.height / 2), 0])
                t.move_to(pos)
                hw, hh = t.width / 2 + 0.15, t.height / 2 + 0.12
                clash = any(abs(pos[0] - m.get_x()) < hw + m.width / 2 and abs(pos[1] - m.get_y()) < hh + m.height / 2
                            for m in keep_out + placed)
                if not clash:
                    ok = True
                    break
            if ok:   # no room left: leave it out
                placed.append(t)
                cloud.add(t)
        self.cloud = cloud
        self.caption("And that string could be *anything*.", wait=0)
        self.play(LaggedStart(*[FadeIn(t, scale=0.8) for t in cloud], lag_ratio=0.03), run_time=T(1.4))
        self.wait(T(0.6))
        self.play(FadeIn(expects, shift=DOWN * 0.1), run_time=T(0.5))
        self.caption("Your code expects one of four options.")
        self.mark("llm_fail")
        self.play(ans.animate.shift(UP * 0.25), run_time=T(0.35))
        self.play(ans.animate.shift(DOWN * 0.25), ans_pill[0].animate.set_stroke(ERR), ans_pill[1].animate.set_color(ERR),
                  Wiggle(ans_pill, scale_value=1.1, rotation_angle=0.03 * TAU), FadeIn(verdict), run_time=T(0.7))
        self.caption("It invented ~\"refund_request\"~, which isn't one of them.",
                     "It invented ~\"refund_request\"~. Not an option.")
        self.clear_all(keep=[cloud])

    # ------------------------------------------------------------ 3. Jev: the answer is the type
    def b_jev(self):
        ticket = ticket_card()
        jev = model_box("Jev", JEV_C)
        pass1 = txt("model passes: 1", 18, MUTED)
        jev_col = VGroup(jev, pass1).arrange(DOWN, buff=0.2)
        bk = buckets(OPTIONS, 0.95, 1.5, 0.4)
        type_lbl = mono("intent: refund | billing | shipping | other", 15, MUTED)
        type_head = txt("you define the possible answers", 17, JEV_C)
        bgroup = VGroup(VGroup(type_head, type_lbl).arrange(DOWN, buff=0.1), bk).arrange(DOWN, buff=0.55)
        if PORTRAIT:
            top = VGroup(ticket, jev_col).arrange(RIGHT, buff=0.7)
            layout = VGroup(top, bgroup).arrange(DOWN, buff=0.9)
        else:
            layout = VGroup(ticket, jev_col, bgroup).arrange(RIGHT, buff=0.9)
        stage(layout, max_up=1.4)
        a_in = Arrow(ticket.get_right(), jev[0].get_left(), buff=0.12, color=MUTED, stroke_width=3)
        if PORTRAIT:
            a_out = Arrow(pass1.get_bottom(), type_head.get_top(), buff=0.12, color=MUTED, stroke_width=3)
        else:
            a_out = Arrow(jev[0].get_right(), [bk.get_left()[0], jev[0].get_y(), 0], buff=0.15, color=MUTED,
                          stroke_width=3)

        # the cloud of strings collapses into the buckets
        self.play(FadeIn(type_head), FadeIn(type_lbl), *[Create(b.walls) for b in bk], *[FadeIn(b.lab) for b in bk],
                  run_time=T(0.6))
        rng = np.random.default_rng(4)
        sinks = [bk[int(rng.integers(0, len(bk)))].walls.get_center() for _ in self.cloud]
        self.play(LaggedStart(*[t.animate.move_to(s).scale(0.2).set_opacity(0) for t, s in zip(self.cloud, sinks)],
                              lag_ratio=0.02), run_time=T(1.6))
        self.remove(self.cloud)
        self.caption("Jev starts from the other end: the only possible answers are the options you define.",
                     "With Jev, the only possible answers are the options you define.")

        self.play(FadeIn(ticket, shift=RIGHT * 0.1), GrowArrow(a_in), FadeIn(jev), run_time=T(0.6))
        pulse = Dot(ticket.get_center(), radius=0.12, color=JEV_C)
        self.mark("jev_hit")
        self.play(Succession(FadeIn(pulse, run_time=0.05), pulse.animate(run_time=0.4).move_to(jev.get_center()),
                             FadeOut(pulse, run_time=0.05)), run_time=T(0.5))
        vals = VGroup(*[mono(f"{p:.2f}", 16, TEXT if p == max(JEV_PROBS) else MUTED).next_to(b.walls, UP, buff=0.1)
                        for b, p in zip(bk, JEV_PROBS)])
        self.play(jev[0].animate.set_fill(JEV_C, 0.35), FadeIn(pass1), GrowArrow(a_out),
                  *[b.to(p) for b, p in zip(bk, JEV_PROBS)], run_time=T(0.7))
        self.play(jev[0].animate.set_fill(JEV_C, 0.10), FadeIn(vals), bk[0].walls.animate.set_stroke(JEV_C, 4),
                  bk[0].lab.animate.set_color(TEXT), run_time=T(0.4))
        self.caption("One pass, and out comes a probability for every option. "
                     "Nothing to parse, and nothing off the menu.",
                     "One pass: a probability for every option. Nothing to parse.")
        if SHORT:
            w = bk[0].walls
            line = DashedLine(bk.get_left() + LEFT * 0.15, bk.get_right() + RIGHT * 0.15, dash_length=0.1)
            line.set_stroke(TEXT, 2).set_y(w.get_bottom()[1] + w.height * (0.04 + 0.92 * THRESHOLD))
            act = VGroup(gear(OK, 0.45), txt("act on its own", 18, OK, weight=BOLD)).arrange(RIGHT, buff=0.15)
            act.next_to(bk, DOWN, buff=0.75)
            arrow = Arrow(bk[0].lab.get_bottom(), act.get_top(), buff=0.1, color=OK, stroke_width=3)
            self.play(Create(line), run_time=0.4)
            self.play(GrowArrow(arrow), FadeIn(act, shift=DOWN * 0.1), bk[0].walls.animate.set_stroke(OK, 4),
                      run_time=0.5)
            self.caption("So it's fast, and the confidence tells your code when to act on its own.")
        self.clear_all()

    # ------------------------------------------------------------ 4. typed shapes
    def b_shapes(self):

        def card(title, hint, bk, probs, extra=None):
            head = VGroup(txt(title, 24, TEXT, weight=BOLD), mono(hint, 14, MUTED)).arrange(DOWN, buff=0.08)
            if PORTRAIT:
                left = VGroup(head, *([extra] if extra is not None else [])).arrange(DOWN, buff=0.25)
                body = VGroup(left, bk).arrange(RIGHT, buff=0.6)
            else:
                parts = [head] + ([extra] if extra is not None else []) + [bk]
                body = VGroup(*parts).arrange(DOWN, buff=0.35)
            vals = VGroup(*[mono(f"{p:.2f}", 14, TEXT if p == max(probs) else MUTED) for p in probs])
            p = panel(max(body.width + 0.7, 6.4 if PORTRAIT else 3.6), body.height + 0.95)
            body.move_to(p).shift(DOWN * 0.1)
            return VGroup(p, body), vals

        b1 = buckets(OPTIONS, 0.55, 1.1, 0.22, size=13)
        c1, v1 = card("Pick one", "choice", b1, JEV_PROBS)
        b2 = buckets(["1", "2", "3", "4", "5"], 0.42, 1.1, 0.16, size=14)
        c2, v2 = card("Score", "ordered levels · risk", b2, SCORE_PROBS)
        b3 = buckets(["yes"], 0.7, 1.1, 0.2, size=14)
        c3, v3 = card("Yes / no", "a probability", b3, [0.96], txt("“Mentions a refund?”", 17, TEXT))
        if PORTRAIT:   # same width for all three
            for c in (c1, c2, c3):
                c[0].stretch_to_fit_width(max(x[0].width for x in (c1, c2, c3)))
        cards = VGroup(c1, c2, c3)
        for c in cards:  # equal heights
            c[0].stretch_to_fit_height(max(x[0].height for x in cards))
        cards.arrange(DOWN if PORTRAIT else RIGHT, buff=0.35)
        stage(cards, max_up=1.6)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.12) for c in cards], lag_ratio=0.25), run_time=T(0.9))
        anims = []
        for bk, probs, vals in ((b1, JEV_PROBS, v1), (b2, SCORE_PROBS, v2), (b3, [0.96], v3)):
            for b, p, v in zip(bk, probs, vals):
                v.scale_to_fit_height(b.lab.height * 0.95).next_to(b.walls, UP, buff=0.08)
                anims.append(b.to(p))
        self.play(*anims, run_time=T(0.8))
        self.play(FadeIn(VGroup(v1, v2, v3)), run_time=T(0.3))
        self.caption("Answers come in a few typed shapes: pick one, score on a scale, or yes/no. "
                     "Every one is a set of probabilities.",
                     "Pick one, score, or yes/no. Always probabilities.")
        self.clear_all()

    # ------------------------------------------------------------ 5. why it's fast, and the claims
    def b_speed(self):
        n = len(LLM_TOKENS)

        def row(name, k, color):
            lab = txt(name, 24, color, weight=BOLD)
            sq = VGroup(*[RoundedRectangle(width=0.3, height=0.3, corner_radius=0.06, fill_color=color,
                                           fill_opacity=0.0, stroke_color=color, stroke_width=2) for _ in range(k)])
            if PORTRAIT and k > 8:
                sq.arrange_in_grid(rows=2, buff=0.1)
            else:
                sq.arrange(RIGHT, buff=0.1)
            cnt = txt(f"{k} model pass" + ("es" if k > 1 else ""), 18, MUTED)
            return VGroup(lab, sq, cnt)

        r1 = row("LLM", n, LLM_C)
        r2 = row("Jev", 1, JEV_C)
        lab_w = max(r1[0].width, r2[0].width)
        for r in (r1, r2):
            r[0].move_to(ORIGIN, aligned_edge=LEFT)
            r[1].next_to(r[0], RIGHT, buff=0.4).set_x(lab_w + 0.4 + r[1].width / 2)
            r[2].next_to(r[1], RIGHT, buff=0.3)
        rows = VGroup(r1, r2).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        for r in (r1, r2):
            r[1].set_x(rows.get_left()[0] + lab_w + 0.4 + r[1].width / 2)
            r[2].next_to(r[1], RIGHT, buff=0.3)
        head = txt("What TypeSafe AI claims", 20, MUTED)
        spec = [("70–500 ms", "per response"), ("40–200×", "faster than frontier LLMs"),
                ("$0.042", "per million input tokens")]
        tiles = VGroup()
        for big, small in spec:
            b = VGroup(txt(big, 40, JEV_C, weight=BOLD), txt(small, 15, MUTED)).arrange(DOWN, buff=0.12)
            p = panel(3.4, b.height + 0.5)
            tiles.add(VGroup(p, b.move_to(p)))
        tiles.arrange(DOWN if PORTRAIT else RIGHT, buff=0.25)
        foot = txt("the company's own benchmarks · no independent evaluation yet", 14, MUTED).set_opacity(0.8)
        claims = VGroup(head, tiles, fit(foot, w=tiles.width)).arrange(DOWN, buff=0.25)
        layout = VGroup(rows, claims).arrange(DOWN, buff=0.7)
        stage(layout, max_up=1.5)

        self.play(FadeIn(r1[0]), FadeIn(r2[0]), FadeIn(r1[1]), FadeIn(r2[1]), run_time=T(0.5))
        self.play(r2[1][0].animate.set_fill(JEV_C, 0.85), FadeIn(r2[2]), run_time=T(0.25))
        self.play(LaggedStart(*[s.animate.set_fill(LLM_C, 0.85) for s in r1[1]], lag_ratio=1.0), run_time=T(2.2))
        self.play(FadeIn(r1[2]), run_time=T(0.3))
        self.caption("That's where the speed comes from: one pass instead of one per token, "
                     "and no text to generate.",
                     "One pass instead of one per token.")
        self.play(FadeIn(head), LaggedStart(*[FadeIn(t, shift=UP * 0.12) for t in tiles], lag_ratio=0.2),
                  FadeIn(foot), run_time=T(1.0))
        self.caption("These are TypeSafe's own benchmarks. "
                     "Treat them as claims until someone tests them independently.",
                     "TypeSafe's own numbers. Still claims, for now.")
        self.clear_all()

    # ------------------------------------------------------------ 6. acting on probabilities
    def b_threshold(self):
        bk = buckets(OPTIONS, 0.95, 1.6, 0.4)
        line = DashedLine(bk.get_left() + LEFT * 0.2, bk.get_right() + RIGHT * 0.2, dash_length=0.1)
        line.set_stroke(TEXT, 2).set_y(bk[0].walls.get_bottom()[1] + bk[0].walls.height * (0.04 + 0.92 * THRESHOLD))
        line_lbl = mono(f"{THRESHOLD:.2f}", 15, TEXT).next_to(line, RIGHT, buff=0.12)
        meter = VGroup(bk, line, line_lbl)

        n_auto = sum(max(p) >= THRESHOLD for _, p in ROUTED)
        pills = [pill(t, TEXT, 15, font=MONO) for t, _ in ROUTED]
        pw = max(x.width for x in pills)

        def dest(icon, label, col, n):
            head = VGroup(icon, txt(label, 20, col, weight=BOLD)).arrange(RIGHT, buff=0.2)
            p = panel(max(pw, head.width) + 0.5, 0.75 + n * 0.5 + 0.2, edge=col)
            head.move_to(p.get_top() + DOWN * 0.38)
            return VGroup(p, head)

        auto = dest(gear(OK, 0.55), "act automatically", OK, n_auto)
        human = dest(person(HUMAN, 0.6), "ask a human", HUMAN, len(ROUTED) - n_auto)
        slot = ticket_card([max((t for t, _ in ROUTED), key=len)], 17, "ticket")   # sizing: the widest ticket
        lanes = VGroup(auto, human).arrange(DOWN, buff=0.3)
        left = VGroup(slot, meter).arrange(DOWN, buff=0.7)
        layout = VGroup(left, lanes).arrange(DOWN if PORTRAIT else RIGHT, buff=0.6 if PORTRAIT else 1.0)
        # where each ticket lands, inside its lane
        filled = {"a": 0, "h": 0}
        for pl, (_, probs) in zip(pills, ROUTED):
            go = max(probs) >= THRESHOLD
            box = auto if go else human
            n = filled["a" if go else "h"]
            filled["a" if go else "h"] += 1
            pl.move_to(box[0].get_top() + DOWN * (0.85 + n * 0.5))
            if go:
                pl[0].set_stroke(OK)
            else:
                pl[0].set_stroke(HUMAN)
        stage(VGroup(layout, *pills), max_up=1.4)
        k = slot.height / ticket_card([max((t for t, _ in ROUTED), key=len)], 17, "ticket").height
        self.play(*[Create(b.walls) for b in bk], *[FadeIn(b.lab) for b in bk], Create(line), FadeIn(line_lbl),
                  FadeIn(auto), FadeIn(human), run_time=T(0.7))
        prev_vals = None
        for i, ((text, probs), pl) in enumerate(zip(ROUTED, pills)):
            card = ticket_card([text], 17, "ticket").scale(k).move_to(slot, aligned_edge=LEFT)
            self.play(FadeIn(card, shift=RIGHT * 0.15), run_time=T(0.3))
            top = int(np.argmax(probs))
            go = probs[top] >= THRESHOLD
            col = OK if go else HUMAN
            vals = VGroup(*[mono(f"{p:.2f}", 15, TEXT if j == top else MUTED).scale(k).next_to(b.walls, UP, buff=0.1)
                            for j, (b, p) in enumerate(zip(bk, probs))])
            anims = [b.to(p) for b, p in zip(bk, probs)]
            if prev_vals is not None:
                anims.append(FadeOut(prev_vals))
            self.play(*anims, FadeIn(vals), bk[top].walls.animate.set_stroke(col, 4), run_time=T(0.5))
            prev_vals = vals
            self.play(ReplacementTransform(card, pl), bk[top].walls.animate.set_stroke(MUTED, 3), run_time=T(0.5))
            if i == 0:
                self.caption("Every answer carries its confidence. Above a threshold, code acts on its own.",
                             "Above a threshold, code acts on its own.", wait=T(1.0))
            if i == 2:
                self.caption("Below it, a person takes a look.", wait=T(0.8))
        self.wait(T(0.6))
        self.clear_all()

    # ------------------------------------------------------------ 7. calibration and RLCD
    def b_calibration(self):
        side = 3.4
        ax = Axes(x_range=[0, 1, 0.5], y_range=[0, 1, 0.5], x_length=side, y_length=side, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": True})
        xl = txt("confidence", 16, MUTED).next_to(ax.x_axis, DOWN, buff=0.32)
        yl = txt("how often right", 16, MUTED).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.3)
        ticks = VGroup(*[mono(s, 13, MUTED).next_to(ax.c2p(v, 0), DOWN, buff=0.08) for v, s in ((0, "0"), (1, "1"))])
        diag = DashedLine(ax.c2p(0, 0), ax.c2p(1, 1), color=MUTED, dash_length=0.08, stroke_width=2)
        pts = [(0.15, 0.17), (0.3, 0.27), (0.45, 0.47), (0.6, 0.58), (0.75, 0.77), (0.9, 0.89), (0.98, 0.97)]
        dots = VGroup(*[Dot(ax.c2p(x, y), radius=0.06, color=JEV_C) for x, y in pts])
        hi = Circle(radius=0.16, color=JEV_C, stroke_width=3).move_to(dots[5])
        hi_lbl = VGroup(txt("90% sure →", 15, TEXT), txt("right ~90% of the time", 15, TEXT)).arrange(
            DOWN, aligned_edge=RIGHT, buff=0.08)
        hi_lbl.move_to(ax.c2p(1.0, 0.2), aligned_edge=RIGHT)
        hi_line = Line(hi_lbl.get_top() + UP * 0.06 + RIGHT * (hi.get_x() - hi_lbl.get_right()[0] + 0.2),
                       hi.get_bottom(), stroke_color=JEV_C, stroke_width=2)
        illus = txt("illustrative", 13, MUTED).set_opacity(0.6).next_to(ax, UP, buff=0.1).align_to(ax, RIGHT)
        chart = VGroup(ax, xl, yl, ticks, diag, dots, hi, hi_lbl, hi_line, illus)

        def rl_card(name, what, reward, col):
            p = panel(5.2, 1.6, edge=col if col != MUTED else PANEL_EDGE)
            b = VGroup(txt(name, 22, col, weight=BOLD), txt(what, 17, TEXT), txt(reward, 15, MUTED))
            b.arrange(DOWN, aligned_edge=LEFT, buff=0.1)
            fit(b, w=p.width - 0.45, h=p.height - 0.25).move_to(p)
            return VGroup(p, b)

        rlhf = rl_card("RLHF", "trained on what human raters prefer", "how a typical chat LLM is tuned", MUTED)
        rlcd = rl_card("RLCD", "trained on whether its probabilities come true", "how Jev is trained", JEV_C)
        rl = VGroup(rlhf, rlcd).arrange(DOWN, buff=0.25)
        layout = VGroup(chart, rl).arrange(DOWN if PORTRAIT else RIGHT, buff=0.5 if PORTRAIT else 0.9)
        stage(layout, max_up=1.5)

        self.play(Create(ax), FadeIn(xl), FadeIn(yl), FadeIn(ticks), run_time=T(0.6))
        self.play(Create(diag), FadeIn(illus), run_time=T(0.4))
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.12), run_time=T(0.9))
        self.play(Create(hi), Create(hi_line), FadeIn(hi_lbl), run_time=T(0.5))
        self.caption("That only works if the numbers are *calibrated*: at 90% confidence, "
                     "right about 90% of the time.",
                     "*Calibrated*: at 90% sure, right about 90% of the time.")
        self.play(LaggedStart(FadeIn(rlhf, shift=UP * 0.1), FadeIn(rlcd, shift=UP * 0.1), lag_ratio=0.4),
                  run_time=T(0.9))
        self.caption("So Jev is trained with *RLCD*, Reinforcement Learning for Calibrated Decisions: "
                     "rewarded when its probabilities match real outcomes.",
                     "Trained with *RLCD*: rewarded for honest probabilities.")
        self.clear_all()

    # ------------------------------------------------------------ 8. the trade-off
    def b_tradeoff(self):
        prompt = VGroup(txt("next task:", 17, MUTED), txt("“Write a friendly reply to this customer.”", 24, TEXT))
        prompt.arrange(DOWN, buff=0.1)
        jev = model_box("Jev", JEV_C, 1.5, 1.0)
        bk = buckets(["?", "?", "?"], 0.6, 0.9, 0.25, size=14)
        no = VGroup(cross_mark(ERR), txt("no type for a paragraph", 17, ERR)).arrange(RIGHT, buff=0.12)
        jside = VGroup(VGroup(jev, bk).arrange(RIGHT, buff=0.5), no).arrange(DOWN, buff=0.3)
        llm = model_box("LLM", LLM_C, 1.5, 1.0)
        strip_w = 6.0 if PORTRAIT else 5.4
        lines, toks = token_lines(REPLY_TOKENS, strip_w - 0.5, 17)
        strip = panel(strip_w, lines.height + 0.5)
        lines.move_to(strip, aligned_edge=LEFT).shift(RIGHT * 0.25)
        lside = VGroup(llm, VGroup(strip, lines)).arrange(DOWN if PORTRAIT else RIGHT, buff=0.4)
        sides = VGroup(jside, lside).arrange(DOWN, buff=0.6, aligned_edge=LEFT if not PORTRAIT else ORIGIN)
        layout = VGroup(prompt, sides).arrange(DOWN, buff=0.6)
        stage(layout, max_up=1.4)
        self.play(FadeIn(prompt, shift=UP * 0.1), run_time=T(0.5))
        self.play(FadeIn(jev), *[Create(b.walls) for b in bk], *[FadeIn(b.lab) for b in bk], run_time=T(0.5))
        self.play(Wiggle(bk, scale_value=1.05, rotation_angle=0.02 * TAU), FadeIn(no), run_time=T(0.7))
        self.caption("The trade-off: Jev can't write. No paragraphs, no code, not even a refusal.",
                     "The trade-off: Jev can't write.")
        self.play(FadeIn(llm), FadeIn(strip), run_time=T(0.4))
        self.play(LaggedStart(*[FadeIn(t, run_time=0.15) for t in toks], lag_ratio=1.0), rate_func=linear,
                  run_time=T(2.0))
        self.caption("Writing is still a job for an ^LLM^.")
        self.clear_all()

    # ------------------------------------------------------------ 9. together
    def b_team(self):
        self.mark("outro")
        src = VGroup(*[mini_ticket() for _ in range(3)]).arrange(DOWN if not PORTRAIT else RIGHT, buff=0.2)
        jev = model_box("Jev", JEV_C, 1.6, 1.1)

        def out(icon, label, sub, col):
            p = panel(3.7, 1.15, edge=col)
            b = VGroup(icon, VGroup(txt(label, 19, col, weight=BOLD), txt(sub, 14, MUTED)).arrange(
                DOWN, aligned_edge=LEFT, buff=0.06)).arrange(RIGHT, buff=0.25)
            return VGroup(p, fit(b, w=3.4).move_to(p))

        o1 = out(gear(OK, 0.5), "sure: act", "refund, route, flag", OK)
        o2 = out(model_box("LLM", LLM_C, 0.9, 0.55), "needs words", "an LLM drafts the reply", LLM_C)
        o3 = out(person(HUMAN, 0.55), "unsure: ask", "a person decides", HUMAN)
        outs = VGroup(o1, o2, o3).arrange(DOWN, buff=0.3)
        if PORTRAIT:
            layout = VGroup(src, jev, outs).arrange(DOWN, buff=0.8)
        else:
            layout = VGroup(src, jev, outs).arrange(RIGHT, buff=1.4)
        stage(layout, max_up=1.4)
        if PORTRAIT:
            a_in = Arrow(src.get_bottom(), jev[0].get_top(), buff=0.12, color=MUTED, stroke_width=3)
            a_out = VGroup(Arrow(jev[0].get_bottom(), outs.get_top(), buff=0.1, color=MUTED, stroke_width=3))
        else:
            a_in = Arrow(src.get_right(), jev[0].get_left(), buff=0.15, color=MUTED, stroke_width=3)
            a_out = VGroup(*[Arrow(jev[0].get_right(), o.get_left(), buff=0.12, color=MUTED, stroke_width=3)
                             for o in outs])
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.1) for t in src], lag_ratio=0.15), GrowArrow(a_in),
                  FadeIn(jev), run_time=T(0.7))
        self.play(*[GrowArrow(a) for a in a_out],
                  LaggedStart(*[FadeIn(o, shift=RIGHT * 0.1) for o in outs], lag_ratio=0.25), run_time=T(0.9))
        self.caption("Jev is the *smart if-statement* in your software. LLMs write the words, "
                     "and people handle the unsure cases.",
                     "Jev decides. LLMs write. People take the unsure cases.")
        self.clear_all(rt=0.8)
        if self.kick is not None:
            self.play(FadeOut(self.kick), run_time=T(0.3))
            self.kick = None

    # ------------------------------------------------------------ end card
    def b_end(self):
        icon = buckets(["", "", ""], 0.36, 0.58, 0.13)
        for b, p in zip(icon, (0.9, 0.25, 0.1)):
            b.fill.stretch_to_fit_height(p * 0.58 * 0.92).align_to(b.walls, DOWN).shift(UP * 0.023)
            b.remove(b.lab)
        name = txt("Jev", 72, TEXT, weight=BOLD)
        head = VGroup(icon, name).arrange(RIGHT, buff=0.3)
        icon.align_to(name, DOWN)
        tag = txt("typed decisions, calibrated probabilities", 24, MUTED)
        end = VGroup(head, tag).arrange(DOWN, buff=0.3)
        fit(end, w=STAGE[1]).move_to(STAGE[0] + (DOWN * 1.0 if PORTRAIT else DOWN * 0.1))
        footer = VGroup(txt("Created by", 22, MUTED).set_opacity(0.6),
                        txt("sujee.dev", 22, TEXT, weight=MEDIUM).set_opacity(0.75)).arrange(RIGHT, buff=0.14)
        footer[1].align_to(footer[0], DOWN)
        if PORTRAIT:
            footer.next_to(end, DOWN, buff=0.9)
        else:
            footer.move_to(DOWN * 3.45)
        if SHORT:
            more = pill("Full 2-minute explainer on the channel", JEV_C, 24, edge=JEV_C)
            more.next_to(end, DOWN, buff=0.8)
            footer.next_to(more, DOWN, buff=0.8)
            end.add(more)
        self.play(FadeIn(end, shift=UP * 0.1), FadeIn(footer), run_time=0.8)
        self.wait(2.6 if SHORT else 2.0)
        self.play(FadeOut(end), FadeOut(footer), run_time=0.8)


# ---------------------------------------------------------------- YouTube thumbnails
def filled(bk, probs):
    """Set bucket levels directly (for stills)."""
    for b, p in zip(bk, probs):
        w = b.walls
        b.fill.stretch_to_fit_height(max(p * w.height * 0.92, 0.001)).align_to(w, DOWN).shift(UP * w.height * 0.04)
    return bk


class JevThumbnail(Scene):
    """One YouTube thumbnail, picked by JEV_THUMB (a, b, c): big type, one picture, readable when tiny.
    Rendered as a still: JEV_ORIENT=landscape JEV_THUMB=a uv run manim -s -r 1280,720 src/scene.py JevThumbnail"""

    def construct(self):
        v = os.environ.get("JEV_THUMB", "a")
        fw, fh = config.frame_width, config.frame_height
        self.add(VGroup(*[Dot([x, y, 0], radius=0.014, color=MUTED, fill_opacity=0.16)
                          for x in np.arange(-fw / 2 + 0.25, fw / 2, 0.5)
                          for y in np.arange(-fh / 2 + 0.25, fh / 2, 0.5)]))
        getattr(self, f"thumb_{v}")()

    def place(self, *rows, gap=0.5):
        """Stack rows and fill the frame, keeping a margin."""
        g = VGroup(*rows).arrange(DOWN, buff=gap)
        k = min((config.frame_width - 1.0) / g.width, (config.frame_height - 1.0) / g.height)
        self.add(g.scale(k).move_to(ORIGIN))
        return g

    def thumb_a(self):   # LLMs write. Jev decides.
        head = VGroup(txt("LLMs", 80, LLM_C, weight=HEAVY), txt("write.", 80, TEXT, weight=HEAVY)).arrange(RIGHT, buff=0.35)
        head2 = VGroup(txt("Jev", 80, JEV_C, weight=HEAVY), txt("decides.", 80, TEXT, weight=HEAVY)).arrange(RIGHT, buff=0.35)
        for h in (head, head2):
            h[1].align_to(h[0], DOWN)
        llm = VGroup(model_box("LLM", LLM_C, 2.2, 1.4), pill('"refund_request"', ERR, 30, edge=ERR, font=MONO))
        llm.arrange(DOWN, buff=0.35)
        bk = filled(buckets(OPTIONS, 0.9, 1.5, 0.3, size=20), JEV_PROBS)
        bk[0].walls.set_stroke(JEV_C, 5)
        val = mono("0.94", 30, TEXT, weight=BOLD).next_to(bk[0].walls, UP, buff=0.12)
        jev = VGroup(model_box("Jev", JEV_C, 2.2, 1.4), VGroup(bk, val)).arrange(DOWN, buff=0.35)
        vs = txt("vs.", 44, MUTED, weight=BOLD)
        pics = VGroup(llm, vs, jev).arrange(DOWN if PORTRAIT else RIGHT, buff=0.6)
        if not PORTRAIT:   # line the two model boxes up
            llm.align_to(jev, UP)
            vs.set_y(jev[0].get_y())
        self.place(VGroup(head, head2).arrange(DOWN, buff=0.15), pics, gap=0.7)

    def thumb_b(self):   # 16 passes vs. 1
        n = len(LLM_TOKENS)
        sq = lambda c, o: RoundedRectangle(width=0.5, height=0.5, corner_radius=0.08, fill_color=c, fill_opacity=o,
                                           stroke_color=c, stroke_width=3)
        llm_sq = VGroup(*[sq(LLM_C, 0.85) for _ in range(n)])
        if PORTRAIT:
            llm_sq.arrange_in_grid(rows=4, buff=0.14)
        else:
            llm_sq.arrange_in_grid(rows=2, buff=0.14)
        r1 = VGroup(txt("LLM", 54, LLM_C, weight=HEAVY), llm_sq).arrange(RIGHT, buff=0.5)
        r2 = VGroup(txt("Jev", 54, JEV_C, weight=HEAVY), sq(JEV_C, 0.9)).arrange(RIGHT, buff=0.5)
        r2[1].align_to(llm_sq, LEFT)
        rows = VGroup(r1, r2).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
        r2[1].set_x(llm_sq.get_left()[0] + 0.25)
        head = VGroup(txt(f"{n} passes", 84, TEXT, weight=HEAVY), txt("vs. 1", 84, JEV_C, weight=HEAVY))
        head.arrange(DOWN if PORTRAIT else RIGHT, buff=0.15 if PORTRAIT else 0.4)
        sub = txt("one model pass per token, or one in total", 30, MUTED)
        self.place(head, rows, sub, gap=0.6)

    def thumb_c(self):   # AI that doesn't write
        bk = filled(buckets(["refund", "billing", "other"], 1.5, 2.6, 0.45, size=30), [0.94, 0.04, 0.02])
        bk[0].walls.set_stroke(JEV_C, 7)
        val = mono("0.94", 64, TEXT, weight=BOLD).next_to(bk[0].walls, UP, buff=0.15)
        head = VGroup(txt("The AI that", 78, TEXT, weight=HEAVY),
                      txt("doesn't write", 78, JEV_C, weight=HEAVY)).arrange(DOWN, buff=0.1)
        tag = txt("Jev vs. LLM", 40, MUTED, weight=BOLD)
        if PORTRAIT:
            self.place(head, VGroup(bk, val), tag, gap=0.8)
        else:
            head.arrange(DOWN, buff=0.1, aligned_edge=LEFT)
            left = VGroup(head, tag).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
            self.place(VGroup(left, VGroup(bk, val)).arrange(RIGHT, buff=1.0))
