"""How a neural network learns: forward pass, backpropagation, weight updates.

Normally rendered through ../render.sh. To run Manim directly, from the story directory:
  NN_ORIENT=landscape uv run manim -qk --frame_rate 30 src/scene.py NeuralNet
  NN_ORIENT=portrait  uv run manim -qk --frame_rate 30 src/scene.py NeuralNet
Timeline events (for music sync) are written to workspace/tmp/events_<orient>.json.
"""
import json
import os
import re
import textwrap

import numpy as np
from manim import *

ORIENT = os.environ.get("NN_ORIENT", "landscape")
PORTRAIT = ORIENT == "portrait"
SPEED = float(os.environ.get("NN_SPEED", "0.51" if PORTRAIT else "1.0"))

if PORTRAIT:
    q = config.pixel_height
    config.pixel_width = q
    config.pixel_height = int(round(q * 16 / 9 / 2)) * 2
    config.frame_height = 16.0
    config.frame_width = 9.0

# ---------------------------------------------------------------- palette
BG = "#0B0F17"
PANEL = "#141B27"
PANEL_EDGE = "#243044"
TEXT = "#E6EAF0"
MUTED = "#8A94A6"
NODE_OFF = "#1A2231"
NODE_EDGE = "#3A475C"
NODE_ON = "#7DD3FC"
SIGNAL = "#BAF2FF"
POS = "#5B9BF0"
NEG = "#E9A23B"
EDGE_BASE = "#2C3749"
ERR = "#FF6B6B"
OK = "#4ADE80"
FONT = "Inter"

CLASSES = ["cat", "dog", "rabbit", "bird"]
# scripted predictions per pass (cat, dog, rabbit, bird)
PROBS = [
    [0.21, 0.52, 0.18, 0.09],
    [0.33, 0.14, 0.45, 0.08],
    [0.86, 0.05, 0.06, 0.03],
]
LOSS = [-np.log(p[0]) for p in PROBS]

config.background_color = BG


def T(x):
    return x * SPEED


def txt(s, size=28, color=TEXT, weight=NORMAL):
    return Text(s, font=FONT, font_size=size, color=color, weight=weight)


HL = {"*": NODE_ON, "~": ERR, "^": OK}


def markup(s, width_chars, size, color=TEXT):
    """Wrap text and turn *sky*, ~red~, ^green^ spans into Pango markup."""
    body = "\n".join(textwrap.wrap(s, width_chars))
    for ch, col in HL.items():
        c = re.escape(ch)
        body = re.sub(c + r"(.+?)" + c,
                      lambda m, col=col: f'<span foreground="{col}" weight="600">{m.group(1)}</span>',
                      body, flags=re.S)
    return MarkupText(body, font=FONT, font_size=size, color=color, line_spacing=0.9)


def rate_after(start, rf=smooth):
    """Rate func that stays at 0 until `start` (0..1) of the animation, then eases."""
    return lambda t: rf(np.clip((t - start) / (1 - start), 0, 1))


# ---------------------------------------------------------------- cat art
def cat_picture(size=2.4):
    card = RoundedRectangle(width=size, height=size, corner_radius=0.18,
                            fill_color=PANEL, fill_opacity=1,
                            stroke_color=PANEL_EDGE, stroke_width=2)
    bg = Circle(radius=0.92, fill_color="#1E2A3D", fill_opacity=1, stroke_width=0).shift(DOWN * 0.05)
    fur, dark, cream, pink = "#F2A65A", "#D27F35", "#FBE3C4", "#F4A6B0"
    ears = VGroup()
    for s in (-1, 1):
        ear = Polygon([s * 0.70, 0.12, 0], [s * 0.50, 0.86, 0], [s * 0.12, 0.42, 0],
                      fill_color=fur, fill_opacity=1, stroke_width=0)
        inner = Polygon([s * 0.58, 0.22, 0], [s * 0.49, 0.68, 0], [s * 0.26, 0.40, 0],
                        fill_color=pink, fill_opacity=1, stroke_width=0)
        ears.add(ear, inner)
    head = Ellipse(width=1.56, height=1.28, fill_color=fur, fill_opacity=1, stroke_width=0).shift(DOWN * 0.1)
    stripes = VGroup(*[
        Line([x, 0.50 - abs(x) * 0.5, 0], [x * 0.8, 0.28 - abs(x) * 0.4, 0],
             stroke_color=dark, stroke_width=5, cap_style=CapStyleType.ROUND)
        for x in (-0.14, 0.0, 0.14)
    ])
    muzzle = Ellipse(width=0.78, height=0.46, fill_color=cream, fill_opacity=1, stroke_width=0).shift(DOWN * 0.40)
    eyes = VGroup()
    for s in (-1, 1):
        iris = Ellipse(width=0.25, height=0.29, fill_color="#9BD35A", fill_opacity=1,
                       stroke_color="#3B4A1F", stroke_width=1.5).move_to([s * 0.31, 0.0, 0])
        pupil = Ellipse(width=0.07, height=0.22, fill_color="#111", fill_opacity=1, stroke_width=0).move_to(iris)
        glint = Circle(radius=0.028, fill_color=WHITE, fill_opacity=1, stroke_width=0).move_to(iris.get_center() + [0.04, 0.06, 0])
        eyes.add(iris, pupil, glint)
    nose = Polygon([-0.08, -0.25, 0], [0.08, -0.25, 0], [0, -0.34, 0],
                   fill_color=pink, fill_opacity=1, stroke_color="#C9707E", stroke_width=1)
    mouth = VGroup(
        ArcBetweenPoints([0, -0.34, 0], [-0.14, -0.37, 0], angle=-PI * 0.7),
        ArcBetweenPoints([0.14, -0.37, 0], [0, -0.34, 0], angle=-PI * 0.7),
    ).set_stroke("#6B4A3A", 2)
    whiskers = VGroup()
    for s in (-1, 1):
        for dy in (-0.02, -0.11, -0.20):
            whiskers.add(Line([s * 0.30, -0.33, 0], [s * 0.86, -0.33 + dy * 1.6 + 0.08, 0],
                              stroke_color="#FFF5E6", stroke_width=1.6, stroke_opacity=0.85))
    cat = VGroup(ears, head, stripes, muzzle, eyes, nose, mouth, whiskers).scale(size / 2.4 * 1.02)
    cat.move_to(card.get_center() + DOWN * 0.02 * size)
    bg.scale(size / 2.4).move_to(card)
    return VGroup(card, bg, cat)


def generic_picture(size=2.4):
    """Placeholder 'some image' card: photo icon (mountains + sun) with a question mark."""
    k = size / 2.4
    card = RoundedRectangle(width=size, height=size, corner_radius=0.18, fill_color=PANEL, fill_opacity=1,
                            stroke_color=PANEL_EDGE, stroke_width=2)
    frame = RoundedRectangle(width=1.7 * k, height=1.3 * k, corner_radius=0.12 * k, fill_opacity=0,
                             stroke_color=MUTED, stroke_width=3, stroke_opacity=0.6)
    bl = frame.get_corner(DL)
    hills = VGroup(
        Polygon(bl + [0.12 * k, 0.12 * k, 0], bl + [0.62 * k, 0.72 * k, 0], bl + [1.05 * k, 0.12 * k, 0]),
        Polygon(bl + [0.72 * k, 0.12 * k, 0], bl + [1.18 * k, 0.55 * k, 0], bl + [1.58 * k, 0.12 * k, 0]),
    ).set_fill(MUTED, 0.28).set_stroke(width=0)
    sun = Circle(radius=0.14 * k, fill_color=MUTED, fill_opacity=0.35, stroke_width=0).move_to(
        frame.get_corner(UR) + [-0.36 * k, -0.34 * k, 0])
    q = Text("?", font=FONT, font_size=int(96 * k), color=NODE_ON, weight=BOLD).move_to(frame)
    return VGroup(card, frame, hills, sun, q)


def check_mark(color=OK, s=0.2):
    return VMobject(stroke_color=color, stroke_width=5).set_points_as_corners(
        [[-s, 0, 0], [-s * 0.3, -s * 0.7, 0], [s, s * 0.8, 0]])


def cross_mark(color=ERR, s=0.16):
    return VGroup(Line([-s, -s, 0], [s, s, 0]), Line([-s, s, 0], [s, -s, 0])).set_stroke(color, 5)


def edge_style(w):
    m = min(abs(w), 1.3) / 1.3
    col = interpolate_color(ManimColor(EDGE_BASE), ManimColor(POS if w > 0 else NEG), 0.25 + 0.75 * m)
    return col, 0.5 + 2.6 * m, 0.22 + 0.55 * m


# ---------------------------------------------------------------- scene
class NeuralNet(Scene):
    def mark(self, name):
        self.events[name] = round(self.renderer.time, 3)

    # ------------------------------------------------------------ build
    def setup_network(self):
        rng = np.random.default_rng(7)
        sizes = [6, 7, 7, 4]
        xs = [-3.2, -1.3, 0.6, 2.5]
        spacing = [0.8, 0.68, 0.68, 1.05]
        radius = [0.19, 0.17, 0.17, 0.24]
        cy = 0.2
        self.sizes = sizes
        self.nodes, self.glows = [], []
        if PORTRAIT:  # layers stacked top -> bottom
            rows_y = [2.9, 1.3, -0.25, -1.8]
            spacing = [1.2, 1.1, 1.1, 2.05]
            radius = [0.24, 0.22, 0.22, 0.3]
        for li, (n, sp, r) in enumerate(zip(sizes, spacing, radius)):
            offs = (np.arange(n) - (n - 1) / 2) * sp
            if PORTRAIT:
                pts = [[o, rows_y[li], 0] for o in offs]
            else:
                pts = [[xs[li], -o + cy, 0] for o in offs]
            layer = VGroup(*[Circle(radius=r, fill_color=NODE_OFF, fill_opacity=1,
                                    stroke_color=NODE_EDGE, stroke_width=2).move_to(pt) for pt in pts])
            glow = VGroup(*[Circle(radius=r * 2.1, fill_color=NODE_ON, fill_opacity=0,
                                   stroke_width=0).move_to(c) for c in layer])
            self.nodes.append(layer)
            self.glows.append(glow)
        self.W = [rng.normal(0, 0.65, (sizes[l], sizes[l + 1])) for l in range(3)]
        self.edges = []
        for l in range(3):
            grp = VGroup()
            for i, a in enumerate(self.nodes[l]):
                for j, b in enumerate(self.nodes[l + 1]):
                    d = normalize(b.get_center() - a.get_center())
                    line = Line(a.get_center() + d * a.radius, b.get_center() - d * b.radius)
                    col, wd, op = edge_style(self.W[l][i, j])
                    line.set_stroke(col, wd, op)
                    line.ij = (i, j)
                    grp.add(line)
            self.edges.append(grp)

        # output panel
        self.rows, self.trackers, self.bars, self.pcts, self.labels = [], [], [], [], []
        x0, bx, W = 2.95, 4.12, 1.3
        for k, node in enumerate(self.nodes[3]):
            y = node.get_y()
            if PORTRAIT:
                W = 1.45
                lab = txt(CLASSES[k], 30, MUTED).move_to(node.get_center() + DOWN * 0.68)
                track = RoundedRectangle(width=W, height=0.18, corner_radius=0.09, fill_color="#FFFFFF",
                                         fill_opacity=0.07, stroke_width=0).move_to(node.get_center() + DOWN * 1.12)
            else:
                lab = txt(CLASSES[k], 26, MUTED).move_to([x0, y, 0], aligned_edge=LEFT)
                track = RoundedRectangle(width=W, height=0.16, corner_radius=0.08, fill_color="#FFFFFF",
                                         fill_opacity=0.07, stroke_width=0).move_to([bx + W / 2, y, 0])
            vt = ValueTracker(0)

            def mk_bar(vt=vt, track=track, k=k):
                w = max(vt.get_value() * track.width, 1e-3)
                h = track.height
                bar = RoundedRectangle(width=w, height=h, corner_radius=min(h, w) / 2,
                                       fill_color=self.bar_colors[k], fill_opacity=1, stroke_width=0)
                return bar.align_to(track, LEFT).set_y(track.get_y())

            def mk_pct(vt=vt, track=track):
                t = txt(f"{round(vt.get_value() * 100)}%", 26 if PORTRAIT else 22, TEXT)
                if PORTRAIT:
                    return t.move_to(track.get_center() + DOWN * 0.4)
                return t.move_to(track.get_right() + RIGHT * 0.12, aligned_edge=LEFT)

            bar = always_redraw(mk_bar)
            pct = always_redraw(mk_pct)
            self.labels.append(lab)
            self.trackers.append(vt)
            self.bars.append(bar)
            self.pcts.append(pct)
            self.rows.append(VGroup(lab, track, bar, pct))
        self.tracks = VGroup(*[r[1] for r in self.rows])

        layer_names = ["Input", "Hidden", "Hidden", "Output"]
        bottom = min(l.get_bottom()[1] for l in self.nodes) - 0.32
        self.layer_labels = VGroup(*[txt(nm, 18, MUTED).move_to([x, bottom, 0]) for nm, x in zip(layer_names, xs)])
        self.target_tag = VGroup(
            txt("Correct answer:", 20, MUTED), txt("cat", 20, OK, weight=BOLD)
        ).arrange(RIGHT, buff=0.12).move_to([bx, self.nodes[3][-1].get_y() - 0.62, 0], aligned_edge=LEFT)
        if PORTRAIT:
            self.layer_labels = VGroup()
            self.target_tag.scale(1.3).move_to([2.0, 4.55, 0])

        self.core = VGroup(*self.edges, *self.glows, *self.nodes,
                           *[VGroup(r[0], r[1]) for r in self.rows], self.layer_labels, self.target_tag)
        # always_redraw rows follow their tracks, so only static parts are in `core`

    # ------------------------------------------------------------ layout helpers
    def caption(self, s, short=None, wait=None):
        if PORTRAIT and short is False:
            return
        s = short if (PORTRAIT and short) else s
        if PORTRAIT:
            m = markup(s, 30, 36).move_to([0, -5.05, 0])
        else:
            m = markup(s, 74, 27).move_to([0, -3.25, 0])
        if self.cap is not None:
            self.play(FadeOut(self.cap, shift=UP * 0.1), run_time=T(0.3))
        self.play(FadeIn(m, shift=UP * 0.1), run_time=T(0.45))
        self.cap = m
        if wait is None:
            wait = 0.6 + 0.26 * len(s.split())
            if PORTRAIT:
                wait = 0.25 + 0.2 * len(s.split())
        if wait:
            self.wait(wait)

    def chip(self, pass_no, phase, color=NODE_ON):
        parts = []
        if pass_no:
            parts.append(txt(f"PASS {pass_no}", 20, color, weight=BOLD))
            parts.append(Dot(radius=0.03, color=MUTED))
        parts.append(txt(phase, 20, TEXT))
        g = VGroup(*parts).arrange(RIGHT, buff=0.16)
        pill = RoundedRectangle(width=g.width + 0.5, height=0.5, corner_radius=0.25,
                                fill_color=PANEL, fill_opacity=1, stroke_color=PANEL_EDGE, stroke_width=1.5)
        c = VGroup(pill, g.move_to(pill))
        if PORTRAIT:
            c.scale(1.25).move_to([0, 7.15, 0])
        else:
            c.move_to([-7.11 + 0.45, 3.45, 0], aligned_edge=LEFT)
        return c

    def set_chip(self, *a, **k):
        new = self.chip(*a, **k)
        if self.chip_m is None:
            self.play(FadeIn(new, shift=DOWN * 0.1), run_time=T(0.5))
        else:
            self.play(FadeOut(self.chip_m, shift=UP * 0.08), FadeIn(new, shift=UP * 0.08), run_time=T(0.5))
        self.chip_m = new

    def build_error_meter(self):
        self.loss_vt = ValueTracker(LOSS[0])
        label = txt("Error (loss)", 18, MUTED)
        track = RoundedRectangle(width=1.9, height=0.12, corner_radius=0.06, fill_color=WHITE,
                                 fill_opacity=0.08, stroke_width=0)
        top = VGroup(label, txt("0.00", 24, TEXT, weight=BOLD)).arrange(RIGHT, buff=0.3)
        meter = VGroup(top, track).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        if PORTRAIT:
            meter.scale(1.3).move_to([2.0, 5.6, 0])
        else:
            meter.move_to([7.11 - 0.45, 3.45, 0], aligned_edge=RIGHT)
        tr = track

        def mk_val():
            v = self.loss_vt.get_value()
            return txt(f"{v:.2f}", 24, TEXT, weight=BOLD).scale(1.3 if PORTRAIT else 1).move_to(
                ph, aligned_edge=LEFT)

        def mk_bar():
            v = self.loss_vt.get_value()
            w = max(tr.width * min(v / 2.0, 1), 1e-3)
            col = interpolate_color(ManimColor(OK), ManimColor(ERR), min(v / 1.6, 1))
            return RoundedRectangle(width=w, height=tr.height, corner_radius=min(w, tr.height) / 2,
                                    fill_color=col, fill_opacity=1, stroke_width=0).align_to(tr, LEFT).set_y(tr.get_y())

        ph = top[1]
        top.remove(ph)
        self.meter = VGroup(meter, always_redraw(mk_val), always_redraw(mk_bar))

    # ------------------------------------------------------------ animation pieces
    def node_anims(self, l, acts, start=0.45):
        anims = []
        for node, glow, a in zip(self.nodes[l], self.glows[l], acts):
            col = interpolate_color(ManimColor(NODE_OFF), ManimColor(NODE_ON), a)
            anims.append(node.animate(rate_func=rate_after(start)).set_fill(col).set_stroke(
                interpolate_color(ManimColor(NODE_EDGE), ManimColor(NODE_ON), a)))
            anims.append(glow.animate(rate_func=rate_after(start)).set_fill(opacity=0.16 * a))
        return anims

    def forward(self, acts, rt=1.3):
        for l in range(3):
            flashes = []
            for line in self.edges[l]:
                i, j = line.ij
                strength = acts[l][i] * min(abs(self.W[l][i, j]), 1.2) / 1.2
                if strength < 0.08:
                    continue
                f = line.copy().set_stroke(SIGNAL, 2.5 + 2 * strength, 0.25 + 0.75 * strength)
                flashes.append(ShowPassingFlash(f, time_width=0.55, rate_func=linear))
            self.play(*flashes, *self.node_anims(l + 1, acts[l + 1], start=0.5), run_time=T(rt))

    def show_probs(self, probs, rt=1.2):
        self.play(*[vt.animate.set_value(p) for vt, p in zip(self.trackers, probs)],
                  *[lab.animate.set_color(TEXT) for lab in self.labels], run_time=T(rt))

    def highlight_row(self, k, color):
        row = VGroup(self.labels[k], self.rows[k][1], self.pcts[k])
        box = SurroundingRectangle(row, color=color, buff=0.12, corner_radius=0.1, stroke_width=2.5)
        icon = (check_mark(color) if color == OK else cross_mark(color))
        if PORTRAIT:
            icon.scale(1.2).next_to(box, DOWN, buff=0.16)
        else:
            box.stretch_to_fit_width(box.width + 0.25).shift(RIGHT * 0.12)
            icon.next_to(box, RIGHT, buff=0.14)
        return VGroup(box, icon)

    def backprop(self, dW, rt=1.4, tag_edge=None):
        # error appears at the output layer
        rings = VGroup(*[n.copy().set_fill(opacity=0).set_stroke(ERR, 3) for n in self.nodes[3]])
        self.play(LaggedStart(*[r.animate(rate_func=rush_from).scale(1.9).set_stroke(opacity=0) for r in rings],
                              lag_ratio=0.08), run_time=T(0.9))
        self.remove(rings)
        for l in (2, 1, 0):
            flashes, updates = [], []
            newW = self.W[l] + dW[l]
            mag = np.abs(dW[l]) / (np.abs(dW[l]).max() + 1e-9)
            for line in self.edges[l]:
                i, j = line.ij
                s = mag[i, j]
                if s > 0.15:
                    rev = Line(line.get_end(), line.get_start()).set_stroke(ERR, 2 + 2.5 * s, 0.3 + 0.7 * s)
                    flashes.append(ShowPassingFlash(rev, time_width=0.55, rate_func=linear))
                col, wd, op = edge_style(newW[i, j])
                updates.append(line.animate(rate_func=rate_after(0.35)).set_stroke(col, wd, op))
            pulses = []
            for n in self.nodes[l]:
                r = n.copy().set_fill(opacity=0).set_stroke(ERR, 2.5)
                pulses.append(r)
            self.add(*pulses)
            self.play(*flashes, *updates,
                      *[r.animate(rate_func=rate_after(0.55, rush_from)).scale(1.7).set_stroke(opacity=0) for r in pulses],
                      run_time=T(rt))
            self.remove(*pulses)
            if tag_edge is not None and l == tag_edge[0]:
                self.show_weight_tag(tag_edge, self.W[l][tag_edge[1], tag_edge[2]], newW[tag_edge[1], tag_edge[2]])
            self.W[l] = newW

    def show_weight_tag(self, te, w0, w1):
        l, i, j = te
        line = next(e for e in self.edges[l] if e.ij == (i, j))
        hl = line.copy().set_stroke(ERR, 5, 1)
        s = self.scale_f
        body = VGroup(txt("weight", 18, MUTED), txt(f"{w0:+.2f}", 20, TEXT),
                      txt("→", 20, MUTED), txt(f"{w1:+.2f}", 20, OK, weight=BOLD)).arrange(RIGHT, buff=0.12)
        pill = RoundedRectangle(width=body.width + 0.4, height=0.46, corner_radius=0.23, fill_color=PANEL,
                                fill_opacity=0.96, stroke_color=ERR, stroke_width=1.5)
        tag = VGroup(pill, body.move_to(pill)).scale(s)
        if PORTRAIT:
            tag.scale(1.3).move_to([line.get_center()[0] - 1.2, self.nodes[2][0].get_y() + 0.78, 0])
            tag.shift(RIGHT * max(0, -4.3 - tag.get_left()[0]))
        else:
            top = max(n.get_top()[1] for n in self.nodes[2])
            tag.move_to([line.get_center()[0], top + 0.45, 0])
        conn = DashedLine(tag.get_right() if PORTRAIT else tag.get_bottom(), line.point_from_proportion(0.5), dash_length=0.06,
                          stroke_color=ERR, stroke_width=1.5, stroke_opacity=0.8)
        self.play(Create(hl), FadeIn(tag, shift=DOWN * 0.1), Create(conn), run_time=T(0.6))
        self.wait(T(1.6))
        self.play(FadeOut(hl), FadeOut(tag), FadeOut(conn), run_time=T(0.5))

    def reset_pass(self):
        anims = [vt.animate.set_value(0) for vt in self.trackers]
        for l in range(1, 4):
            anims += self.node_anims(l, [0] * self.sizes[l], start=0)
        anims += [lab.animate.set_color(MUTED) for lab in self.labels]
        if self.verdict is not None:
            anims.append(FadeOut(self.verdict))
            self.verdict = None
        self.play(*anims, run_time=T(0.8))

    def feed_input(self, acts):
        card = self.picture[0]
        n = 8
        inner = card.width * 0.84
        step = inner / n
        grid = VGroup()
        for k in range(n + 1):
            off = -inner / 2 + k * step
            grid.add(Line(card.get_center() + [off, -inner / 2, 0], card.get_center() + [off, inner / 2, 0]))
            grid.add(Line(card.get_center() + [-inner / 2, off, 0], card.get_center() + [inner / 2, off, 0]))
        grid.set_stroke(NODE_ON, 1, 0.35)
        return grid, step, inner

    def pixels_to_input(self, acts, grid_info, rt=1.3):
        grid, step, inner = grid_info
        card = self.picture[0]
        rng = np.random.default_rng(3)
        cells = rng.choice(64, size=len(self.nodes[0]) * 2, replace=False)
        sqs = []
        for k, c in enumerate(cells):
            r, q = divmod(c, 8)
            p = card.get_center() + [-inner / 2 + (q + 0.5) * step, inner / 2 - (r + 0.5) * step, 0]
            sq = Square(side_length=step * 0.9, fill_color=NODE_ON, fill_opacity=0.55, stroke_width=0).move_to(p)
            sqs.append((sq, self.nodes[0][k % len(self.nodes[0])]))
        self.play(LaggedStart(*[FadeIn(s) for s, _ in sqs], lag_ratio=0.04), run_time=T(0.5))
        self.play(LaggedStart(*[s.animate.scale(0.35).move_to(node).set_opacity(0) for s, node in sqs],
                              lag_ratio=0.03),
                  *self.node_anims(0, acts[0], start=0.55), run_time=T(rt))
        for s, _ in sqs:
            self.remove(s)

    # ------------------------------------------------------------ main
    def construct(self):
        self.events = {}
        self.cap = None
        self.chip_m = None
        self.verdict = None
        self.bar_colors = [NODE_ON] * 4
        self.scale_f = 1.0
        rng = np.random.default_rng(11)
        self.setup_network()
        self.build_error_meter()

        # picture
        if PORTRAIT:
            self.picture = cat_picture(2.7).move_to([-2.0, 5.35, 0])
        else:
            self.picture = cat_picture(2.4).move_to([-5.5, 0.2, 0])
        pic_label = txt("input image", 18, MUTED).next_to(self.picture, DOWN, buff=0.16)

        # ---- title
        title = txt("How a Neural Network Learns", 58 if not PORTRAIT else 50, TEXT, weight=BOLD)
        sub = txt("forward pass  ·  backpropagation  ·  weight updates", 26, MUTED)
        tgroup = VGroup(title, sub).arrange(DOWN, buff=0.35)
        if PORTRAIT:
            title2 = VGroup(txt("How a Neural", 58, TEXT, weight=BOLD), txt("Network Learns", 58, TEXT, weight=BOLD)).arrange(DOWN, buff=0.2)
            sub = txt("forward pass · backprop · weights", 28, MUTED)
            tgroup = VGroup(title2, sub).arrange(DOWN, buff=0.4).move_to([0, 0.6, 0])
        self.mark("start")
        self.play(FadeIn(tgroup, shift=UP * 0.2), run_time=T(1.2))
        self.wait(T(1.6) if not PORTRAIT else 0.6)
        self.play(FadeOut(tgroup, shift=UP * 0.2), run_time=T(0.7))

        # ---- network intro
        self.mark("intro")
        self.play(LaggedStart(*[LaggedStart(*[GrowFromCenter(n) for n in layer], lag_ratio=0.08)
                                for layer in self.nodes], lag_ratio=0.25), run_time=T(1.6))
        self.add(*self.glows)
        self.bring_to_front(*self.nodes)
        self.play(LaggedStart(*[Create(g) for g in self.edges], lag_ratio=0.3),
                  FadeIn(self.layer_labels), run_time=T(1.6))
        self.bring_to_front(*self.nodes)
        self.caption("A neural network: *neurons* (circles) joined by *weighted connections* (lines).",
                     "A neural network: *neurons* joined by *weighted connections*.")
        self.play(LaggedStart(*[FadeIn(r[0], shift=LEFT * 0.1) for r in self.rows], lag_ratio=0.1),
                  LaggedStart(*[FadeIn(r[1]) for r in self.rows], lag_ratio=0.1), run_time=T(0.9))
        self.fade_in_live(*self.bars, *self.pcts)
        # input picture on the left, with an arrow into the input layer
        in_arrow = VGroup()
        if not PORTRAIT:
            in_arrow = Arrow(self.picture.get_right() + RIGHT * 0.05, [self.nodes[0].get_left()[0] - 0.08, 0.2, 0],
                             buff=0, stroke_width=3, color=MUTED, tip_length=0.16, max_tip_length_to_length_ratio=0.3)
        generic = generic_picture(self.picture[0].width).move_to(self.picture)
        self.play(FadeIn(generic, scale=0.92), FadeIn(pic_label), GrowArrow(in_arrow) if not PORTRAIT else Wait(),
                  run_time=T(0.9))
        self.caption("Its job: look at a picture and decide which animal it shows.",
                     False)

        # ---- section title: dim the stage, show the title, bring the stage back
        self.mark("train_title")
        veil = Rectangle(width=config.frame_width + 1, height=config.frame_height + 1, fill_color=BG,
                         fill_opacity=0.88, stroke_width=0)
        if PORTRAIT:
            ttl = VGroup(txt("Here's how the network", 44, TEXT, weight=BOLD),
                         txt("is trained", 44, TEXT, weight=BOLD)).arrange(DOWN, buff=0.18).move_to(UP * 0.8)
        else:
            ttl = txt("Here's how the network is trained", 46, TEXT, weight=BOLD).move_to(UP * 0.25)
        rule = Line(LEFT, RIGHT, stroke_color=NODE_ON, stroke_width=3).set_width(ttl.width * 0.35)
        rule.next_to(ttl, DOWN, buff=0.3)
        fade_cap = [FadeOut(self.cap)] if self.cap is not None else []
        self.play(FadeIn(veil), *fade_cap, run_time=T(0.7))
        self.cap = None
        self.play(FadeIn(ttl, shift=UP * 0.15), Create(rule), run_time=T(0.9))
        self.wait(T(1.4) if not PORTRAIT else 0.45)
        self.play(FadeOut(ttl, shift=UP * 0.15), FadeOut(rule), run_time=T(0.6))
        self.play(FadeOut(veil), run_time=T(0.6))

        # ---- the input
        self.mark("input")
        self.play(FadeOut(generic[1:], scale=0.9), FadeIn(self.picture[1:], scale=1.05), run_time=T(0.8))
        self.add(self.picture)
        self.remove(generic, *generic)  # FadeOut of a slice splits the group; drop every piece
        grid_info = self.feed_input(None)
        self.caption("The input is a picture of a cat. To the network it is just a grid of numbers: *pixels*.",
                     "Input: a cat photo. To the network it's just numbers: *pixels*.", wait=0)
        self.play(Create(grid_info[0], lag_ratio=0.02), run_time=T(1.0))
        self.wait(T(1.8) if not PORTRAIT else 1.2)

        in_acts = [0.9, 0.35, 0.75, 0.55, 0.95, 0.4]

        def acts_for(k):
            r = np.random.default_rng(100 + k)
            h1 = np.clip(r.beta(1.4, 1.6, 7), 0.05, 1)
            h2 = np.clip(r.beta(1.4, 1.6, 7), 0.05, 1)
            return [in_acts, h1, h2, PROBS[k]]

        passes = [
            dict(wrong=1, cap_fwd=("*Forward pass*: the signal flows layer by layer. Each weight strengthens or weakens it.",
                                   "*Forward pass*: signals flow layer by layer, scaled by each weight."),
                 cap_pred=("Prediction: ~dog~ (52%). But the correct answer is *cat*. ~Wrong!~",
                           "Prediction: ~dog~. The answer is *cat*. ~Wrong!~")),
            dict(wrong=2, cap_fwd=("Same picture, adjusted weights. Another forward pass.",
                                   "Same picture, new weights. Forward pass again."),
                 cap_pred=("Prediction: ~rabbit~ (45%). Closer, *cat* rose to 33%, but still ~wrong~.",
                           "Prediction: ~rabbit~. Closer, but still ~wrong~.")),
            dict(wrong=None, cap_fwd=("Third try.", "Third try."),
                 cap_pred=("Prediction: ^cat^ (86%). ^Correct!^", "Prediction: ^cat^ (86%). ^Correct!^")),
        ]

        meter_shown = False
        for k, ps in enumerate(passes):
            acts = acts_for(k)
            self.mark(f"pass{k + 1}")
            if k > 0:
                self.reset_pass()
            self.set_chip(k + 1, "Forward pass")
            self.caption(*ps["cap_fwd"], wait=0)
            if k == 0:
                self.pixels_to_input(acts, grid_info)
                self.play(FadeOut(grid_info[0]), FadeOut(in_arrow), run_time=T(0.4))
            else:
                self.pixels_to_input(acts, grid_info, rt=0.9)
            self.forward(acts, rt=1.35 if k == 0 else 1.0)
            if k == 0:
                self.wait(T(0.6))
                self.caption("The output layer scores every animal. The highest score is the network's guess.",
                             "The output layer scores each animal. Highest score wins.", wait=0)
            self.show_probs(PROBS[k])
            if k == 0:
                self.wait(T(1.8))

            # verdict
            self.set_chip(k + 1, "Check the answer", color=ERR if ps["wrong"] else OK)
            pred = ps["wrong"] if ps["wrong"] else 0
            color = ERR if ps["wrong"] else OK
            self.verdict = self.highlight_row(pred, color)
            anims = [Create(self.verdict[0]), FadeIn(self.verdict[1], scale=0.6),
                     self.labels[pred].animate.set_color(color)]
            if k == 0:
                anims.append(FadeIn(self.target_tag, shift=UP * 0.1))
            self.mark("wrong" + str(k + 1) if ps["wrong"] else "correct")
            self.play(*anims, run_time=T(0.7))
            if not meter_shown:
                self.caption(*ps["cap_pred"])
                self.loss_vt.set_value(LOSS[0])
                self.fade_in_live(self.meter[0], self.meter[1], self.meter[2])
                self.caption("We measure how wrong it was. This number is the *error*, or loss.",
                             "How wrong was it? That's the *error* (loss).")
                meter_shown = True
            else:
                self.play(self.loss_vt.animate.set_value(LOSS[k]), run_time=T(1.0))
                self.caption(*ps["cap_pred"])

            if ps["wrong"] is None:
                break

            # backprop
            self.mark(f"backprop{k + 1}")
            self.set_chip(k + 1, "Backpropagation", color=ERR)
            dW = []
            for l in range(3):
                d = rng.normal(0, 0.35, self.W[l].shape)
                if l == 2:
                    d[:, 0] += 0.45
                    d[:, ps["wrong"]] -= 0.45
                dW.append(d)
            dW[2][3, 0] = abs(dW[2][3, 0]) + 0.2
            if k == 0:
                self.caption("~Backpropagation~: the error is sent backward, from the output toward the input.",
                             "~Backpropagation~: the error flows backward through the network.", wait=0)
                self.backprop(dW, rt=1.45, tag_edge=(2, 3, 0))
                self.caption("Every weight gets a small nudge, in the direction that makes *cat* more likely.",
                             "Each weight is nudged so *cat* becomes more likely.")
            else:
                self.caption("Backpropagate again, and adjust the weights again.",
                             "Backpropagate again. Adjust the weights again.", wait=0)
                self.backprop(dW, rt=1.05, tag_edge=(2, 3, 0))
                self.wait(T(0.4))

        # ---- success
        self.set_chip(3, "Learned it", color=OK)
        glow = self.picture[0].copy().set_fill(opacity=0).set_stroke(OK, 3)
        self.play(Create(glow), Flash(self.nodes[3][0], color=OK, line_length=0.2 * self.scale_f,
                                      flash_radius=0.4 * self.scale_f), run_time=T(0.8))
        self.caption("Error dropped from ~1.56~ to ^0.15^ in three rounds of feedback.",
                     "Error: ~1.56~ → ^0.15^ in three rounds.")

        # ---- outro: the training loop
        self.mark("outro")
        for m in [*self.bars, *self.pcts, *self.meter]:
            m.clear_updaters()
        stage = VGroup(self.core, *self.bars, *self.pcts, self.picture, pic_label, self.verdict, glow,
                       self.meter, self.chip_m)
        self.play(FadeOut(stage), FadeOut(self.cap), run_time=T(0.9))
        self.cap = None
        steps = ["Forward pass", "Measure error", "Backpropagate", "Adjust weights"]
        cols = [NODE_ON, ERR, ERR, OK]
        chips = VGroup()
        for s, c in zip(steps, cols):
            t = txt(s, 26 if not PORTRAIT else 28, TEXT)
            p = RoundedRectangle(width=t.width + 0.6, height=0.66, corner_radius=0.33, fill_color=PANEL,
                                 fill_opacity=1, stroke_color=c, stroke_width=2)
            chips.add(VGroup(p, t.move_to(p)))
        arrows = VGroup()
        if PORTRAIT:  # vertical list with a return arc on the left
            for ch in chips:
                ch.scale(1.25)
            chips.arrange(DOWN, buff=0.75).move_to([0.5, 1.0, 0])
            for a in range(3):
                arrows.add(Arrow(chips[a].get_bottom(), chips[a + 1].get_top(), buff=0.08,
                                 stroke_width=3, color=MUTED, tip_length=0.2, max_tip_length_to_length_ratio=0.4))
            x = min(c.get_left()[0] for c in chips) - 0.35
            arrows.add(CurvedArrow([x + 0.2, chips[3].get_y(), 0], [x + 0.2, chips[0].get_y(), 0], angle=-PI * 0.6,
                                   stroke_width=3, color=MUTED, tip_length=0.2))
            center = txt("repeat", 28, MUTED).rotate(PI / 2).move_to([arrows[3].get_left()[0] - 0.35, chips.get_y(), 0])
        else:
            R, cy = 2.0, 0.35
            pos = [UP * R * 0.72, RIGHT * R * 1.6, DOWN * R * 0.72, LEFT * R * 1.6]
            for ch, p in zip(chips, pos):
                ch.move_to(p + UP * cy)
            for a in range(4):
                b = (a + 1) % 4
                arrows.add(CurvedArrow(self._edge_pt(chips[a], chips[b]), self._edge_pt(chips[b], chips[a]),
                                       angle=-PI / 4, stroke_width=2.5, color=MUTED, tip_length=0.18))
            center = txt("repeat", 22, MUTED).move_to(UP * cy)
        self.play(LaggedStart(*[AnimationGroup(FadeIn(chips[i], scale=0.9), Create(arrows[i]))
                                for i in range(4)], lag_ratio=0.35), FadeIn(center), run_time=T(2.4))
        self.caption("That's training: this loop, repeated over *millions of images*, until the network gets them right.",
                     "That's training: this loop, repeated over *millions of images*.")
        if PORTRAIT:
            end = VGroup(txt("How a Neural", 48, TEXT, weight=BOLD), txt("Network Learns", 48, TEXT, weight=BOLD)).arrange(DOWN, buff=0.15).move_to(UP * 0.6)
        else:
            end = txt("How a Neural Network Learns", 40, TEXT, weight=BOLD).move_to(DOWN * 0.2)
        self.play(FadeOut(VGroup(chips, arrows, center)), FadeOut(self.cap), run_time=T(0.8))
        fs = 22 if not PORTRAIT else 28
        footer = VGroup(txt("Created by", fs, MUTED).set_opacity(0.6),
                        txt("sujee.dev", fs, TEXT, weight=MEDIUM).set_opacity(0.75)).arrange(RIGHT, buff=0.14)
        footer[1].align_to(footer[0], DOWN)
        if PORTRAIT:
            footer.next_to(end, DOWN, buff=0.9)
        else:
            footer.move_to(DOWN * 3.45)
        self.play(FadeIn(end, shift=UP * 0.1), FadeIn(footer), run_time=T(0.8) if not PORTRAIT else 0.8)
        self.wait(1.4 if not PORTRAIT else 2.2)
        self.play(FadeOut(end), FadeOut(footer), run_time=0.8)
        self.mark("end")
        out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "tmp")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, f"events_{ORIENT}.json"), "w") as f:
            json.dump(self.events, f, indent=1)

    def fade_in_live(self, *mobs, rt=0.6):
        """FadeIn that works for always_redraw mobjects (fade a frozen copy, then swap)."""
        frozen = [m.copy().clear_updaters() for m in mobs]
        self.play(*[FadeIn(f, shift=DOWN * 0.08) for f in frozen], run_time=T(rt))
        self.remove(*frozen)
        self.add(*mobs)

    @staticmethod
    def _edge_pt(a, b):
        """Point on chip a's border facing chip b (approximate, via bounding box)."""
        d = b.get_center() - a.get_center()
        hw, hh = a.width / 2 + 0.08, a.height / 2 + 0.08
        t = min(hw / (abs(d[0]) + 1e-9), hh / (abs(d[1]) + 1e-9))
        return a.get_center() + d * t
