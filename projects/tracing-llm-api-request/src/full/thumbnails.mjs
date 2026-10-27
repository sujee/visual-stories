// YouTube thumbnails for the full video (16:9, 1280x720, each under 2 MB), rendered in headless Chromium: big type over a clean
// frame of the video (the whole map, the recap's big number) or a glowing lightning bolt.
//
//   node src/full/thumbnails.mjs [--out thumbnails]
//
// Writes <out>/tracing-llm-api-request-thumbnail-full-<design>-16x9.png. Key content stays clear of the bottom-right corner
// (YouTube's duration badge). There is no 9:16 version: the Short for this story is the promo's.
import { chromium } from 'playwright';
import { readFileSync, mkdirSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const arg = (name, def) => { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : def; };
const OUT = resolve(arg('out', 'thumbnails'));
mkdirSync(OUT, { recursive: true });
const font = f => readFileSync(join(here, '../../assets/fonts', f)).toString('base64');
const BOLD = font('JetBrainsMono-Bold.ttf'), REG = font('JetBrainsMono-Regular.ttf');
const TW = 1280, TH = 720;

// [design, headline lines, the accent line under it (cyan), an amber chip or null, the picture]
//   picture: { frame: seconds, crop: [x, y, w, h] } a frame of the video; or { bolt: true }
const DESIGNS = [
  ['question', ['What happens', 'when we call', 'an LLM API?'], 'one request, traced to the GPU', null, { frame: 'overview', crop: [820, 30, 1100, 780] }],
  ['optimize', ['5 tricks that', 'make LLMs', 'fast'], 'caching · batching · KV cache · disaggregated prefill · speculation', 'OPTIMIZATION', { bolt: true }],
  ['time', ['Where does', 'the time go?'], 'one request, to the GPU and back', 'first token  0.42 s', { frame: 'recap', crop: [300, 120, 1320, 560] }],
];
const BOLT = '<svg viewBox="-60 -70 120 140" width="__W__" height="__H__"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFC233"/><stop offset=".5" stop-color="#FFF6D0"/><stop offset="1" stop-color="#FFC233"/></linearGradient></defs><polygon points="12,-52 -28,6 -4,6 -14,52 30,-8 4,-8" fill="url(#g)" stroke="#FFE9A8" stroke-width="3" stroke-linejoin="round" style="filter: drop-shadow(0 0 18px #FFC233)"/></svg>';

const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--font-render-hinting=none'] });
const src = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await src.goto(pathToFileURL(join(here, 'full2d.html')).href + '?capture');
await src.waitForFunction(() => window.__ready === true);
const times = await src.evaluate(() => window.THUMB_FRAMES);
const frames = {};
for (const [name, t] of Object.entries(times)) { await src.evaluate(x => window.seek(x), t); frames[name] = (await src.screenshot({ type: 'png' })).toString('base64'); }
await src.close();

for (const [design, lines, accent, chip, pic] of DESIGNS) {
  const page = await browser.newPage({ viewport: { width: TW, height: TH } });
  let picture = '';
  if (pic.bolt) picture = `<div class="bolt">${BOLT.replace('__W__', 420).replace('__H__', 490)}</div>`;
  else {
    const [cx, cy, cw, ch] = pic.crop;
    picture = `<div class="bg"><div style="width:${cw}px;height:${ch}px;background:url(data:image/png;base64,${frames[pic.frame]}) -${cx}px -${cy}px;transform:scale(${620 / cw});transform-origin:0 0"></div></div>`;
  }
  await page.setContent(`<!doctype html><style>
    @font-face { font-family: JB; font-weight: 700; src: url(data:font/ttf;base64,${BOLD}); }
    @font-face { font-family: JB; font-weight: 400; src: url(data:font/ttf;base64,${REG}); }
    html, body { margin: 0; width: ${TW}px; height: ${TH}px; overflow: hidden; background: #060A13; font-family: JB; }
    .bg { position: absolute; left: 640px; top: 110px; width: 620px; height: 500px; overflow: hidden;
          -webkit-mask-image: linear-gradient(90deg, transparent 0%, #000 22%, #000 85%, transparent 100%); }
    .bolt { position: absolute; left: 700px; top: 110px; }
    .txt { position: absolute; left: 60px; top: 0; bottom: 0; width: 640px; display: flex; flex-direction: column; justify-content: center; }
    h1 { margin: 0; color: #EAF2FF; font-size: 76px; line-height: 1.08; letter-spacing: -2px; font-weight: 700; text-shadow: 0 0 28px rgba(59,228,255,.35); }
    .acc { margin-top: 26px; color: #3BE4FF; font-size: 28px; max-width: 600px; line-height: 1.3; }
    .chip { display: inline-block; margin-top: 30px; padding: 10px 22px; color: #FFB547; border: 3px solid #FFB547; border-radius: 16px;
            font-size: 36px; font-weight: 700; white-space: pre; box-shadow: 0 0 24px rgba(255,181,71,.35); align-self: flex-start; }
  </style>${picture}<div class="txt"><h1>${lines.join('<br>')}</h1><div class="acc">${accent}</div>${chip ? `<div class="chip">${chip}</div>` : ''}</div>`);
  await page.evaluate(() => document.fonts.ready);
  const file = join(OUT, `tracing-llm-api-request-thumbnail-full-${design}-16x9.png`);
  await page.screenshot({ path: file, type: 'png' });
  await page.close();
  const mb = statSync(file).size / 2 ** 20;
  if (mb >= 2) { console.error(`thumbnail over 2 MB (${mb.toFixed(2)} MB): ${file}`); process.exit(1); }
  console.log('wrote', file, `(${mb.toFixed(2)} MB)`);
}
await browser.close();
