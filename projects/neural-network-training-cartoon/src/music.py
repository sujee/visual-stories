"""Procedural bouncy-cartoon backing track, synced to the scene's timeline events.

Usage: uv run python src/music.py workspace/tmp/events_landscape.json out.wav

Cartoon band language, everything synthesized here (no samples, no licensing):
  - intro: soft pad + music-box bells while the network is introduced
  - pass 1: the oom-pah band kicks in -- tuba bass on 1 and 3, offbeat "pah"
    stabs, bright plucked 8ths
  - first wrong guess: percussion joins (kick, rim, ticking woodblock)
  - wrong guesses: a little bent-note "wah wah waaah" trombone womp
  - backprop: a quick descending plucked run -- the error flowing backward
  - correct: bell run up + FM ding (the ta-da)
  - outro: the band thins back to plucks over the pad and resolves on a C add9.
Key: bright C major, 124 BPM. Deterministic (seeded rng, sox -R, two-pass
loudnorm), ends exactly with the video, -14 LUFS integrated / -2 dBTP.
"""
import json
import subprocess
import sys
import wave
import os

import numpy as np

SR = 48000
BPM = 124.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(11)

ev = json.load(open(sys.argv[1]))
out = sys.argv[2]
DUR = ev["end"] + 1.0
N = int(DUR * SR)

t_groove = ev.get("pass1", 8.0)
t_drums = ev.get("wrong1", t_groove + 10)
t_outro = ev.get("outro", ev["end"] - 10)
t_end = ev["end"]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def add(buf, start, sig):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


# chord loop (bright C major, square oom-pah changes): C6, F, G, C6 -- midi notes
CHORDS = [
    [48, 55, 64, 67, 72],
    [53, 60, 65, 69, 72],
    [55, 62, 67, 71, 74],
    [48, 55, 64, 67, 72],
]
ROOTS = [48, 53, 55, 48]      # C3 F3 G3 C3; the tuba voices these an octave down

pad = np.zeros(N)
bells = np.zeros(N)
tuba = np.zeros(N)
stabL = np.zeros(N)   # offbeat "pah" stabs, alternating sides
stabR = np.zeros(N)
pluck = np.zeros(N)
drums = np.zeros(N)
fx = np.zeros(N)

nbars = int(np.ceil(DUR / BAR)) + 1
for b in range(nbars):
    t0 = b * BAR
    if t0 > t_end:
        break
    ch = CHORDS[b % 4]

    # --- pad: detuned soft additive tones, slow crossfading swell
    n = int(BAR * 1.3 * SR)
    tt = np.arange(n) / SR
    e = np.minimum(tt / 0.8, 1.0)
    rel = tt - BAR
    e[rel > 0] = np.maximum(0.0, 1.0 - rel[rel > 0] / 0.9)
    sig = np.zeros(n)
    for m in ch:
        f = hz(m)
        for det in (-0.15, 0.15):
            ff = f * 2 ** (det / 12)
            for h, amp in ((1, 1.0), (2, 0.28), (3, 0.12), (4, 0.05)):
                sig += amp * np.sin(2 * np.pi * ff * h * tt + rng.uniform(0, 6.28))
    sig *= e * (1 + 0.12 * np.sin(2 * np.pi * 0.22 * tt))
    add(pad, t0, sig * 0.013)

    if t0 + BAR < t_groove - 0.2:
        # --- intro: music-box bell motif every other bar, rising
        if b % 2 == 0:
            for k, m in enumerate([84, 88, 91, 96] if b % 4 == 0 else [79, 84, 88, 91]):
                nb = int(1.6 * SR)
                tb = np.arange(nb) / SR
                f = hz(m)
                s = (np.sin(2 * np.pi * f * tb) + 0.35 * np.sin(2 * np.pi * 2.01 * f * tb)
                     + 0.18 * np.sin(2 * np.pi * 3.02 * f * tb))
                s *= np.exp(-tb * 3.2) * np.minimum(1, tb / 0.003)
                add(bells, t0 + k * 0.26, s * 0.032)
        continue

    # --- tuba: bouncy oom-pah bass, root on 1 and 3, fifth + octave pickups
    for bt, ln, semi in ((0, 1.15, 0), (2, 0.85, 0), (2.75, 0.4, 7), (3.5, 0.4, 12)):
        n = int(ln * BEAT * SR)
        tt = np.arange(n) / SR
        f = hz(ROOTS[b % 4] - 12 + semi)
        e = np.minimum(1, tt / 0.008) * np.exp(-tt * 2.8)
        s = (np.sin(2 * np.pi * f * tt) + 0.32 * np.sin(4 * np.pi * f * tt)
             + 0.14 * np.sin(6 * np.pi * f * tt))
        add(tuba, t0 + bt * BEAT, s * e * 0.15)

    # --- stabs: short "pah" chord stabs on the offbeats, alternating L/R
    if t0 <= t_outro + BAR:
        for bt, dst in ((1, stabL), (3, stabR)):
            n = int(0.16 * SR)
            tt = np.arange(n) / SR
            s = np.zeros(n)
            for m in (ch[2], ch[3], ch[4]):
                f = hz(m) * 2 ** (rng.uniform(-0.05, 0.05) / 12)
                s += np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt)
            e = np.minimum(1, tt / 0.004) * np.exp(-tt * 30)
            nz = rng.normal(0, 1, n) * np.exp(-tt * 120) * 0.12
            add(dst, t0 + bt * BEAT, (s + nz) * e * 0.05)

    # --- plucks: bright marimba-ish 8ths through the chord, an octave up
    pattern = [0, 2, 4, 2, 1, 3, 4, 2]
    for k, idx in enumerate(pattern):
        n = int(0.55 * SR)
        tt = np.arange(n) / SR
        f = hz(ch[idx] + 12)
        e = np.minimum(1, tt / 0.003) * np.exp(-tt * 8.5)
        s = (np.sin(2 * np.pi * f * tt) + 0.33 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 14)
             + 0.14 * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 22))
        vel = 0.85 + 0.15 * (k % 2 == 0)
        add(pluck, t0 + k * BEAT / 2, s * e * 0.045 * vel)

    if t0 + BAR < t_drums or t0 > t_outro + BAR:
        continue  # full percussion only between the first mistake and the outro

    # --- kick on 1 and the "and" of 2, rim on 2 and 4, woodblock ticking 8ths
    for bt in (0, 2.5):
        n = int(0.45 * SR)
        tt = np.arange(n) / SR
        f = 42 + 90 * np.exp(-tt * 28)
        ph = 2 * np.pi * np.cumsum(f) / SR
        add(drums, t0 + bt * BEAT, np.sin(ph) * np.exp(-tt * 7) * 0.42)
    for bt in (1, 3):
        n = int(0.18 * SR)
        tt = np.arange(n) / SR
        nz = rng.normal(0, 1, n)
        nz = nz - np.convolve(nz, np.ones(8) / 8, mode="same")
        body = np.sin(2 * np.pi * 210 * tt) * np.exp(-tt * 35)
        add(drums, t0 + bt * BEAT, (nz * 0.5 * np.exp(-tt * 20) + body * 0.35) * 0.30)
    for k in range(8):
        n = int(0.06 * SR)
        tt = np.arange(n) / SR
        s = (np.sin(2 * np.pi * 1650 * tt) * np.exp(-tt * 70)
             + 0.6 * np.sin(2 * np.pi * 2350 * tt) * np.exp(-tt * 85))
        amp = 0.03 if k % 2 else 0.02
        add(drums, t0 + k * BEAT / 2 + (0.01 if k % 2 else 0), s * amp)


# --- wrong guesses: bent-note "wah wah waaah" trombone womp, each lower than the last
def womp(t, notes, amp=0.07):
    for k, (m, dur) in enumerate(notes):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        f = hz(m) * 2 ** (-1.7 * (k + 1) * tt / dur / 12)          # each note slides down
        vib = 1 + (0.004 + 0.003 * k) * np.sin(2 * np.pi * 6.0 * tt)  # growing wobble
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        s = np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.28 * np.sin(3 * ph)
        e = np.minimum(1, tt / 0.02) * np.exp(-tt * (2.2 if k == 2 else 4.5))
        add(fx, t + (0.0, 0.4, 0.8)[k], s * e * amp)


if "wrong1" in ev:
    womp(ev["wrong1"], ((58, 0.34), (56, 0.34), (52, 0.8)))
if "wrong2" in ev:
    womp(ev["wrong2"], ((56, 0.34), (54, 0.34), (50, 0.8)))

# --- backprop: quick descending plucked run -- the error flows backward
for key in ("backprop1", "backprop2"):
    if key in ev:
        t = ev[key]
        for k in range(8):
            m = 88 - 3 * k - (2 if key == "backprop2" else 0)
            n = int(0.5 * SR)
            tt = np.arange(n) / SR
            f = hz(m)
            e = np.minimum(1, tt / 0.002) * np.exp(-tt * 10)
            s = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 18)
            add(fx, t + k * 0.06, s * e * 0.05)

# --- correct answer: bell run up, FM ding, warm low pluck -- the ta-da
tc = ev.get("correct")
if tc is not None:
    for k, m in enumerate((72, 76, 79, 84)):
        n = int(0.5 * SR)
        tt = np.arange(n) / SR
        f = hz(m)
        e = np.minimum(1, tt / 0.003) * np.exp(-tt * 8)
        s = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 16)
        add(fx, tc + k * 0.075, s * e * 0.05)
    for m, dly, g in ((91, 0.34, 0.05), (96, 0.38, 0.06)):
        n = int(2.2 * SR)
        tt = np.arange(n) / SR
        f = hz(m)
        mod = np.sin(2 * np.pi * f * 3.01 * tt) * 1.3 * np.exp(-tt * 3)
        s = np.sin(2 * np.pi * f * tt + mod) * np.exp(-tt * 2.2) * np.minimum(1, tt / 0.003)
        add(fx, tc + dly, s * g)
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    f = hz(36)
    s = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt))
    add(fx, tc, s * np.exp(-tt * 4) * np.minimum(1, tt / 0.006) * 0.08)

# final resolving chord (C add9) under the last seconds
n = int(3.5 * SR)
tt = np.arange(n) / SR
fin = np.zeros(n)
for m in (36, 48, 55, 64, 67, 72, 84):
    fin += np.sin(2 * np.pi * hz(m) * tt) * np.exp(-tt * 0.9)
add(pad, max(0, t_end - 3.2), fin * 0.032)


def stereo(x, width=0.0, delay_ms=0.0):
    d = int(delay_ms * SR / 1000)
    L = x.copy()
    R = np.concatenate([np.zeros(d), x[:-d]]) if d else x.copy()
    return np.stack([L * (1 - width), R * (1 + width)], axis=1)


wet = (stereo(pad, 0, 11) + stereo(bells, 0.2, 9) + stereo(pluck, 0.12, 6)
       + stereo(fx, 0, 5) + stereo(stabL, -0.35) + stereo(stabR, 0.35))
dry = stereo(tuba, 0.1) + stereo(drums)

# sox -R (repeatable mode) keeps its dither noise deterministic, so the same source gives the same audio.
tmp = os.path.join(os.path.dirname(out) or ".", "_music_tmp")
os.makedirs(tmp, exist_ok=True)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


write_wav(f"{tmp}/wet.wav", wet)
write_wav(f"{tmp}/dry.wav", dry)
subprocess.run(["sox", "-R", f"{tmp}/wet.wav", f"{tmp}/wet_rev.wav", "reverb", "55", "50", "90", "100", "18"], check=True)
fade_out = 2.5
subprocess.run(["sox", "-R", "-m", f"{tmp}/wet_rev.wav", f"{tmp}/dry.wav", f"{tmp}/mix.wav",
                "lowpass", "9000", "trim", "0", f"{t_end:.3f}",       # end exactly with the video,
                "fade", "t", "1.5", f"{t_end:.3f}", f"{fade_out}"], check=True)  # fully faded out
# Loudness-normalize to -14 LUFS integrated, true peak <= -1 dBTP (see AGENTS.md).
# Two passes: measure, then apply linearly. The peak target leaves headroom for AAC encoding.
LN = "loudnorm=I=-14:TP=-2:LRA=11"
probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", f"{tmp}/mix.wav", "-af", LN + ":print_format=json",
                        "-f", "null", "-"], check=True, capture_output=True, text=True).stderr
m = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
LN += (f":measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
       f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/mix.wav", "-af", LN, "-ar", str(SR), out], check=True)
print("wrote", out, f"{DUR:.1f}s")
