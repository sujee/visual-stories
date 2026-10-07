// The soundtrack: a very quiet, mellow felt-piano figure. No sound effects, no beat.
//
//   node src/music.mjs --duration 17 [--out workspace/tmp/music_16x9.wav] [--lufs -20]
//
// Synthesized here (additive piano: a few slightly inharmonic partials per note, soft attack, darker for high
// partials, two detuned strings), then a small reverb, a gentle low-pass, and a fade-out at the end.
// Deterministic (seeded rng), no dependencies. Slow: 72 BPM, C maj7 - A min7 - F maj7 - G6, then a rolled C add9.
// Normalized with a two-pass ffmpeg loudnorm to a deliberately low level (default -20 LUFS integrated, true peak <= -3 dBTP):
// it is meant to sit very quietly under the picture (the house default is about -14 LUFS; this is a choice, see brief.md).
import { spawnSync } from 'node:child_process';
import { writeFileSync, mkdtempSync, rmSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const DUR = +arg('duration', 17);
const OUT = resolve(arg('out', 'workspace/tmp/music_16x9.wav'));
const LUFS = +arg('lufs', -20);
const SR = 48000, N = Math.round(DUR * SR);
const L = new Float64Array(N), R = new Float64Array(N);

let seed = 7;                                              // mulberry32: same numbers every run
const rnd = () => { seed |= 0; seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const hz = m => 440 * 2 ** ((m - 69) / 12);

// One soft piano note: m = MIDI note, vel 0..1.
function note(start, m, vel) {
  const f0 = hz(m), i0 = Math.round(start * SR);
  const base = 0.9 + (m - 40) * 0.05;                       // low notes ring longer
  const B = 0.0001 * (m / 60) ** 2;                         // slight string stiffness (inharmonic partials)
  const pan = Math.max(-0.45, Math.min(0.45, (m - 60) / 40));
  const lg = Math.cos((pan + 1) * Math.PI / 4), rg = Math.sin((pan + 1) * Math.PI / 4);
  for (const det of [-0.0003, 0.0003]) {                    // two strings, a hair apart
    for (let n = 1; n <= 8; n++) {
      const f = f0 * n * Math.sqrt(1 + B * n * n) * (1 + det);
      if (f > 4500) break;                                  // mellow: nothing bright
      const amp = vel * 0.5 * Math.pow(n, -1.2) * Math.exp(-0.28 * (n - 1));
      const d = base * (1 + 0.5 * (n - 1));
      const len = Math.min(N - i0, Math.ceil(Math.log(1 / 0.0005) / d * SR));
      const w = 2 * Math.PI * f / SR;
      for (let i = 0; i < len; i++) {
        const t = i / SR;
        const s = Math.sin(w * i) * amp * Math.exp(-d * t) * (1 - Math.exp(-t / 0.004));
        L[i0 + i] += s * lg; R[i0 + i] += s * rg;
      }
    }
  }
}

// ---------------------------------------------------------------- the piece
const BEAT = 60 / 72, BAR = 4 * BEAT, T0 = 0.3;
const CHORDS = [
  { bass: 48, tones: [52, 55, 59, 64], mel: 76 },           // C maj7
  { bass: 45, tones: [52, 55, 60, 64], mel: 72 },           // A min7
  { bass: 41, tones: [53, 57, 60, 64], mel: 74 },           // F maj7
  { bass: 43, tones: [50, 55, 59, 64], mel: 71 },           // G6
];
const PATTERN = [0, 1, 2, 3, 2, 1, 2];                      // eighth-note rolling figure after the bass
const human = () => (rnd() - 0.5) * 0.024;
CHORDS.forEach((c, b) => {
  const t0 = T0 + b * BAR;
  note(t0 + Math.max(0, human()), c.bass, 0.36 * (0.92 + 0.16 * rnd()));
  PATTERN.forEach((k, s) => note(t0 + (s + 1) * BEAT / 2 + human(), c.tones[k], (s === 3 ? 0.34 : 0.26) * (0.9 + 0.2 * rnd())));
  if (b % 2 === 0) note(t0 + 2 * BEAT + 0.04, c.mel, 0.30);  // a high, quiet note on the third beat of every other bar
});
const tEnd = T0 + 4 * BAR;                                  // the resolution: a rolled C add9 that rings out
[48, 52, 55, 62, 67, 71].forEach((m, k) => note(tEnd + k * 0.09, m, k === 0 ? 0.36 : 0.32));

// ---------------------------------------------------------------- room + master
function reverb(x, delaysMs, fb = 0.78) {                    // Schroeder: 4 parallel combs + 2 allpasses
  const y = new Float64Array(x.length);
  for (const dm of delaysMs) {
    const d = Math.round(dm * SR / 1000), buf = new Float64Array(d); let p = 0;
    for (let i = 0; i < x.length; i++) { const o = buf[p]; y[i] += o; buf[p] = x[i] + o * fb; p = (p + 1) % d; }
  }
  for (const [dm, g] of [[5.0, 0.5], [1.7, 0.5]]) {
    const d = Math.round(dm * SR / 1000), buf = new Float64Array(d); let p = 0;
    for (let i = 0; i < y.length; i++) { const b = buf[p], v = y[i] + g * b; y[i] = b - g * v; buf[p] = v; p = (p + 1) % d; }
  }
  return y;
}
const onePole = (x, fc) => { const a = Math.exp(-2 * Math.PI * fc / SR); let z = 0; for (let i = 0; i < x.length; i++) { z = (1 - a) * x[i] + a * z; x[i] = z; } };
const wetL = reverb(L, [29.7, 37.1, 41.1, 43.7]), wetR = reverb(R, [30.9, 38.3, 42.7, 45.1]);
const MIX = 0.22;
for (let i = 0; i < N; i++) { L[i] += MIX * wetL[i] * 0.25; R[i] += MIX * wetR[i] * 0.25; }
for (const ch of [L, R]) { onePole(ch, 3000); onePole(ch, 3000); }   // roll off the top: soft, round
const fadeS = 0.8;
let peak = 1e-9;
for (let i = 0; i < N; i++) {
  const f = Math.min(1, (N - i) / (fadeS * SR)), g = Math.min(1, i / (0.1 * SR));
  L[i] *= f * g; R[i] *= f * g; peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
}
const pcm = Buffer.alloc(44 + N * 4);
pcm.write('RIFF', 0); pcm.writeUInt32LE(36 + N * 4, 4); pcm.write('WAVEfmt ', 8); pcm.writeUInt32LE(16, 16);
pcm.writeUInt16LE(1, 20); pcm.writeUInt16LE(2, 22); pcm.writeUInt32LE(SR, 24); pcm.writeUInt32LE(SR * 4, 28);
pcm.writeUInt16LE(4, 32); pcm.writeUInt16LE(16, 34); pcm.write('data', 36); pcm.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) { pcm.writeInt16LE(Math.round(L[i] / peak * 0.8 * 32767), 44 + i * 4); pcm.writeInt16LE(Math.round(R[i] / peak * 0.8 * 32767), 46 + i * 4); }

mkdirSync(dirname(OUT), { recursive: true });
const tmp = mkdtempSync(join(dirname(OUT), 'music_'));
try {
  const mix = join(tmp, 'mix.wav'); writeFileSync(mix, pcm);
  const LN = `loudnorm=I=${LUFS}:TP=-3:LRA=11`;
  const probe = spawnSync('ffmpeg', ['-hide_banner', '-i', mix, '-af', LN + ':print_format=json', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
  const m = JSON.parse(probe.slice(probe.lastIndexOf('{'), probe.lastIndexOf('}') + 1));
  const ln2 = `${LN}:measured_I=${m.input_i}:measured_LRA=${m.input_lra}:measured_TP=${m.input_tp}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`;
  const r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', mix, '-af', ln2, '-ar', String(SR), OUT], { stdio: 'inherit' });
  if (r.status !== 0) throw new Error('ffmpeg loudnorm failed');
} finally { rmSync(tmp, { recursive: true, force: true }); }
console.log('wrote', OUT);
