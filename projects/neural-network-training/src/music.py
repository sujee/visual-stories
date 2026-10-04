"""Procedural chill-electronic backing track, synced to the scene's timeline events.

Usage: uv run python src/music.py workspace/tmp/events_landscape.json out.wav
Structure: soft pad intro -> bass + arp at pass 1 -> light drums -> chime on "correct"
-> resolve and fade at "end". Everything is synthesized here (no samples, no licensing).
"""
import json
import subprocess
import sys
import wave
import os

import numpy as np

SR = 48000
BPM = 92.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(5)

ev = json.load(open(sys.argv[1]))
out = sys.argv[2]
DUR = ev["end"] + 1.0
N = int(DUR * SR)
t_all = np.arange(N) / SR


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def env_adsr(n, a, r, sustain_len):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na) if na else 1
    ns = min(n, na + int(sustain_len * SR))
    if nr:
        tail = e[ns:ns + nr]
        e[ns:ns + nr] = np.linspace(1, 0, len(tail))
    e[ns + nr:] = 0
    return e


def add(buf, start, sig):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


# chord progression (A minor): Am9, Fmaj7, Cmaj7, G6/B  -- midi notes
CHORDS = [
    [57, 60, 64, 67, 71],
    [53, 57, 60, 64, 69],
    [48, 55, 59, 64, 67],
    [47, 55, 59, 62, 64],
]
ROOTS = [45, 41, 48, 43]

pad = np.zeros(N)
bass = np.zeros(N)
arp = np.zeros(N)
drums = np.zeros(N)
fx = np.zeros(N)

t_groove = ev.get("pass1", 8.0)
t_drums = ev.get("wrong1", t_groove + 10)
t_outro = ev.get("outro", DUR - 10)
t_end = ev["end"]

nbars = int(np.ceil(DUR / BAR)) + 1
for b in range(nbars):
    t0 = b * BAR
    if t0 > t_end:
        break
    ch = CHORDS[b % 4]
    # --- pad: detuned soft saw-ish additive tones, slow swell
    n = int(BAR * 1.25 * SR)
    tt = np.arange(n) / SR
    e = env_adsr(n, 0.9, 1.2, BAR * 0.95 - 0.9)
    sig = np.zeros(n)
    for m in ch:
        f = hz(m)
        for det in (-0.12, 0.12):
            ff = f * 2 ** (det / 12)
            for h, amp in ((1, 1.0), (2, 0.28), (3, 0.12), (4, 0.05)):
                sig += amp * np.sin(2 * np.pi * ff * h * tt + rng.uniform(0, 6.28))
    sig *= e * (1 + 0.15 * np.sin(2 * np.pi * 0.25 * tt))
    add(pad, t0, sig * 0.018)

    if t0 + BAR < t_groove:
        continue
    # --- bass: round sine with a touch of 2nd harmonic, on beats 1 and 3 (+ pickup)
    for bt, ln in ((0, 1.6), (2, 1.2), (3.5, 0.45)):
        n = int(ln * BEAT * SR)
        tt = np.arange(n) / SR
        f = hz(ROOTS[b % 4] - 12 if bt != 3.5 else ROOTS[b % 4])
        e = np.minimum(1, tt / 0.01) * np.exp(-tt * 2.2)
        s = np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)
        add(bass, t0 + bt * BEAT, s * e * 0.16)
    # --- arp: plucked 8th notes through chord tones, an octave up
    pattern = [0, 2, 4, 2, 1, 3, 4, 3]
    for k, idx in enumerate(pattern):
        n = int(0.9 * SR)
        tt = np.arange(n) / SR
        f = hz(ch[idx] + 12)
        e = np.minimum(1, tt / 0.004) * np.exp(-tt * 6.5)
        s = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) * np.exp(-tt * 12)
             + 0.12 * np.sin(6 * np.pi * f * tt) * np.exp(-tt * 20))
        vel = 0.75 + 0.25 * (k % 2 == 0)
        add(arp, t0 + k * BEAT / 2, s * e * 0.05 * vel)

    if t0 + BAR < t_drums or t0 > t_outro + BAR:
        continue
    # --- drums: soft kick, rim-ish snare, gentle hats
    for bt in (0, 2.5):
        n = int(0.5 * SR)
        tt = np.arange(n) / SR
        f = 45 + 80 * np.exp(-tt * 30)
        ph = 2 * np.pi * np.cumsum(f) / SR
        add(drums, t0 + bt * BEAT, np.sin(ph) * np.exp(-tt * 7) * 0.55)
    for bt in (1, 3):
        n = int(0.25 * SR)
        tt = np.arange(n) / SR
        nz = rng.normal(0, 1, n)
        nz = nz - np.convolve(nz, np.ones(8) / 8, mode="same")  # crude highpass
        body = np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 30)
        add(drums, t0 + bt * BEAT, (nz * 0.35 * np.exp(-tt * 22) + body * 0.3) * 0.35)
    for k in range(8):
        n = int(0.08 * SR)
        tt = np.arange(n) / SR
        nz = np.diff(rng.normal(0, 1, n + 1))
        amp = 0.05 if k % 2 else 0.028
        add(drums, t0 + k * BEAT / 2 + (0.012 if k % 2 else 0), nz * np.exp(-tt * 60) * amp)

# --- chime on the correct answer: bell-like FM partials, A major arpeggio lift
tc = ev.get("correct")
if tc is not None:
    for k, m in enumerate([81, 85, 88, 93]):
        n = int(2.5 * SR)
        tt = np.arange(n) / SR
        f = hz(m)
        mod = np.sin(2 * np.pi * f * 3.5 * tt) * 1.2 * np.exp(-tt * 3)
        s = np.sin(2 * np.pi * f * tt + mod) * np.exp(-tt * 2.4) * np.minimum(1, tt / 0.003)
        add(fx, tc + k * 0.09, s * 0.06)

# soft low "thud" on wrong answers (subtle)
for key in ("wrong1", "wrong2"):
    if key in ev:
        n = int(0.8 * SR)
        tt = np.arange(n) / SR
        s = np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 5) + 0.5 * np.sin(2 * np.pi * 103.8 * tt) * np.exp(-tt * 5)
        add(fx, ev[key], s * 0.06)

# final resolving chord (A minor add9) at end of outro
n = int(3.5 * SR)
tt = np.arange(n) / SR
fin = np.zeros(n)
for m in (45, 57, 64, 67, 71, 72):
    fin += np.sin(2 * np.pi * hz(m) * tt) * np.exp(-tt * 0.9)
add(pad, max(0, t_end - 3.2), fin * 0.03)


def stereo(x, width=0.0, delay_ms=0.0):
    d = int(delay_ms * SR / 1000)
    L = x.copy()
    R = np.concatenate([np.zeros(d), x[:-d]]) if d else x.copy()
    return np.stack([L * (1 - width), R * (1 + width)], axis=1)


wet = stereo(pad, 0, 11) + stereo(arp, 0.15, 7) + stereo(fx, 0, 5)
dry = stereo(bass) + stereo(drums, 0, 0)

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
