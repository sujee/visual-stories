// The promo soundtrack: house, 120 BPM. Four-on-the-floor kick with claps, off-beat open hats, chord stabs, a sub
// bass and a plucked melody, over Am7 - Fmaj7 - Cmaj7 - G7.
//
//   node src/promo/music.mjs --duration 42.83 [--cues JSON] [--out workspace/tmp/music_promo.wav] [--lufs -14]
//
//   0-drop        pads and a riser, no drums
//   drop-stop     the beat; the plucked melody joins on the second bar
//   stop          the stop (<eos>): a hit and a held chord, a lighter kick until the outro
//   outro-        a hit, the final chord and a few falling plucks under the title card
//
// The sections start on the promo's cuts, in seconds: --cues '{"drop":5,"stop":31.58,"outro":36.58}' (render.sh passes
// them from `capture.mjs --print-cues`, so they follow the promo's pacing). Synthesized here, deterministic (seeded rng),
// no dependencies. Normalized with a two-pass ffmpeg loudnorm to about -14 LUFS integrated, true peak <= -1 dBTP in the encoded video
// (see AGENTS.md).
import { spawnSync } from 'node:child_process';
import { writeFileSync, mkdtempSync, rmSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const DUR = +arg('duration', 42.83);
const OUT = resolve(arg('out', 'workspace/tmp/music_promo.wav'));
const LUFS = +arg('lufs', -14);
const { drop: DROP, stop: STOP, outro: OUTRO } = JSON.parse(arg('cues', '{"drop":5,"stop":31.58,"outro":36.58}'));
const SR = 48000, N = Math.round(DUR * SR);
const L = new Float64Array(N), R = new Float64Array(N), VL = new Float64Array(N), VR = new Float64Array(N);   // dry, reverb send
const DUCK = new Float64Array(N), MUS = { L: new Float64Array(N), R: new Float64Array(N) };   // tonal parts, ducked by the kick

let seed = 17;                                             // mulberry32: same numbers every run
const rnd = () => { seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const hz = m => 440 * 2 ** ((m - 69) / 12);
function voice(t, len, fn, pan = 0, send = .25, duck = false) {
  const i0 = Math.round(t * SR), lg = Math.cos((pan + 1) * Math.PI / 4), rg = Math.sin((pan + 1) * Math.PI / 4), dl = duck ? MUS.L : L, dr = duck ? MUS.R : R;
  for (let i = 0; i < len * SR; i++) { const j = i0 + i; if (j < 0 || j >= N) continue; const v = fn(i / SR); dl[j] += v * lg; dr[j] += v * rg; VL[j] += v * lg * send; VR[j] += v * rg * send; }
}
const env = (s, len, att, rel) => Math.min(1, s / att) * (s > len ? Math.exp(-(s - len) / rel) : 1);

// ---------------------------------------------------------------- instruments
function kick(t, g = 1, punch = 1) {
  let ph = 0; voice(t, .45, s => { ph += 2 * Math.PI * (45 + 100 * punch * Math.exp(-s / .03)) / SR; return g * .8 * Math.sin(ph) * Math.exp(-s / .16); }, 0, 0);
  const i0 = Math.round(t * SR); for (let i = 0; i < .3 * SR && i0 + i < N; i++) DUCK[i0 + i] = Math.max(DUCK[i0 + i], g * Math.exp(-i / SR / .1));
}
function noise(t, len, decay, g, hp, pan = 0, send = .2) { let lp = 0; voice(t, len, s => { const n = rnd() * 2 - 1; lp += (n - lp) * hp; return g * (n - lp) * Math.min(1, s / .001) * Math.exp(-s / decay); }, pan, send); }
const hat = (t, g, open = false) => noise(t, open ? .3 : .08, open ? .09 : .016, g, .4, .25);
const clap = (t, g) => { for (const d of [0, .012, .024]) noise(t + d, .25, d ? .012 : .08, .22 * g, .1, -.1, .25); };   // three quick bursts
function saw(t, m, len, g, cut, o = {}) {                  // band-limited saw (additive), its brightness set by `cut`
  const f = hz(m) * (1 + (o.det || 0)), n = Math.max(1, Math.min(40, Math.floor(cut / f)));
  voice(t, len + (o.rel ?? .05) * 4, s => { let v = 0; for (let k = 1; k <= n; k++) v += Math.sin(2 * Math.PI * f * k * s) / k; return g * v * env(s, len, o.att ?? .005, o.rel ?? .05) * (o.pluck ? Math.exp(-s / o.pluck) : 1); }, o.pan || 0, o.send ?? .25, true);
}
const sub = (t, m, len, g) => { const f = hz(m); voice(t, len + .1, s => g * Math.sin(2 * Math.PI * f * s) * env(s, len, .01, .03), 0, 0, true); };
const pluck = (t, m, g, pan = 0, dec = .12) => saw(t, m, .02, g, 3500, { pluck: dec, rel: .1, pan, send: .45 });

// ---------------------------------------------------------------- the tune
const BEAT = 60 / 120, BAR = 4 * BEAT;
const PROG = [[45, [57, 60, 64, 67]], [41, [57, 60, 64, 65]], [48, [55, 60, 64, 71]], [43, [55, 59, 62, 65]]];   // Am7 Fmaj7 Cmaj7 G7
const M1 = [
  [[0, 76, .5], [.5, 72, .5], [1, 76, .5], [1.5, 79, 1], [2.5, 76, .5], [3, 72, .5], [3.5, 74, .5]],
  [[0, 77, .5], [.5, 72, .5], [1, 77, .5], [1.5, 81, 1], [2.5, 79, .5], [3, 77, 1]],
  [[0, 76, .5], [.5, 79, .5], [1, 84, 1], [2, 79, .5], [2.5, 76, .5], [3, 72, 1]],
  [[0, 74, .5], [.5, 71, .5], [1, 67, .5], [1.5, 71, 1], [2.5, 74, 1.5]]];
const M2 = [M1[0], M1[1], M1[2], [[0, 74, 1], [1, 79, .5], [1.5, 77, .5], [2, 76, .5], [2.5, 74, .5], [3, 71, 1]]];

// intro: wide pads and a riser into the drop
const introBars = Math.max(1, Math.round(DROP / BAR)), iBar = DROP / introBars;
for (let b = 0; b < introBars; b++) PROG[b % 4][1].forEach((m, k) => saw(b * iBar, m, iBar, .05, 1200, { att: .5, rel: .4, det: .003 * (k - 1.5), pan: -.4 + k * .27, send: .5 }));
for (let i = Math.round(Math.max(0, DROP - 2) * SR); i < DROP * SR; i++) { const u = (i / SR - DROP + 2) / 2; L[i] += .08 * u * u * (rnd() * 2 - 1); R[i] += .08 * u * u * (rnd() * 2 - 1); }

// main: from the drop to the stop
const nBars = Math.floor((STOP - DROP) / BAR);
for (let b = 0; b < nBars + 1; b++) {
  const t0 = DROP + b * BAR, [root, ch] = PROG[b % 4], mel = (Math.floor(b / 4) % 2 ? M2 : M1)[b % 4], first = b < 4;
  const ev = (beat, fn) => { const t = t0 + beat * BEAT; if (t < STOP - .03) fn(t); };
  for (const beat of [0, 1, 2, 3]) ev(beat, t => kick(t, .85));
  ev(1, t => clap(t, .8)); ev(3, t => clap(t, .8));
  for (const beat of [.5, 1.5, 2.5, 3.5]) ev(beat, t => hat(t, .1, true));   // off-beat open hats
  for (let e = 0; e < 16; e++) ev(e / 4, t => hat(t, e % 2 ? .04 : .025));
  for (const beat of [.5, 1.75, 3]) ev(beat, t => ch.forEach((m, k) => saw(t, m, BEAT * .3, .045, 1800, { rel: .06, det: .003 * (k - 1.5), pan: -.3 + k * .2, send: .45 })));   // chord stabs
  for (const beat of [0, .75, 2, 2.75]) ev(beat, t => sub(t, root - 12, BEAT * .5, .4));
  if (b >= 1) for (const [beat, m, len] of mel) ev(beat, t => pluck(t, m, first ? .1 : .13, .15, .18));
}
// the stop: a hit and a held chord, a lighter kick; then the outro: a hit, the final chord and falling plucks
kick(STOP, 1); noise(STOP, 1.5, .4, .15, .08, 0, .5);
const [r0, c0] = PROG[1];
c0.forEach((m, k) => saw(STOP, m, OUTRO - STOP - .3, .05, 1500, { att: .3, rel: .5, det: .004 * (k - 1.5), pan: -.4 + k * .27, send: .6 }));
sub(STOP, r0 - 12, OUTRO - STOP - .5, .3);
for (let t = STOP + 2 * BEAT; t < OUTRO - .2; t += 2 * BEAT) kick(t, .5, .8);
kick(OUTRO, .8); noise(OUTRO, 1.5, .45, .1, .08, 0, .5);
[48, 55, 64, 67, 71, 76].forEach((m, k) => saw(OUTRO, m, DUR - OUTRO - 1.5, .04, 1600, { att: .4, rel: .8, det: .003 * (k - 2.5), pan: -.4 + k * .16, send: .7 }));
[72, 76, 79, 76, 72, 67].forEach((m, k) => pluck(OUTRO + .5 + k * BEAT, m + 12, .05 * (1 - k / 7), k % 2 ? .4 : -.4, .15));

// ---------------------------------------------------------------- room + master
function reverb(x, delaysMs, fb) {                         // Schroeder: 4 parallel combs + 2 allpasses
  const y = new Float64Array(x.length);
  for (const dm of delaysMs) { const d = Math.round(dm * SR / 1000), buf = new Float64Array(d); let p = 0; for (let i = 0; i < x.length; i++) { const o = buf[p]; y[i] += o; buf[p] = x[i] + o * fb; p = (p + 1) % d; } }
  for (const [dm, g] of [[5.0, .5], [1.7, .5]]) { const d = Math.round(dm * SR / 1000), buf = new Float64Array(d); let p = 0; for (let i = 0; i < y.length; i++) { const b = buf[p], v = y[i] + g * b; y[i] = b - g * v; buf[p] = v; p = (p + 1) % d; } }
  return y;
}
const wl = reverb(VL, [29.7, 37.1, 41.1, 43.7], .82), wr = reverb(VR, [30.9, 38.3, 42.7, 45.1], .82);
for (let i = 0; i < N; i++) { const d = 1 - .55 * DUCK[i]; L[i] += d * MUS.L[i] + .12 * wl[i]; R[i] += d * MUS.R[i] + .12 * wr[i]; }   // side-chain: the kick ducks the tonal parts
const soften = (x, fc) => { const a = Math.exp(-2 * Math.PI * fc / SR); let z = 0; for (let i = 0; i < N; i++) { z = (1 - a) * x[i] + a * z; x[i] = z; } };
soften(L, 8000); soften(R, 8000);
let peak = 1e-9;
for (let i = 0; i < N; i++) { const t = i / SR, f = Math.min(1, (DUR - t) / 2.5) * Math.min(1, t / .05); L[i] = Math.tanh(L[i]) * f; R[i] = Math.tanh(R[i]) * f; peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i])); }
const pcm = Buffer.alloc(44 + N * 4);
pcm.write('RIFF', 0); pcm.writeUInt32LE(36 + N * 4, 4); pcm.write('WAVEfmt ', 8); pcm.writeUInt32LE(16, 16);
pcm.writeUInt16LE(1, 20); pcm.writeUInt16LE(2, 22); pcm.writeUInt32LE(SR, 24); pcm.writeUInt32LE(SR * 4, 28);
pcm.writeUInt16LE(4, 32); pcm.writeUInt16LE(16, 34); pcm.write('data', 36); pcm.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) { pcm.writeInt16LE(Math.round(L[i] / peak * 0.8 * 32767), 44 + i * 4); pcm.writeInt16LE(Math.round(R[i] / peak * 0.8 * 32767), 46 + i * 4); }

mkdirSync(dirname(OUT), { recursive: true });
const tmp = mkdtempSync(join(dirname(OUT), 'music_'));
try {
  const mix = join(tmp, 'mix.wav'); writeFileSync(mix, pcm);
  const LN = `loudnorm=I=${LUFS}:TP=-2.5:LRA=11`;   // -2.5 leaves room for AAC overshoot (the mp4 must stay <= -1 dBTP)
  const probe = spawnSync('ffmpeg', ['-hide_banner', '-i', mix, '-af', LN + ':print_format=json', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
  const m = JSON.parse(probe.slice(probe.lastIndexOf('{'), probe.lastIndexOf('}') + 1));
  const ln2 = `${LN}:measured_I=${m.input_i}:measured_LRA=${m.input_lra}:measured_TP=${m.input_tp}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`;
  const r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', mix, '-af', ln2, '-ar', String(SR), OUT], { stdio: 'inherit' });
  if (r.status !== 0) throw new Error('ffmpeg loudnorm failed');
} finally { rmSync(tmp, { recursive: true, force: true }); }
console.log('wrote', OUT);
