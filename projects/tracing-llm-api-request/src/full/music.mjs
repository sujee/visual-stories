// The full video's soundtrack: calm lo-fi background music with a light Indian-film colour. A soft bansuri-like flute carries a
// lyrical line (a major pentatonic, a raga-like colour) over a smooth sustained drone bed, with a faint tape wobble and hiss, no
// plucks and no hard hits. (u1-u4: an upbeat, major-key family.) The default option, `u2`, is the one chosen for the video. The other options (a, b, c, a1-a8, n1-n3, r1-r3,
// s2, s3, d1-d3) are variations kept to compare or remix: warmer, sparser, flute-only, or with deep taiko-style war drums.
// Original compositions: nothing is taken from an existing song.
//
//   node src/full/music.mjs --duration 315 [--option u2] [--cues cues.json] [--out workspace/tmp/music_full.wav]
//   cues.json: { "lift": [[from, to], ...], "quiet": [[from, to], ...] } in seconds: the music lifts a little (a soft, airy swell of
//   strings, the flute a touch louder) under the lift ranges and goes about 3.5 dB quieter in the quiet ranges, so it follows the story.
//
// Synthesized here, deterministic (seeded rng), no dependencies. Normalized to about -14 LUFS integrated (true peak <= -2.5 dBTP
// before the AAC encode, so the video stays <= -1 dBTP). A .wav output stays lossless (the render encodes it once, into the mp4);
// any other extension (.m4a) is encoded as AAC. The render passes the real duration of the video.
import { spawnSync } from 'node:child_process';
import { writeFileSync, readFileSync, mkdtempSync, rmSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const arg = (n, d) => { const i = process.argv.indexOf('--' + n); return i > 0 ? process.argv[i + 1] : d; };
const OPT = arg('option', 'u2'), DUR = +arg('duration', 315), OUT = resolve(arg('out', `workspace/tmp/music_full_${OPT}.wav`));
const SR = 48000, N = Math.round(DUR * SR);
const CUES = arg('cues', null) ? JSON.parse(readFileSync(resolve(arg('cues')), 'utf8')) : {};
const smoothEnv = (ranges = [], ramp) => t => ranges.reduce((m, [a, b]) => Math.max(m, Math.min(1, Math.max(0, (t - a) / ramp), Math.max(0, (b - t) / ramp))), 0);
const LIFT = smoothEnv(CUES.lift, 1.8), QUIET = smoothEnv(CUES.quiet, 1.8);          // 0..1, with gentle ramps
const P = Object.assign({ bpm: { a: 66, b: 80, c: 72 }[OPT] ?? 70, fAtt: .09, fRel: .22, fGain: .13, breath: .12, tanAtt: .01, tanBuzz: .5, lp: 7000, wow: 0, hiss: 0, rev: .18, padAtt: 1.6, bassGain: .09, vib: .0045, padMul: 1, taiko: 0, roll: 0 }, {
  a1: { bpm: 62, fAtt: .28, fRel: .5, fGain: .10, breath: .06, tanAtt: .08, tanBuzz: .15, lp: 5200, rev: .2, padAtt: 2.2 },
  a2: { bpm: 62, fAtt: .28, fRel: .5, fGain: .10, breath: .06, tanAtt: .08, tanBuzz: .15, lp: 3800, wow: .0016, hiss: .004, rev: .2, padAtt: 2.2 },
  a4: { bpm: 62, fAtt: .4, fRel: .7, fGain: .075, breath: .04, tanAtt: .1, tanBuzz: .1, lp: 2600, wow: .0016, hiss: .003, rev: .22, padAtt: 2.6, fShift: -12, dropTop: true, fEvery: 2 },
  a5: { bpm: 62, fAtt: .4, fRel: .7, fGain: .07, breath: .04, tanAtt: .1, tanBuzz: .1, lp: 2400, wow: .0016, hiss: .003, rev: .22, padAtt: 2.6, dropTop: true, fEvery: 2 },
  a6: { bpm: 60, fAtt: .45, fRel: .8, fGain: .07, breath: .04, tanAtt: .1, tanBuzz: .1, lp: 2600, wow: .0016, hiss: .003, rev: .24, padAtt: 2.6, fShift: -12, dropTop: true, fEvery: 3 },
  a7: { bpm: 60, fAtt: .9, fRel: 1.4, fGain: .065, breath: .03, tanAtt: .1, tanBuzz: .08, lp: 2600, wow: .0016, hiss: .003, rev: .26, padAtt: 2.8, fShift: -12, dropTop: true, fLong: true },
  a8: { bpm: 60, fAtt: .5, fRel: .9, fGain: .07, breath: .03, tanAtt: .12, tanBuzz: .05, lp: 2000, wow: .0018, hiss: .002, rev: .26, padAtt: 3, fShift: -12, dropTop: true, fEvery: 2, bassGain: .14 },
  n1: { bpm: 62, fAtt: .5, fRel: .8, fGain: .07, breath: .04, lp: 2600, wow: .0016, hiss: .003, rev: .22, padAtt: 3, fShift: -12, dropTop: true, fEvery: 2, sustain: true },
  n2: { bpm: 60, fAtt: .9, fRel: 1.4, fGain: .065, breath: .03, lp: 2600, wow: .0016, hiss: .003, rev: .26, padAtt: 3, fShift: -12, dropTop: true, fLong: true, sustain: true },
  n3: { bpm: 60, fAtt: .6, fRel: .9, fGain: .07, breath: .03, lp: 2000, wow: .0018, hiss: .002, rev: .26, padAtt: 3.2, fShift: -12, dropTop: true, fEvery: 2, bassGain: .14, sustain: true },
  r1: { bpm: 64, fAtt: .18, fRel: .45, fGain: .10, breath: .08, lp: 4200, wow: .0014, hiss: .003, rev: .24, padAtt: 2.8, sustain: true, vib: .006, dropTop: true },
  r2: { bpm: 64, fAtt: .18, fRel: .45, fGain: .10, breath: .08, lp: 4200, wow: .0014, hiss: .003, rev: .26, padAtt: 2.8, sustain: true, vib: .006, dropTop: true, strings: true },
  r3: { bpm: 64, fAtt: .2, fRel: .5, fGain: .095, breath: .08, lp: 4200, wow: .0014, hiss: .003, rev: .28, padAtt: 2.8, sustain: true, vib: .008, dropTop: true, echo: true },
  s1: { bpm: 64, fAtt: .18, fRel: .45, fGain: .10, breath: .08, lp: 4200, wow: .0014, hiss: .002, rev: .24, padAtt: 2.8, sustain: true, vib: .006, dropTop: true, padMul: .55 },
  s2: { bpm: 64, fAtt: .18, fRel: .45, fGain: .10, breath: .08, lp: 4200, wow: .0014, hiss: .0015, rev: .24, padAtt: 3, sustain: true, vib: .006, dropTop: true, padMul: .38 },
  s3: { bpm: 64, fAtt: .2, fRel: .5, fGain: .10, breath: .08, lp: 4200, wow: .0014, hiss: .001, rev: .28, padAtt: 3.2, sustain: true, vib: .006, dropTop: true, padMul: .25 },
  d1: { bpm: 68, fAtt: .18, fRel: .45, fGain: .09, breath: .08, lp: 4200, wow: 0, hiss: 0, rev: .26, padAtt: 2.8, sustain: true, vib: .006, dropTop: true, padMul: .6, taiko: .5, roll: 1 },
  d2: { bpm: 76, fAtt: .18, fRel: .45, fGain: .085, breath: .08, lp: 4200, wow: 0, hiss: 0, rev: .26, padAtt: 2.8, sustain: true, vib: .006, dropTop: true, padMul: .6, taiko: .62, roll: 2 },
  d3: { bpm: 68, rev: .3, lp: 3600, padAtt: 2.8, sustain: true, dropTop: true, padMul: .9, taiko: .6, roll: 2, noFlute: true },
  e1: { bpm: 66, lead: 'esraj', fGain: .11, east: true, soar: true, sustain: true, padMul: .5, lp: 4200, wow: .0012, hiss: .0015, rev: .3, padAtt: 3 },
  e2: { bpm: 66, lead: 'sarod', fGain: .12, east: true, soar: true, sustain: true, padMul: .5, lp: 4200, wow: .0012, hiss: .0015, rev: .3, padAtt: 3 },
  e3: { bpm: 66, lead: 'shehnai', fGain: .085, east: true, soar: true, harmonium: true, sustain: true, padMul: .4, lp: 3800, wow: .0012, hiss: .0015, rev: .3, padAtt: 3 },
  e4: { bpm: 66, lead: null, east: true, soar: true, harmonium: true, choir: .02, sustain: true, padMul: .55, lp: 4000, wow: .0012, hiss: .0015, rev: .32, padAtt: 3 },
  u1: { bpm: 92, up: true, padMul: .45, padAtt: 1.2, lp: 5000, wow: .001, hiss: .0015, rev: .22, fAtt: .12, fRel: .35, fGain: .10, breath: .06, vib: .005, noDrone: true, keys: true, melody: true, shaker: true },
  u2: { bpm: 96, up: true, padMul: .45, padAtt: 1.2, lp: 5000, wow: .001, hiss: .0015, rev: .22, fAtt: .12, fRel: .35, fGain: .10, breath: .06, vib: .005, noDrone: true, kal: true },
  u3: { bpm: 90, up: true, padMul: .45, padAtt: 1.2, lp: 5000, wow: .001, hiss: .0015, rev: .22, fAtt: .12, fRel: .35, fGain: .10, breath: .06, vib: .005, noDrone: true, melody: true, tabla: true, shaker: true },
  u4: { bpm: 100, up: true, padMul: .45, padAtt: 1.2, lp: 5000, wow: .001, hiss: .0015, rev: .22, fAtt: .12, fRel: .35, fGain: .10, breath: .06, vib: .005, noDrone: true, strum: true, melody: true, melodyEvery: 2, shaker: true },
  a3: { bpm: 58, fAtt: .5, fRel: .8, fGain: .09, breath: .03, tanAtt: .1, tanBuzz: .05, lp: 3200, wow: .0022, hiss: .004, rev: .32, padAtt: 2.6 },
}[OPT] || {});
const FLUTE = /^[anrsd]/.test(OPT) && !P.noFlute;
const L = new Float64Array(N), R = new Float64Array(N), VL = new Float64Array(N), VR = new Float64Array(N);
let seed = { a: 11, b: 29, c: 47 }[OPT] ?? 11;
const rnd = () => { seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
const hz = m => 440 * 2 ** ((m - 69) / 12);
function voice(t, len, fn, pan = 0, send = .3) {
  const i0 = Math.round(t * SR), lg = Math.cos((pan + 1) * Math.PI / 4), rg = Math.sin((pan + 1) * Math.PI / 4);
  for (let i = 0; i < len * SR; i++) { const j = i0 + i; if (j < 0 || j >= N) continue; const v = fn(i / SR); L[j] += v * lg; R[j] += v * rg; VL[j] += v * lg * send; VR[j] += v * rg * send; }
}
const env = (s, len, att, rel) => Math.min(1, s / att) * (s > len ? Math.exp(-(s - len) / rel) : 1);
function pad(t, m, len, g, cut, o = {}) {                  // a warm band-limited saw
  const f = hz(m) * (1 + (o.det || 0)), n = Math.max(1, Math.min(30, Math.floor(cut / f)));
  voice(t, len + 3, s => { let v = 0; for (let k = 1; k <= n; k++) v += Math.sin(2 * Math.PI * f * k * s) / k; return g * P.padMul * v * env(s, len, o.att ?? P.padAtt, o.rel ?? 1.6); }, o.pan || 0, o.send ?? .6);
}
function tanpura(t, m, g, pan) {                           // a drone string: a long ring with a "buzz" of upper partials that swells and fades
  const f = hz(m);
  voice(t, 5.5, s => { let v = 0; for (let k = 1; k <= 14; k++) { const buzz = k > 3 ? Math.exp(-((s - .9 - k * .03) ** 2) / .35) * .9 * P.tanBuzz / .5 : 0; v += Math.sin(2 * Math.PI * f * k * s + k * .3) * (1 / k ** 1.1 * Math.exp(-s * (.35 + .12 * k)) + buzz / k ** 1.6 * .5); } return g * v * Math.min(1, s / P.tanAtt); }, pan, .5);
}
function flute(t, m, len, g, slide, pan) {                 // a bansuri-like tone: sine + a little 2nd harmonic, breath noise, vibrato and a short glide into the note
  let ph = 0, br = 0; const f0 = hz(m);
  voice(t, len + .5, s => {
    const vib = 1 + P.vib * Math.sin(2 * Math.PI * 5.2 * s) * Math.min(1, s / .6), f = f0 * 2 ** ((slide || 0) * Math.exp(-s * 14) / 12) * vib;
    ph += 2 * Math.PI * f / SR; br = .86 * br + .14 * (rnd() * 2 - 1);
    const e = env(s, len, P.fAtt, P.fRel);
    return g * e * (Math.sin(ph) + .22 * Math.sin(2 * ph) + .06 * Math.sin(3 * ph) + br * .9 * (.25 + .75 * Math.min(1, s / .05)) * P.breath);
  }, pan, .55);
}
function bowed(t, m, len, g, slide, pan) {                  // an esraj-like bowed string: a slow bow, a singing vibrato and a glide (meend) into the note
  let ph = 0, br = 0; const f0 = hz(m);
  voice(t, len + .6, s => {
    const f = f0 * 2 ** ((slide || 0) * Math.exp(-s * 9) / 12) * (1 + .0055 * Math.sin(2 * Math.PI * 5.1 * s) * Math.min(1, s / .6)), n = Math.max(1, Math.min(14, Math.floor(2400 / f)));
    ph += 2 * Math.PI * f / SR; br = .9 * br + .1 * (rnd() * 2 - 1); let v = 0; for (let k = 1; k <= n; k++) v += Math.sin(k * ph) / k ** 1.2;
    return g * (v + br * .25) * env(s, len, .26, .55) * .8;
  }, pan, .6);
}
function sarodGlide(t, m, len, g, slide, pan) {              // a sarod-like gliding tone: soft, a wide slide between notes, no pluck
  let ph = 0; const f0 = hz(m);
  voice(t, len + .6, s => {
    const f = f0 * 2 ** ((slide || -3) * Math.exp(-s * 5) / 12); ph += 2 * Math.PI * f / SR;
    let v = 0; for (let k = 1; k <= 7; k++) v += Math.sin(k * ph) * .55 ** (k - 1) * (k % 2 ? 1 : .6);
    return g * v * env(s, len, .3, .7) * (1 + .12 * Math.sin(2 * Math.PI * 4.6 * s)) * .8;
  }, pan, .65);
}
function reed(t, m, len, g, slide, pan) {                    // a shehnai-like reed: nasal, a little vibrato, kept soft
  let ph = 0; const f0 = hz(m);
  voice(t, len + .6, s => {
    const f = f0 * 2 ** ((slide || 0) * Math.exp(-s * 10) / 12) * (1 + .004 * Math.sin(2 * Math.PI * 5.3 * s) * Math.min(1, s / .5)); ph += 2 * Math.PI * f / SR;
    let v = 0; for (let k = 1; k <= 14; k++) v += Math.sin(k * ph) / k ** .6 * (1 + 2.2 * Math.exp(-(((k * f - 1700) / 520) ** 2)));
    return g * v * env(s, len, .32, .6) * .32;
  }, pan, .6);
}
function choir(t, m, len, g, pan, att = 2.2) {              // a wordless "aah" choir: harmonics shaped by vowel formants, slow swell
  const f = hz(m);
  [-.004, 0, .004].forEach(d => voice(t, len + 3, s => {
    let v = 0; const fd = f * (1 + d) * (1 + .003 * Math.sin(2 * Math.PI * 4.8 * s + d * 900));
    for (let k = 1; k <= 18; k++) { const fk = k * fd; v += Math.sin(2 * Math.PI * fk * s) / k * (Math.exp(-(((fk - 700) / 280) ** 2)) + .7 * Math.exp(-(((fk - 1150) / 350) ** 2)) + .3 * Math.exp(-(((fk - 2600) / 500) ** 2))); }
    return g * v * env(s, len, att, 2);
  }, pan, .75));
}
function harmonium(t, m, len, g, pan) {                      // a harmonium: three reeds, a slow swell and a faint tremolo
  const f = hz(m);
  voice(t, len + 2, s => { let v = 0; for (const d of [-.004, 0, .004]) for (let k = 1; k <= 8; k++) v += Math.sin(2 * Math.PI * f * (1 + d) * k * s) / k ** 1.1; return g * v * env(s, len, .9, 1.4) * (1 + .06 * Math.sin(2 * Math.PI * 5.2 * s)); }, pan, .5);
}
function ks(t, m, len, g, pan, bright = .5, buzz = 0) {    // a plucked string (Karplus-Strong), with an optional sitar-like buzz of upper partials
  const f = hz(m), d = Math.max(2, Math.round(SR / f)), buf = new Float64Array(d); for (let i = 0; i < d; i++) buf[i] = rnd() * 2 - 1;
  let p = 0, last = 0;
  voice(t, len, s => {
    const o = buf[p], nx = buf[(p + 1) % d]; buf[p] = (bright * o + (1 - bright) * nx) * .9965; p = (p + 1) % d; last = o;
    const b = buzz ? buzz * Math.sin(2 * Math.PI * f * 5 * s) * Math.exp(-s * 6) * .5 : 0;
    return g * (o + b) * env(s, len - .3, .002, .25);
  }, pan, .6);
}
function tabla(t, kind, g) {                               // soft hand-drum hits
  const hit = (len, fn, pan = 0, send = .35) => voice(t, len, fn, pan, send);
  if (kind === 'dha' || kind === 'ge') hit(.4, s => g * Math.sin(2 * Math.PI * (70 + 70 * Math.exp(-s * 18)) * s) * Math.exp(-s * 9) * (kind === 'ge' ? .8 : 1));
  if (kind === 'dha' || kind === 'na') hit(.3, s => g * .9 * (Math.sin(2 * Math.PI * 300 * s) + .4 * Math.sin(2 * Math.PI * 610 * s)) * Math.exp(-s * 16), .25);
  if (kind === 'ti') hit(.1, s => g * (rnd() * 2 - 1) * Math.exp(-s * 55) * .6, .2);
  if (kind === 'dhi') hit(.25, s => g * (Math.sin(2 * Math.PI * 190 * s) * Math.exp(-s * 20) + .5 * Math.sin(2 * Math.PI * 440 * s) * Math.exp(-s * 25)), .1);
}
function shaker(t, g) { let z = 0; voice(t, .09, s => { z = .5 * z + .5 * (rnd() * 2 - 1); return g * (z - .5 * (rnd() * 2 - 1)) * Math.exp(-s * 45); }, .35 * (rnd() - .5) * 2, .2); }

// C major pentatonic (a Bhupali-like colour): C D E G A. Four chords, two bars each: C - Am - F - Gsus2
const BPM = P.bpm, BEAT = 60 / BPM, CHORD = 8 * BEAT;
const CH = P.up ? [[48, [64, 67, 71, 74]], [43, [59, 62, 67, 69]], [45, [60, 64, 67, 72]], [41, [57, 60, 64, 69]]]    // upbeat, major: Cmaj9, Gadd13, Am7, Fmaj7 (I V vi IV)
  : P.east ? [[48, [60, 64, 67, 71]], [50, [62, 66, 69, 74]], [43, [59, 62, 67, 71]], [45, [57, 60, 64, 67]]]    // eastern: a Yaman-like colour (C D E F# G A B): Cmaj7, D, G, Am
  : [[48, [60, 64, 67, 74]], [45, [57, 64, 67, 72]], [41, [57, 60, 67, 72]], [43, [55, 62, 67, 74]]];   // bass, upper voices
const nCh = Math.ceil(DUR / CHORD);
for (let c = 0; c < nCh; c++) {
  const t0 = c * CHORD, [bass, up] = CH[c % 4];
  (P.dropTop ? up.slice(0, 3) : up).forEach((m, k) => pad(t0, m, CHORD + .4, OPT === 'b' ? .03 : .036, 1000, { det: .003 * (k - 1.5), pan: -.5 + k * .33 }));
  if (P.strings) up.slice(0, 3).forEach((m, k) => [-.005, 0, .005].forEach(d => pad(t0, m, CHORD + .4, .011, 1500, { det: d, pan: -.6 + k * .6, att: 2.4, rel: 2.2, send: .7 })));   // a soft string-like layer, held under the flute
  pad(t0, bass - 12, CHORD, P.bassGain, 300, { att: 1.2, rel: 1.4, send: .2 });
}
if (!P.noDrone) if (P.sustain) for (let t = -2; t < DUR; t += 6) for (const [m, g, pn] of [[48, .05, -.2], [55, .04, .2], [60, .02, 0]]) pad(Math.max(0, t), m, 8, g, 500, { att: 3.2, rel: 3, det: .002, pan: pn, send: .7 });   // a smooth, sustained drone bed: no plucks, so nothing dings
else for (let t = 0; t < DUR - 3; t += 4.2) { tanpura(t, 55, .05, -.2); tanpura(t + 1.05, 60, .035, .2); tanpura(t + 2.1, 60, .035, .25); tanpura(t + 3.15, 48, .06, -.25); }   // Pa Sa Sa Sa(low)

if (FLUTE) {                                               // bansuri over the drone: a calm, singing line
  const PH = [[[67, 0, 2, -2], [69, 2, 1, 0], [67, 3, 1, 0], [64, 4, 3.5, -2]], [[69, 0, 2, 0], [72, 2, 1.5, -2], [71, 3.5, .5, 0], [69, 4, 3.5, 0]],
    [[72, 0, 2, 0], [69, 2, 1, 0], [67, 3, 1, 0], [69, 4, 3.5, -1]], [[67, 0, 2, 0], [62, 2, 1, 0], [64, 3, 1, 0], [67, 4, 4, -2]]];
  if (P.fLong) for (let c = 1; c < nCh; c++) flute(c * CHORD + .5 * BEAT, [67, 69, 69, 67][c % 4] + (P.fShift || 0), 7 * BEAT, P.fGain, 0, .15);   // one long, soft tone per chord
else for (let c = 1; c < nCh; c++) { if (P.fEvery && (c - 1) % P.fEvery) continue; for (const [m, b, l, sl] of PH[c % 4]) { flute(c * CHORD + b * BEAT, m + (P.fShift || 0), l * BEAT * .92, P.fGain * (1 + .3 * LIFT(c * CHORD + b * BEAT)), sl, .15); if (P.echo) flute(c * CHORD + b * BEAT + 1.5 * BEAT, m + (P.fShift || 0), l * BEAT * .8, P.fGain * .32, 0, -.5); } }
}
if (P.east) {
  const PHE = [[[64, 0, 2, 0], [66, 2, 1, 0], [67, 3, 1, 0], [71, 4, 3.5, -2]], [[69, 0, 2, -2], [66, 2, 1, 0], [69, 3, 1, 0], [74, 4, 3.5, -1]],
    [[71, 0, 2, 0], [74, 2, 1.5, -2], [71, 3.5, .5, 0], [67, 4, 3.5, 0]], [[69, 0, 2, 0], [67, 2, 1, 0], [64, 3, 1, 0], [67, 4, 4, -2]]];
  const LEAD = { esraj: bowed, sarod: sarodGlide, shehnai: reed }[P.lead];
  for (let c = 0; c < nCh; c++) {
    const t0 = c * CHORD, [bass, up] = CH[c % 4];
    if (P.harmonium) up.slice(0, 3).forEach((m, k) => harmonium(t0, m - 12 * (k === 0), CHORD + .3, .02, -.4 + k * .4));
    if (P.choir) up.slice(0, 3).forEach((m, k) => choir(t0, m, CHORD, P.choir * (1 + .6 * LIFT(t0 + CHORD / 2)), -.5 + k * .5, 2.6));
    if (P.soar && c >= 2 && c % 2 === 0) [up[1], up[2], up[1] + 12, up[2] + 12].forEach((m, k) => choir(t0, m, CHORD, .016, -.6 + k * .4, 2.6));      // a soaring swell on every other chord
    if (LEAD && c >= 1) for (const [m, b, l, sl] of PHE[c % 4]) LEAD(t0 + b * BEAT, m, l * BEAT * .92, P.fGain * (1 + .3 * LIFT(t0 + b * BEAT)), sl, .15);
  }
}
if (P.up) {                                                // upbeat: a gentle major groove, all of it soft and rounded
  const sine = (f, s) => Math.sin(2 * Math.PI * f * s);
  const keys = (t, m, g, pan) => { const f = hz(m); voice(t, 2.4, s => g * (sine(f, s) + .35 * sine(2 * f, s) * Math.exp(-s * 5) + .1 * sine(3 * f, s) * Math.exp(-s * 9)) * Math.min(1, s / .014) * Math.exp(-s * 2.4), pan, .55); };
  const kal = (t, m, g, pan) => { const f = hz(m); voice(t, 1.8, s => g * (sine(f, s) + .18 * sine(2.01 * f, s) * Math.exp(-s * 8)) * Math.min(1, s / .01) * Math.exp(-s * 3.2), pan, .5); };
  const bassNote = (t, m, g) => { const f = hz(m); voice(t, 1.6, s => g * (sine(f, s) + .22 * sine(2 * f, s)) * Math.min(1, s / .012) * Math.exp(-s * 2.8), 0, .15); };
  const MEL = [[[72, 0, 1.5], [76, 1.5, 1], [74, 2.5, .5], [72, 3, 1], [67, 4, 3]], [[71, 0, 1.5], [74, 1.5, 1], [71, 2.5, .5], [69, 3, 1], [67, 4, 3]],
    [[69, 0, 1.5], [72, 1.5, 1], [76, 2.5, .5], [74, 3, 1], [72, 4, 3]], [[69, 0, 1], [72, 1, 1], [69, 2, 1], [67, 3, 1], [72, 4, 3.5]]];
  for (let c = 0; c < nCh; c++) {
    const t0 = c * CHORD, [bass, up] = CH[c % 4];
    bassNote(t0, bass, .10); bassNote(t0 + 3.5 * BEAT, bass + (c % 2 ? 7 : 0), .06); bassNote(t0 + 4 * BEAT, bass, .08);
    if (P.keys) for (const b of [0, 2.5, 4, 6.5]) up.slice(0, 3).forEach((m, k) => keys(t0 + b * BEAT, m, .03, -.3 + k * .3));
    if (P.kal) for (let e = 0; e < 16; e++) kal(t0 + e * BEAT / 2, up[[0, 1, 2, 3, 2, 1, 2, 3][e % 8]] + (e % 8 === 3 ? 0 : 0) + (e >= 8 ? 12 * (e % 4 === 3) : 0), .05 * (e % 2 ? .7 : 1), -.35 + (e % 4) * .23);
    if (P.strum) for (const b of [0, 1.5, 3, 4.5, 6]) up.forEach((m, k) => ks(t0 + b * BEAT + k * .018, m - 12 * (k < 2), 1.2, .045 * (b % 3 === 0 ? 1 : .7), -.3 + k * .2, .38));
    if (P.melody && c >= 1 && !(P.melodyEvery && (c - 1) % P.melodyEvery)) for (const [m, b, l] of MEL[c % 4]) flute(t0 + b * BEAT, m, l * BEAT * .9, P.fGain * (1 + .3 * LIFT(t0 + b * BEAT)), 0, .15);
    if (P.tabla) for (let b = 0; b < 8; b++) { const k = ['ge', null, 'na', 'ti', 'na', null, 'dhi', 'na'][b]; if (k) tabla(t0 + b * BEAT, k, k === 'ge' ? .07 : .04); }
  }
  if (P.shaker) for (let t = 2; t < DUR - 3; t += BEAT / 2) shaker(t, Math.round((t - 2) / (BEAT / 2)) % 2 ? .022 : .012);
}
if (OPT === 'b') {                                         // a soft pulse: tabla in an 8-beat pattern, a shaker and a plucked ostinato
  const KEHERWA = ['dha', 'ge', 'na', 'ti', 'na', 'ka', 'dhi', 'na'];
  for (let b = 0; b * BEAT < DUR - 4; b++) {
    const t = 6 + b * BEAT; if (t > DUR - 4) break; const k = KEHERWA[b % 8];
    if (k !== 'ka') tabla(t, k, k === 'dha' ? .13 : .07);
    shaker(t + BEAT / 2, .03); shaker(t, .018);
  }
  const OST = [60, 64, 67, 72, 67, 64, 69, 67];
  for (let e = 0; e * BEAT / 2 < DUR - 3; e++) { const t = 4 + e * BEAT / 2; if (t > DUR - 3) break; if (e % 2 === 0 || e % 8 === 5) ks(t, OST[e % 8] + (Math.floor(t / CHORD) % 4 === 1 ? -3 : 0), 1.4, .09, (e % 4 - 1.5) * .25, .5); }
}
if (OPT === 'c') {                                         // sitar-like plucks arpeggiating the pentatonic, over the drone
  const SC = [60, 62, 64, 67, 69, 72, 74, 76];
  for (let e = 0; e * BEAT / 2 < DUR - 3; e++) {
    const t = 3 + e * BEAT / 2; if (t > DUR - 3) break; const ph = Math.floor(e / 8) % 4;
    if ((e % 4 === 0) || (e % 4 === 2 && rnd() < .7) || rnd() < .18) ks(t, SC[(e * 3 + ph * 2 + (rnd() < .3 ? 1 : 0)) % SC.length] + (ph === 3 ? -5 * (e % 3 === 0) : 0), 2.2, .11, (rnd() - .5) * .8, .42, .5);
  }
  for (let b = 0; b * BEAT * 4 < DUR - 6; b++) tabla(6 + b * BEAT * 4, 'ge', .06);   // a soft low thump on every bar
}
function taiko(t, kind, g, pan = 0) {                      // a big drum: a round thump (no sharp click), a shell ring, and a breath of low noise
  const [f0, f1, dec] = { boom: [70, 38, 1.0], dun: [92, 54, .55], don: [128, 78, .4], ka: [210, 150, .16] }[kind];
  let z = 0;
  voice(t, dec * 3, s => {
    const body = Math.sin(2 * Math.PI * (f1 + (f0 - f1) * Math.exp(-s * 22)) * s) * Math.exp(-s / dec * 2.2);
    z = .93 * z + .07 * (rnd() * 2 - 1);
    return g * (body + .35 * Math.sin(2 * Math.PI * f0 * 1.9 * s) * Math.exp(-s * 14) + 1.6 * z * Math.exp(-s * 22)) * Math.min(1, s / .004);
  }, pan, kind === 'boom' ? .5 : .3);
}
if (P.taiko) {
  const EIGHTH = BEAT / 3, BAR = 6 * EIGHTH, T0 = 4;
  const PATA = [[[0, 'boom', 1], [3, 'don', .5], [4, 'dun', .35], [5, 'dun', .35]], [[0, 'boom', 1], [2, 'dun', .4], [3, 'don', .6], [5, 'ka', .3]]];
  for (let b = 0; T0 + b * BAR < DUR - 3; b++) {
    const tb = T0 + b * BAR, lift = Math.min(1, b / 6) * (P.taiko), fill = (b % 4 === 3);
    for (const [e, kind, v] of PATA[b % 2]) { if (fill && e >= 3 && P.roll) continue; taiko(tb + e * EIGHTH, kind, v * lift * .9, (e % 2 ? .25 : -.25)); }
    if (fill && P.roll) for (let k = 0; k < (P.roll === 2 ? 8 : 6); k++) taiko(tb + 3 * EIGHTH + k * (3 * EIGHTH / (P.roll === 2 ? 8 : 6)), k % 2 ? 'don' : 'dun', (.35 + .5 * k / 8) * lift, k % 2 ? .3 : -.3);
  }
  for (let c = 2; c * CHORD < DUR - 3; c += 2) taiko(c * CHORD, 'boom', 1.1 * P.taiko, 0);        // a big drum under every other chord change
}
for (const [a, b] of CUES.lift || []) {                    // the lift: a soft, airy swell of strings, an octave of the current chord, rising and fading with the section
  const c = Math.floor(a / CHORD) % 4, len = Math.max(3, b - a + 1);
  [CH[c][1][1], CH[c][1][2], CH[c][1][1] + 12, CH[c][1][2] + 12].forEach((m, k) => [-.004, .004].forEach(d => pad(a, m, len, .016, 2200, { att: Math.min(2.4, len * .45), rel: 2.6, det: d, pan: -.6 + k * .4, send: .8 })));
}
function reverb(x, delaysMs, fb) {
  const y = new Float64Array(x.length);
  for (const dm of delaysMs) { const d = Math.round(dm * SR / 1000), buf = new Float64Array(d); let p = 0; for (let i = 0; i < x.length; i++) { const o = buf[p]; y[i] += o; buf[p] = x[i] + o * fb; p = (p + 1) % d; } }
  for (const [dm, g] of [[5.0, .5], [1.7, .5]]) { const d = Math.round(dm * SR / 1000), buf = new Float64Array(d); let p = 0; for (let i = 0; i < y.length; i++) { const b = buf[p], v = y[i] + g * b; y[i] = b - g * v; buf[p] = v; p = (p + 1) % d; } }
  return y;
}
const wl = reverb(VL, [29.7, 37.1, 41.1, 43.7, 53.3], .86), wr = reverb(VR, [30.9, 38.3, 42.7, 45.1, 54.9], .86);
for (let i = 0; i < N; i++) { L[i] += P.rev * wl[i]; R[i] += P.rev * wr[i]; }
if (P.wow) for (const x of [L, R]) {                      // tape: a slow wobble in the pitch, and a faint hiss
  const src = Float64Array.from(x), A = P.wow * SR / (2 * Math.PI * .5), A2 = P.wow * .25 * SR / (2 * Math.PI * 5.5);
  for (let i = 0; i < N; i++) { const d = 60 + A * Math.sin(2 * Math.PI * .5 * i / SR) + A2 * Math.sin(2 * Math.PI * 5.5 * i / SR), q = i - d, i0 = Math.floor(q), fr = q - i0; x[i] = i0 >= 0 ? src[i0] * (1 - fr) + src[i0 + 1] * fr : 0; }
}
if (P.hiss) for (const x of [L, R]) { let z = 0; for (let i = 0; i < N; i++) { z = .9 * z + .1 * (rnd() * 2 - 1); x[i] += P.hiss * z; } }
const soften = (x, fc) => { const a = Math.exp(-2 * Math.PI * fc / SR); let z = 0; for (let i = 0; i < N; i++) { z = (1 - a) * x[i] + a * z; x[i] = z; } };
soften(L, P.lp); soften(R, P.lp);
let peak = 1e-9;
for (let i = 0; i < N; i++) { const t = i / SR, f = Math.min(1, (DUR - t) / 3) * Math.min(1, t / (P.sustain ? 3 : 1.2)) * (1 - .33 * QUIET(t)); L[i] = Math.tanh(L[i]) * f; R[i] = Math.tanh(R[i]) * f; peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i])); }
const pcm = Buffer.alloc(44 + N * 4);
pcm.write('RIFF', 0); pcm.writeUInt32LE(36 + N * 4, 4); pcm.write('WAVEfmt ', 8); pcm.writeUInt32LE(16, 16);
pcm.writeUInt16LE(1, 20); pcm.writeUInt16LE(2, 22); pcm.writeUInt32LE(SR, 24); pcm.writeUInt32LE(SR * 4, 28);
pcm.writeUInt16LE(4, 32); pcm.writeUInt16LE(16, 34); pcm.write('data', 36); pcm.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) { pcm.writeInt16LE(Math.round(L[i] / peak * 0.8 * 32767), 44 + i * 4); pcm.writeInt16LE(Math.round(R[i] / peak * 0.8 * 32767), 46 + i * 4); }
mkdirSync(dirname(OUT), { recursive: true });
const tmp = mkdtempSync(join(dirname(OUT), 'music_'));
try {
  const mix = join(tmp, 'mix.wav'); writeFileSync(mix, pcm);
  const LN = 'loudnorm=I=-14:TP=-2.5:LRA=11';
  const probe = spawnSync('ffmpeg', ['-hide_banner', '-i', mix, '-af', LN + ':print_format=json', '-f', 'null', '-'], { encoding: 'utf8' }).stderr;
  const m = JSON.parse(probe.slice(probe.lastIndexOf('{'), probe.lastIndexOf('}') + 1));
  const ln2 = `${LN}:measured_I=${m.input_i}:measured_LRA=${m.input_lra}:measured_TP=${m.input_tp}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`;
  const r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', mix, '-af', ln2, '-ar', String(SR), ...(OUT.endsWith('.wav') ? [] : ['-c:a', 'aac', '-b:a', '192k']), OUT], { stdio: 'inherit' });
  if (r.status !== 0) throw new Error('ffmpeg loudnorm failed');
} finally { rmSync(tmp, { recursive: true, force: true }); }
console.log('wrote', OUT);
