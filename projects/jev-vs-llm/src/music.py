"""Procedural minimal modern piano, synced to the scene's timeline events.

Usage: uv run python src/music.py workspace/tmp/events_landscape.json out.wav
Soft "felt" piano, 80 BPM, Cmaj7 - Am7 - Fmaj7 - Gsus, kept simple and level so it sits behind the
visuals: held chords until "groove", then a gentle repeating broken-chord pattern, back to held
chords from "outro", and a last Cmaj7 that rings out at "end". Accents are single soft notes: one on
each section card ("sec1", ...) and a high chime on "jev_hit". The piano is synthesized here
(warm additive partials, slow decay): no samples, no licensing.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

SR = 48000
BPM = 80.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(7)

ev = json.load(open(sys.argv[1]))
out = sys.argv[2]
DUR = ev["end"] + 1.0
N = int(DUR * SR)

t_groove = ev.get("groove", 8.0)
t_outro = ev.get("outro", DUR - 10)
t_end = ev["end"]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def add(buf, start, sig):
    i = int(round(start * SR))
    if i >= len(buf) or i + len(sig) <= 0:
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def piano(midi, dur, vel=0.5):
    """A soft felt-piano note: few, quickly fading upper partials, a slow body decay, soft attack."""
    f = hz(midi)
    tail = 0.8
    n = int((dur + tail) * SR)
    t = np.arange(n) / SR
    base = 0.45 + f / 900.0
    sig = np.zeros(n)
    for k in range(1, 6):
        fk = k * f * np.sqrt(1 + 0.0003 * k * k)
        amp = (0.38 ** (k - 1)) / k
        dec = base * (1 + 1.0 * (k - 1))
        env = 0.55 * np.exp(-t * dec * 1.8) + 0.45 * np.exp(-t * dec * 0.3)
        for det in (-0.0004, 0.0004):
            sig += 0.5 * amp * env * np.sin(2 * np.pi * fk * (1 + det) * t + rng.uniform(0, 6.28))
    sig *= np.minimum(1, t / 0.012)               # felt: a softer attack than a bare hammer
    off = int(dur * SR)
    if off < n:
        sig[off:] *= np.exp(-(t[off:] - dur) / (tail / 4))
    return sig * vel


P = np.zeros(N)
FX = np.zeros(N)

# Cmaj7 - Am7 - Fmaj7 - Gsus: (bass, upper voicing)
CHORDS = [(36, [55, 59, 64, 67]), (33, [55, 60, 64, 67]), (29, [57, 60, 64, 69]), (31, [55, 60, 62, 67])]
CELL = [0, 2, 1, 3, 2, 1, 3, 2]   # the broken-chord pattern, eighth notes, through the upper voicing

nbars = int(np.ceil(t_end / BAR)) + 1
for b in range(nbars):
    t0 = b * BAR
    if t0 >= t_end - 4.0:          # leave room for the last chord
        break
    bass, upper = CHORDS[b % 4]
    add(P, t0, piano(bass, BAR * 0.98, 0.42))
    add(P, t0, piano(bass + 12, BAR * 0.98, 0.22))
    if t_groove <= t0 < t_outro:
        for k, idx in enumerate(CELL):
            add(P, t0 + k * BEAT / 2, piano(upper[idx], BEAT * 0.9, 0.26 if k % 2 == 0 else 0.21))
    else:   # held chord, softly rolled
        for i, m in enumerate(upper):
            add(P, t0 + 0.05 + i * 0.06, piano(m, BAR * 0.95, 0.24))


def q8(t):
    """Quantize an accent to the next eighth note, so it lands on the pulse."""
    return np.ceil(t / (BEAT / 2) - 1e-6) * (BEAT / 2)


# one soft high note on each section card, a little higher each time
for i, key in enumerate(sorted(k for k in ev if k.startswith("sec"))):
    add(FX, q8(ev[key]), piano([76, 79, 81, 83, 84, 86][i % 6], BEAT * 2, 0.30))

# a gentle chime when Jev answers: a high fifth
if "jev_hit" in ev:
    add(FX, q8(ev["jev_hit"]), piano(84, BEAT * 2, 0.26))
    add(FX, q8(ev["jev_hit"]) + BEAT / 2, piano(91, BEAT * 2, 0.22))

# the last chord: Cmaj7, rolled, ringing out with the video
tc = max(0.0, t_end - 3.6)
for i, m in enumerate([36, 48, 55, 59, 64, 67, 71]):
    add(P, tc + i * 0.07, piano(m, 3.4, 0.36))


def stereo(x, pan):
    """Constant-power pan, -1 (left) .. 1 (right)."""
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


mix = stereo(P, 0.0) + stereo(FX, 0.2) * 0.8

# sox -R (repeatable mode) keeps its dither noise deterministic, so the same source gives the same audio.
tmp = os.path.join(os.path.dirname(out) or ".", "_music_tmp")
os.makedirs(tmp, exist_ok=True)


def write_wav(path, x):
    x = np.clip(x / max(1.0, np.abs(x).max() * 1.05), -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


write_wav(f"{tmp}/dry.wav", mix)
fade_out = 2.5
subprocess.run(["sox", "-R", f"{tmp}/dry.wav", f"{tmp}/mix.wav",
                "reverb", "50", "40", "90", "100", "20",          # a soft, spacious room
                "lowpass", "5000",                                 # felt piano: no sharp highs
                "trim", "0", f"{t_end:.3f}",                       # end exactly with the video,
                "fade", "t", "1.0", f"{t_end:.3f}", f"{fade_out}"], check=True)  # fully faded out
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
