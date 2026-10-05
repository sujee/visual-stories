"""Soundtrack for the Short: 30 s, same synths as music.py, seeded.

    python src/short_music.py <out.wav>

Silence at 11.7-12 s, then the drop at 12 s ("IT GOT BIG."). render.sh normalizes loudness afterwards.
"""
import numpy as np
from scipy.signal import butter, lfilter, fftconvolve
from scipy.io import wavfile
import sys

SR = 44100
DUR = 30.0
N = int(SR * DUR)
BEAT = 0.5
rng = np.random.default_rng(7)

L = np.zeros(N)
R = np.zeros(N)
send_L = np.zeros(N)  # reverb send
send_R = np.zeros(N)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, fc, order=2):
    b, a = butter(order, min(fc, SR * 0.45) / (SR / 2), 'low')
    return lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), 'high')
    return lfilter(b, a, x)


def saw(freq, n, phase=0.0):
    t = np.arange(n) / SR
    return 2.0 * ((t * freq + phase) % 1.0) - 1.0


def env(n, a=0.005, d=0.1, s=0.7, r=0.05):
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = max(1, min(na, n)); e[:na] = np.linspace(0, 1, na)
    nd = max(1, min(nd, n - na)); e[na:na + nd] = np.linspace(1, s, nd)
    nr = max(1, min(nr, n)); e[-nr:] *= np.linspace(1, 0, nr)
    return e


def place(sig, t0, gain=1.0, pan=0.0, send=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    sig = sig[:N - i]
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    L[i:i + len(sig)] += sig * gain * gl
    R[i:i + len(sig)] += sig * gain * gr
    if send:
        send_L[i:i + len(sig)] += sig * gain * gl * send
        send_R[i:i + len(sig)] += sig * gain * gr * send


def in_any(t, ranges):
    return any(a <= t < b for a, b in ranges)


# --- harmony: Am F C G, one chord per bar (2s), aligned so bar at t=30 is Am
CHORDS = [
    dict(root=33, pad=[57, 60, 64, 69]),   # Am
    dict(root=29, pad=[57, 60, 65, 69]),   # F
    dict(root=36, pad=[55, 60, 64, 67]),   # C
    dict(root=31, pad=[55, 59, 62, 67]),   # G
]


def chord_at(t):
    if t >= 28:
        return CHORDS[0]
    return CHORDS[int(np.floor((t - 12) / 2)) % 4]


FULL = [(12, 28)]
KICK = [(4, 11.5)] + FULL

# --- pad: detuned saws, one chord per bar
for bar in range(15):
    t0 = bar * 2.0
    if t0 > 28:
        continue
    dur = 2.5 if t0 == 28 else 2.0
    ch = chord_at(t0)
    n = int((dur + 0.6) * SR)
    sig = np.zeros(n)
    for m in ch['pad'] + [ch['root'] + 24]:
        f = mtof(m)
        for det in (-0.12, 0.0, 0.12):
            sig += saw(f * 2 ** (det / 12), n, rng.random())
    cutoff = 1400 if not in_any(t0, [(62, 78)]) else 2200
    sig = lp(sig, cutoff) * env(n, a=0.25, d=0.5, s=0.85, r=0.6)
    g = 0.026
    if t0 < 4:
        g *= 0.5 + t0 / 8
    if t0 >= 28:
        sig *= np.linspace(1, 0, n) ** 1.5
    place(sig, t0, g, pan=0.0, send=0.8)

# --- arpeggio: 16ths over chord tones
ARP_PAT = [0, 1, 2, 3, 2, 1, 0, 2, 0, 1, 2, 3, 2, 3, 1, 2]
step = BEAT / 4
for k in range(int(28 / step)):
    t0 = k * step
    ch = chord_at(t0)
    notes = ch['pad']
    m = notes[ARP_PAT[k % 16]] + 12
    n = int(0.2 * SR)
    f = mtof(m)
    sig = np.sign(np.sin(2 * np.pi * f * np.arange(n) / SR)) * 0.6 + saw(f, n) * 0.4
    if t0 < 12:
        cutoff = 400 + t0 / 12 * 3200
    elif 62 <= t0 < 78:
        cutoff = 1800 + (t0 - 62) / 16 * 2500
    else:
        cutoff = 3200
    sig = lp(sig, cutoff) * env(n, a=0.002, d=0.12, s=0.0, r=0.02)
    g = 0.05 * (1.0 if k % 4 == 0 else 0.75) * (0.6 if t0 < 6 else 0.8 if t0 < 12 else 1.0)
    place(sig, t0, g, pan=(0.35 if k % 2 else -0.35), send=0.35)
    # dotted 8th echo
    place(sig, t0 + 0.375, g * 0.35, pan=(-0.5 if k % 2 else 0.5), send=0.3)

# --- kick
def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t * 35)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) + 0.3 * np.exp(-t * 300) * rng.standard_normal(n) * 0.3


K = kick()
for b in range(240):
    t0 = b * BEAT
    if in_any(t0, KICK):
        place(K, t0, 0.5 if t0 < 12 else 0.8)
place(K, 28, 0.9)

# --- clap on 2 & 4
def clap():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    e = np.exp(-t * 18)
    for off in (0.0, 0.011, 0.022):
        e = np.maximum(e, (t >= off) * np.exp(-(t - off) * 120) * (t < off + 0.01))
    x = noise * e
    b, a = butter(2, [900 / (SR / 2), 4000 / (SR / 2)], 'band')
    return lfilter(b, a, x)


C = clap()
for b in range(240):
    t0 = b * BEAT
    if b % 2 == 1 and in_any(t0, FULL):
        place(C, t0, 0.35, send=0.4)

# --- hats
def hat(dec):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t * dec)


HO, HC = hat(18), hat(70)
for k in range(int(120 / (BEAT / 4))):
    t0 = k * BEAT / 4
    if k % 4 == 2 and in_any(t0, KICK):
        place(HO, t0, 0.12, pan=0.2)
    elif in_any(t0, FULL) and k % 4 != 2:
        place(HC, t0, 0.05 if k % 2 else 0.08, pan=-0.25)

# --- bass: offbeat 8ths, root
for k in range(int(120 / (BEAT / 2))):
    t0 = k * BEAT / 2
    if not in_any(t0, FULL):
        continue
    ch = chord_at(t0)
    m = ch['root'] + (12 if k % 2 else 0)
    n = int(0.24 * SR)
    f = mtof(m)
    sig = saw(f, n) + saw(f * 1.005, n) + 0.6 * np.sin(2 * np.pi * f / 2 * np.arange(n) / SR)
    sig = lp(sig, 900) * env(n, a=0.003, d=0.15, s=0.5, r=0.03)
    place(sig, t0, 0.16)
# final sub
n = int(2.5 * SR)
place(lp(saw(mtof(33), n) + np.sin(2 * np.pi * mtof(21) * np.arange(n) / SR), 500)
      * np.exp(-np.arange(n) / SR * 0.6) * env(n, 0.01, 0.1, 1, 1.5), 28, 0.18)

# --- lead melody (beats, midi) 4-bar phrases
PHRASE_A = [(1.5, 76), (0.5, 74), (1, 72), (1, 69),
            (1.5, 72), (0.5, 74), (1, 76), (1, 77),
            (1.5, 79), (0.5, 76), (1, 74), (1, 72),
            (2, 74), (1, 71), (1, 74)]
PHRASE_B = [(1, 81), (1, 79), (1, 76), (1, 72),
            (1.5, 77), (0.5, 76), (2, 72),
            (1, 76), (1, 79), (2, 84),
            (1.5, 83), (0.5, 81), (1, 79), (1, 74)]


def lead_note(m, dur):
    n = int((dur + 0.1) * SR)
    t = np.arange(n) / SR
    f = mtof(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t * 3, 0, 1))
    ph = np.cumsum(f) / SR
    sig = (2 * (ph % 1) - 1) + (2 * ((ph * 1.006) % 1) - 1) + 0.5 * np.sign(np.sin(2 * np.pi * ph * 0.5))
    return lp(sig, 2800) * env(n, a=0.01, d=0.2, s=0.75, r=0.08)


def play_phrase(ph, t0):
    t = t0
    for beats, m in ph:
        d = beats * BEAT
        s = lead_note(m, d * 0.95)
        place(s, t, 0.05, pan=0.05, send=0.5)
        for i, g in enumerate((0.3, 0.15, 0.07), start=1):  # dotted-8th delay
            place(s, t + 0.375 * i, 0.05 * g, pan=(0.6 if i % 2 else -0.6), send=0.4)
        t += d


for i, t0 in enumerate([12, 20]):
    play_phrase([PHRASE_A, PHRASE_B][i % 2], t0)
for i, t0 in enumerate([]):
    play_phrase([PHRASE_A, PHRASE_B][i % 2], t0)

# --- risers + impacts
def riser(t0, dur):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    chunk = n // 32
    for c in range(32):
        seg = x[c * chunk:(c + 1) * chunk]
        out[c * chunk:(c + 1) * chunk] = hp(seg, 300 + c / 32 * 6000)
    out *= np.linspace(0, 1, n) ** 2
    place(out, t0, 0.12, send=0.6)


riser(9, 2.75)
for ti in (12, 28):
    n = int(3 * SR)
    t = np.arange(n) / SR
    place(hp(rng.standard_normal(n), 3000) * np.exp(-t * 1.5), ti, 0.12, send=0.6)

# --- sidechain pump on everything but drums: approximate by ducking melodic bus
#     (simple: duck whole mix lightly on kick beats; kick re-added after)
tt = np.arange(N) / SR
duck = np.ones(N)
ph = (tt % BEAT) / BEAT
active = np.zeros(N, bool)
for a, b in KICK:
    active |= (tt >= a) & (tt < b)
duck[active] = 1 - 0.35 * np.exp(-ph[active] * 9)

# --- reverb
ir_n = int(2.6 * SR)
ir_t = np.arange(ir_n) / SR
irL = rng.standard_normal(ir_n) * np.exp(-ir_t * 2.6)
irR = rng.standard_normal(ir_n) * np.exp(-ir_t * 2.6)
irL, irR = lp(irL, 5000), lp(irR, 5000)
revL = fftconvolve(send_L, irL)[:N] * 0.06
revR = fftconvolve(send_R, irR)[:N] * 0.06

L = (L + revL) * duck
R = (R + revR) * duck
# dramatic silence right before the drop
gate = np.ones(N)
gate[int(11.7 * SR):int(12 * SR)] = 0
a, b = int(11.6 * SR), int(11.7 * SR); gate[a:b] = np.linspace(1, 0, b - a)
L *= gate; R *= gate

# master: fade, soft clip, normalize
fade = np.ones(N)
fade[-int(1.5 * SR):] = np.linspace(1, 0, int(1.5 * SR)) ** 1.5
fade[:int(0.05 * SR)] = np.linspace(0, 1, int(0.05 * SR))
st = np.stack([L, R], 1) * fade[:, None]
st = hp(st.T, 25).T
st /= np.max(np.abs(st)) + 1e-9
st = np.tanh(st * 1.4) / np.tanh(1.4)
st *= 0.89
wavfile.write(sys.argv[1], SR, (st * 32767).astype(np.int16))
print('peak', np.max(np.abs(st)), 'rms', np.sqrt(np.mean(st ** 2)))
