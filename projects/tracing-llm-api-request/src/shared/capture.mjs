// Render a page (src/promo/promo.html by default, or src/full/full.html) to a silent mp4 by stepping the animation frame by frame in headless Chromium.
//
//   node src/shared/capture.mjs --out video.mp4 --width 3840 --height 2160 [--fps 30] [--workers N] [--portrait] [--3d] [--page src/full/full.html]
//   ... --segments 10 --cache workspace/full/cache/720p   (render in segments and cache them: only the segments whose frames changed are
//                                                           rendered again, the rest come from the cache; --no-cache renders everything.
//                                                           The page may set window.SCENE_STARTS (seconds): segments never cross a scene start
//                                                           (a longer scene is cut every N s) and are keyed by their frames, not their position,
//                                                           so a scene that only moved in time is reused. Without it, the video is cut every N s.)
//   ... --to 178.6                                          (with --segments: only the video up to this time, which must be a scene start; for a draft of the first part)
//   ... --report workspace/full/preview/v1/changed.txt     (with --segments: write what changed, as time ranges with scene names, to this file; it is also printed)
//   ... --plan                                              (with --segments and --cache: list which segments would be rendered, and render nothing)
//   node src/shared/capture.mjs --print-chapters                                            (the page's YouTube chapters and duration, JSON: window.CHAPTERS)
//   node src/shared/capture.mjs --print-duration                                            (the promo's length in seconds)
//   node src/shared/capture.mjs --print-cues                                                (music cue times, JSON: the page's window.MUSIC_CUES, or the promo's)
//   node src/shared/capture.mjs --out frame.png --width 1920 --height 1080 --at 12.5|end [--portrait] [--3d]   (one frame; `end` = the last 0.1 s)
//
// Deterministic: promo.html is a pure function of time (window.seek(t)); nothing is fetched at render time.
// Set CHROME_PATH to use a system Chrome instead of Playwright's bundled Chromium.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, rmSync, existsSync, readdirSync, renameSync, statSync, utimesSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { cpus } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const arg = (name, def) => { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : def; };
const out = resolve(arg('out', 'workspace/tmp/video.mp4'));
const W = +arg('width', 1920), H = +arg('height', 1080), FPS = +arg('fps', 30);
const WORKERS = +arg('workers', Math.min(6, Math.max(1, cpus().length >> 1)));
const AT = arg('at', null);
const PORTRAIT = process.argv.includes('--portrait');
const THREED = process.argv.includes('--3d');                // the 3D version (WebGL, rendered in software for identical frames)
mkdirSync(dirname(out), { recursive: true });

// The page is laid out at up to 1920 CSS px on its long side; a device scale factor reaches the target pixel size
// (3840x2160 = 2x of 1920x1080, 2160x3840 = 2x of 1080x1920).
const dsf = Math.max(1, Math.round(Math.max(W, H) / 1920)), vw = Math.round(W / dsf), vh = Math.round(H / dsf);
const url = pathToFileURL(resolve(arg('page', 'src/promo/promo.html'))).href + '?capture' + (PORTRAIT ? '&portrait' : '') + (THREED ? '&3d' : '');

let TMP_DIR = null;                                             // chunk folder, removed on every exit path
const cleanup = () => { if (TMP_DIR) try { rmSync(TMP_DIR, { recursive: true, force: true }); } catch {} };
const KIDS = [];                                                // the chunk ffmpegs, stopped if the capture fails
const fail = async () => { KIDS.forEach(k => k.kill()); await browser.close().catch(() => {}); cleanup(); process.exit(1); };
const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || undefined,
  args: ['--force-color-profile=srgb', '--hide-scrollbars', '--font-render-hinting=none', ...(THREED ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : [])],
});
async function openPage(pw = vw, ph = vh, scale = dsf) {
  const ctx = await browser.newContext({ viewport: { width: pw, height: ph }, deviceScaleFactor: scale, colorScheme: 'light', reducedMotion: 'no-preference' });
  const page = await ctx.newPage();
  page.on('pageerror', e => { console.error('page error:', e.message); fail(); });
  await page.goto(url);
  await page.waitForFunction(() => window.__ready === true);
  return page;
}

// --- one still ---
if (AT !== null) {
  const page = await openPage();
  const at = AT === 'end' ? (await page.evaluate(() => window.DURATION)) - 0.1 : +AT;   // `end`: the settled final scene, whatever the story's length
  await page.evaluate(t => window.seek(t), at);
  await page.screenshot({ path: out, type: 'png' });
  await browser.close();
  process.exit(0);
}

const first = await openPage();
if (process.argv.includes('--print-cues')) {               // when the music's sections start: the drop, the stop, the title card
  console.log(JSON.stringify(await first.evaluate(() => window.MUSIC_CUES || ({ drop: realAt(4), stop: realAt(22), outro: realAt(26) })))); await browser.close(); process.exit(0);   // a page may publish its own cues
}
if (process.argv.includes('--print-chapters')) { console.log(JSON.stringify(await first.evaluate(() => ({ chapters: window.CHAPTERS, duration: window.DURATION })))); await browser.close(); process.exit(0); }   // the page's YouTube chapters
if (process.argv.includes('--print-duration')) { console.log(await first.evaluate(() => window.DURATION)); await browser.close(); process.exit(0); }
const duration = await first.evaluate(() => window.DURATION);


const N = Math.round(duration * FPS);
const SEG = +arg('segments', 0), CACHE = arg('cache', null) && resolve(arg('cache'));
const sha = s => createHash('sha1').update(s).digest('hex');
console.log(`${N} frames (${duration.toFixed(2)} s) at ${W}x${H}, ${FPS} fps, ${WORKERS} workers`);

const tmp = join(dirname(out), `chunks_${process.pid}`);
mkdirSync(tmp, { recursive: true });
TMP_DIR = tmp;
const pool = [first];                                           // one open page per worker, reused across segments
const joinFiles = (files, to, name) => {
  const list = join(tmp, name);
  writeFileSync(list, files.map(f => `file '${f.replaceAll("'", "'\\''")}'`).join('\n'));
  return new Promise((res, rej) => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', to], { stdio: 'inherit' })
    .on('exit', c => c === 0 ? res() : rej(new Error('concat failed'))));
};

// Frames F0..F1-1 -> one mp4. The frames are split into contiguous chunks; each worker pipes its PNGs straight into its own
// ffmpeg (near-lossless intermediate), then the chunks are joined without re-encoding.
async function captureFrames(F0, F1, to) {
  const per = Math.ceil((F1 - F0) / WORKERS), dir = join(tmp, `c_${F0}`), jobs = [];
  mkdirSync(dir, { recursive: true });
  for (let k = 0; k < WORKERS; k++) {
    const a = F0 + k * per, b = Math.min(F1, a + per);
    if (a >= b) break;
    const file = join(dir, `chunk_${String(k).padStart(2, '0')}.mp4`);
    jobs.push((async () => {
      const page = pool[k] ??= await openPage();
      const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(FPS), '-i', '-',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-pix_fmt', 'yuv420p', file], { stdio: ['pipe', 'inherit', 'inherit'] });
      KIDS.push(ff);
      const done = new Promise((res, rej) => { ff.on('exit', c => c === 0 ? res() : rej(new Error('ffmpeg chunk failed'))); });
      ff.stdin.on('error', () => {});                              // a dead ffmpeg is reported through `done`, not as an unhandled EPIPE
      for (let i = a; i < b; i++) {
        await page.evaluate(t => window.seek(t), i / FPS);
        const png = await page.screenshot({ type: 'png' });
        if (!ff.stdin.write(png)) await Promise.race([new Promise(r => ff.stdin.once('drain', r)), done]);
      }
      ff.stdin.end();
      await done;
      return file;
    })());
  }
  let files;
  try { files = await Promise.all(jobs); } catch (e) { console.error('capture failed:', e.message); await fail(); }
  await joinFiles(files, to, `list_${F0}.txt`);
}

// The segments: one per scene (a scene longer than SEG seconds is cut into SEG-second pieces from its start), so a change
// in one scene, or in a scene's length, leaves the segments around it exactly as they were.
const STRIDE = 3;
async function segmentsOf() {
  const starts = (await first.evaluate(() => window.SCENE_STARTS || [0])).map(t => Math.round(t * FPS)).filter(f => f >= 0 && f < N);
  const cuts = [...new Set([0, ...starts, N])].sort((a, b) => a - b), max = Math.round(SEG * FPS), segs = [];
  for (let c = 0; c < cuts.length - 1; c++) for (let f = cuts[c]; f < cuts[c + 1]; f += max) segs.push([f, Math.min(cuts[c + 1], f + max)]);
  return segs;
}
// A fingerprint of every third frame of a segment, from a small render (640x360): the same pixels give the same hash, so a
// segment whose fingerprints are unchanged does not need to be rendered again. (A change that lives in under 3 frames, 0.1 s,
// can slip through: bypass the cache with --no-cache.)
async function fingerprints(segs) {
  const samples = segs.flatMap(([a, b], si) => Array.from({ length: Math.ceil((b - a) / STRIDE) }, (_, m) => [si, a + m * STRIDE]));
  const per = Math.ceil(samples.length / WORKERS), fp = new Array(samples.length);
  await Promise.all(Array.from({ length: WORKERS }, async (_, k) => {
    const a = k * per, b = Math.min(samples.length, a + per); if (a >= b) return;
    const page = await openPage(640, 360, 1);
    for (let i = a; i < b; i++) { await page.evaluate(t => window.seek(t), samples[i][1] / FPS); fp[i] = sha(await page.screenshot({ type: 'png' })).slice(0, 12); }
    await page.context().close();
  }));
  const bySeg = segs.map(() => []); samples.forEach(([si], i) => bySeg[si].push(fp[i]));
  return bySeg;
}

const mmss = f => { const t = Math.round(f / FPS), m = Math.floor(t / 60), s = t % 60; return `${m}:${String(s).padStart(2, '0')}`; };
async function describe(ranges, total, what) {           // "0:45-0:49  title: blocks", merged where the segments touch
  const names = await first.evaluate(() => window.SCENE_NAMES || null), starts = await first.evaluate(() => window.SCENE_STARTS || null);
  if (!ranges.length) return [`${what}: nothing changed since the last render (all ${total} segments reused)`];
  const merged = ranges.reduce((acc, [a, b]) => (acc.length && acc.at(-1)[1] === a ? acc.at(-1)[1] = b : acc.push([a, b]), acc), []);
  const lines = merged.map(([a, b]) => {
    const sc = names && starts ? names.filter((_, i) => starts[i] * FPS < b - 1 && (starts[i + 1] ?? Infinity) * FPS > a + 1).join('; ') : '';
    return `${mmss(a)}-${mmss(b)}  ${sc}`.trimEnd();
  });
  const all = merged.length === 1 && merged[0][0] === 0 && merged[0][1] >= N - 2;
  return [`${what}: ${all ? 'everything (no earlier render to compare with, or the cache was bypassed)' : `${ranges.length} of ${total} segments`}`, ...(all ? [] : lines)];
}
try {
  if (SEG > 0 && CACHE) {
    mkdirSync(CACHE, { recursive: true });
    const TO = arg('to', null), segs = (await segmentsOf()).filter(([, b]) => TO === null || b <= Math.round(+TO * FPS)), fps = await fingerprints(segs), parts = []; let reused = 0, rendered = 0, todo = 0;
    const PLAN = process.argv.includes('--plan'), changed = [];
    for (const [si, [F0, F1]] of segs.entries()) {
      const key = sha(fps[si].join('') + `|${W}x${H}|${FPS}|${F1 - F0}|${STRIDE}|${THREED}`).slice(0, 20), file = join(CACHE, `seg_${key}.mp4`);
      if (existsSync(file) && !process.argv.includes('--no-cache')) { reused++; if (!PLAN) utimesSync(file, new Date(), new Date()); }
      else if (PLAN) { rendered++; todo += F1 - F0; changed.push([F0, F1]); console.log(`would render segment ${si + 1}/${segs.length} (${(F0 / FPS).toFixed(1)}-${(F1 / FPS).toFixed(1)} s)`); }
      else {
        console.log(`rendering segment ${si + 1}/${segs.length} (${(F0 / FPS).toFixed(1)}-${(F1 / FPS).toFixed(1)} s)`);
        await captureFrames(F0, F1, file + '.part.mp4'); renameSync(file + '.part.mp4', file); rendered++; changed.push([F0, F1]);
      }
      parts.push(file);
    }
    if (PLAN) { console.log(`plan: ${segs.length} segments, ${reused} reused, ${rendered} to render (${(todo / FPS).toFixed(0)} s of video)`); console.log((await describe(changed, segs.length, 'would change')).join('\n')); await browser.close(); cleanup(); process.exit(0); }
    for (const f of readdirSync(CACHE)) {                      // the old position-keyed segments, and any nobody asked for in two weeks
      const full = join(CACHE, f);
      if (!parts.includes(full) && (/^seg_\d\d_/.test(f) || Date.now() - statSync(full).mtimeMs > 14 * 864e5)) rmSync(full, { force: true });
    }
    console.log(`segments: ${parts.length} (${reused} reused from the cache, ${rendered} rendered)`);
    const rep = await describe(changed, parts.length, 'changed since the last render'); console.log(rep.join('\n'));
    if (arg('report', null)) { mkdirSync(dirname(resolve(arg('report'))), { recursive: true }); writeFileSync(resolve(arg('report')), rep.join('\n') + '\n'); }
    await joinFiles(parts, out, 'list_all.txt');
  } else await captureFrames(0, N, out);
} finally { await browser.close().catch(() => {}); cleanup(); }
console.log('wrote', out);
