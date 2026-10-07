// Render src/story.html to a silent mp4 by stepping the animation frame by frame in headless Chromium.
//
//   node src/capture.mjs --out video.mp4 --width 3840 --height 2160 [--fps 30] [--workers N] [--portrait]
//   node src/capture.mjs --print-duration                                            (the story's length in seconds)
//   node src/capture.mjs --out frame.png --width 1920 --height 1080 --at 12.5|end [--portrait] [--still] [--thumb lineup|question]
//                                                                  (one frame; `end` = the last 0.1 s of the story; --still drops the confetti)
//
// Deterministic: story.html is a pure function of time (window.seek(t)); nothing is fetched at render time.
// Set CHROME_PATH to use a system Chrome instead of Playwright's bundled Chromium.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
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
const THUMB = arg('thumb', null);                          // --thumb lineup|question: a YouTube thumbnail design
const STILL = process.argv.includes('--still');          // clean frame for screenshots: no confetti
mkdirSync(dirname(out), { recursive: true });

// The page is laid out at up to 1920 CSS px on its long side; a device scale factor reaches the target pixel size
// (3840x2160 = 2x of 1920x1080, 2160x3840 = 2x of 1080x1920).
const dsf = Math.max(1, Math.round(Math.max(W, H) / 1920)), vw = Math.round(W / dsf), vh = Math.round(H / dsf);
const url = pathToFileURL(join(here, 'story.html')).href + '?capture' + (PORTRAIT ? '&portrait' : '') + (STILL ? '&still' : '') + (THUMB ? `&thumb=${THUMB}` : '');

let TMP_DIR = null;                                             // chunk folder, removed on every exit path
const cleanup = () => { if (TMP_DIR) try { rmSync(TMP_DIR, { recursive: true, force: true }); } catch {} };
const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || undefined,
  args: ['--force-color-profile=srgb', '--hide-scrollbars', '--font-render-hinting=none'],
});
async function openPage() {
  const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: dsf, colorScheme: 'light', reducedMotion: 'no-preference' });
  const page = await ctx.newPage();
  page.on('pageerror', e => { console.error('page error:', e.message); cleanup(); process.exit(1); });
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
if (process.argv.includes('--print-duration')) { console.log(await first.evaluate(() => window.DURATION)); await browser.close(); process.exit(0); }
const duration = await first.evaluate(() => window.DURATION);


const N = Math.round(duration * FPS);
console.log(`capturing ${N} frames (${(duration).toFixed(2)} s) at ${W}x${H}, ${FPS} fps, ${WORKERS} workers`);

// Frames are split into contiguous chunks; each worker pipes its PNGs straight into its own ffmpeg (near-lossless
// intermediate), then the chunks are joined without re-encoding.
const tmp = join(dirname(out), `chunks_${process.pid}`);
mkdirSync(tmp, { recursive: true });
TMP_DIR = tmp;
const per = Math.ceil(N / WORKERS);
const jobs = [];
for (let k = 0; k < WORKERS; k++) {
  const a = k * per, b = Math.min(N, a + per);
  if (a >= b) break;
  const file = join(tmp, `chunk_${String(k).padStart(2, '0')}.mp4`);
  jobs.push((async () => {
    const page = k === 0 ? first : await openPage();
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(FPS), '-i', '-',
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-pix_fmt', 'yuv420p', file], { stdio: ['pipe', 'inherit', 'inherit'] });
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
try { files = await Promise.all(jobs); }
catch (e) { console.error('capture failed:', e.message); await browser.close().catch(() => {}); cleanup(); process.exit(1); }
await browser.close();

const list = join(tmp, 'list.txt');
writeFileSync(list, files.map(f => `file '${f}'`).join('\n'));
await new Promise((res, rej) => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out], { stdio: 'inherit' })
  .on('exit', c => c === 0 ? res() : rej(new Error('concat failed'))));
cleanup();
console.log('wrote', out);
