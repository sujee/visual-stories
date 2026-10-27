// A short clip (or one still) of a page, for checking a note without a render.
//
//   node src/shared/clip.mjs --page src/full/full2d.html --range 45.3-49.9 [--range 63-67] --out workspace/tmp/clip.mp4 [--width 1280 --height 720] [--fps 30] [--3d] [--portrait]
//   node src/shared/clip.mjs --page src/full/full2d.html --at 78.5 --out workspace/tmp/frame.png
//
// Each --range is start-end in seconds; several ranges are joined into one mp4 (no audio). Same page contract as capture.mjs
// (window.seek, window.__ready). The size is the real pixel size (default 1280x720), so a clip is quick.
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2), all = n => args.flatMap((a, i) => a === '--' + n ? [args[i + 1]] : []), arg = (n, d) => all(n)[0] ?? d;
const W = +arg('width', 1280), H = +arg('height', 720), FPS = +arg('fps', 30), AT = arg('at', null), out = resolve(arg('out', AT !== null ? 'workspace/tmp/frame.png' : 'workspace/tmp/clip.mp4'));
const ranges = all('range').map(r => r.split('-').map(Number));
if (AT === null && !ranges.length) { console.error('give --range start-end (seconds), or --at t for one frame'); process.exit(2); }
mkdirSync(dirname(out), { recursive: true });
const THREED = args.includes('--3d'), PORTRAIT = args.includes('--portrait');
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--force-color-profile=srgb', '--hide-scrollbars', '--font-render-hinting=none', ...(THREED ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] : [])] });
const dsf = Math.max(1, Math.round(Math.max(W, H) / 1920));          // the page lays out at up to 1920 CSS px, as in capture.mjs
const page = await (await browser.newContext({ viewport: { width: Math.round(W / dsf), height: Math.round(H / dsf) }, deviceScaleFactor: dsf })).newPage();
page.on('pageerror', e => { console.error('page error:', e.message); process.exit(1); });
await page.goto(pathToFileURL(resolve(arg('page', 'src/promo/promo.html'))).href + '?capture' + (PORTRAIT ? '&portrait' : '') + (THREED ? '&3d' : ''));
await page.waitForFunction(() => window.__ready === true);
if (AT !== null) {
  const t = AT === 'end' ? (await page.evaluate(() => window.DURATION)) - 0.1 : +AT;
  await page.evaluate(x => window.seek(x), t); await page.screenshot({ path: out, type: 'png' });
} else {
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-c:v', 'png', '-framerate', String(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  ff.stdin.on('error', () => {});
  for (const [a, b] of ranges) for (let i = 0; i < Math.round((b - a) * FPS); i++) { await page.evaluate(x => window.seek(x), a + i / FPS); ff.stdin.write(await page.screenshot({ type: 'png' })); }
  ff.stdin.end(); await new Promise(r => ff.on('exit', r));
}
await browser.close();
console.log('wrote', out);
