// YouTube thumbnails for the promo, rendered in headless Chromium: big type over a clean 3D frame of the promo (no
// stopwatch, titles or timeline), and "path": client -> every stage -> the GPU, with each stage's (example) time.
//
//   node src/promo/thumbnails.mjs [--out thumbnails]
//
// Writes <out>/tracing-llm-api-request-thumbnail-promo-<design>-<aspect>.png: 1280x720 (16x9) and 1080x1920 (9x16),
// each under 2 MB. Key content stays clear of the bottom-right corner (YouTube's duration badge).
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

// [aspect, thumbnail size, promo frame size, when (real seconds: the first token leaving the KV cache)]
const ASPECTS = [['16x9', 1280, 720, 1920, 1080, 23.6], ['9x16', 1080, 1920, 1080, 1920, 24.0]];
// [design, headline lines, the accent line under it (cyan), an amber chip or null]
const DESIGNS = [
  ['question', ['What happens', 'when you call', 'an LLM API?'], 'from your code to the GPU and back', null],
  ['time', ['Where does', 'the time go?'], 'one LLM request, traced', 'first token  0.42 s'],
];

async function shoot(page, design, aspect) {
  await page.evaluate(() => document.fonts.ready);
  const file = join(OUT, `tracing-llm-api-request-thumbnail-promo-${design}-${aspect}.png`);
  await page.screenshot({ path: file, type: 'png' });
  await page.close();
  const mb = statSync(file).size / 2 ** 20;
  if (mb >= 2) { console.error(`thumbnail over 2 MB (${mb.toFixed(2)} MB): ${file}`); process.exit(1); }
  console.log('wrote', file, `(${mb.toFixed(2)} MB)`);
}

const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--font-render-hinting=none', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
for (const [aspect, tw, th, fw, fh, at] of ASPECTS) {
  const portrait = aspect === '9x16';
  const src = await browser.newPage({ viewport: { width: fw, height: fh } });
  await src.goto(pathToFileURL(join(here, 'promo.html')).href + '?capture&3d&clean' + (portrait ? '&portrait' : ''));
  await src.waitForFunction(() => window.__ready === true);
  await src.evaluate(t => window.seek(t), at);
  const bg = (await src.screenshot({ type: 'png' })).toString('base64');
  const stages = await src.evaluate(() => window.STAGE_TIMES), total = await src.evaluate(() => window.TOTAL);   // [name, s, colour], as on the timeline
  await src.close();

  for (const [design, lines, accent, chip] of DESIGNS) {
    const page = await browser.newPage({ viewport: { width: tw, height: th } });
    const size = portrait ? 116 : 72;
    await page.setContent(`<!doctype html><style>
      @font-face { font-family: JB; font-weight: 700; src: url(data:font/ttf;base64,${BOLD}); }
      @font-face { font-family: JB; font-weight: 400; src: url(data:font/ttf;base64,${REG}); }
      html, body { margin: 0; width: ${tw}px; height: ${th}px; overflow: hidden; background: #060A13; font-family: JB; }
      /* the frame, placed so the token row fills the half the text leaves free (16:9: the right half; 9:16: below) */
      .bg { position: absolute; ${portrait ? 'left: 0; top: 420px; width: 1080px;' : 'left: 470px; top: 110px; width: 1000px;'}
            -webkit-mask-image: linear-gradient(${portrait ? '180deg' : '90deg'}, transparent 0%, #000 18%, #000 85%, transparent 100%); }
      .txt { position: absolute; ${portrait ? 'left: 80px; right: 80px; top: 150px;' : 'left: 60px; top: 0; bottom: 0; width: 580px; display: flex; flex-direction: column; justify-content: center;'} }
      h1 { margin: 0; color: #EAF2FF; font-size: ${size}px; line-height: 1.08; letter-spacing: -2px; font-weight: 700;
           text-shadow: 0 0 28px rgba(59,228,255,.35); }
      .acc { margin-top: ${portrait ? 40 : 26}px; color: #3BE4FF; font-size: ${portrait ? 50 : 30}px; font-weight: 400; }
      .chip { display: inline-block; margin-top: ${portrait ? 44 : 30}px; padding: ${portrait ? '14px 28px' : '10px 22px'}; color: #FFB547;
              border: 3px solid #FFB547; border-radius: 16px; font-size: ${portrait ? 48 : 36}px; font-weight: 700; white-space: pre;
              box-shadow: 0 0 24px rgba(255,181,71,.35); align-self: flex-start; }
    </style><img class="bg" src="data:image/png;base64,${bg}">
    <div class="txt"><h1>${lines.join('<br>')}</h1><div class="acc">${accent}</div>${chip ? `<div class="chip">${chip}</div>` : ''}</div>`);
    await shoot(page, design, aspect);
  }

  // path: client -> network ... queue -> GPU (prefill, decode), each stage's time below it
  const page = await browser.newPage({ viewport: { width: tw, height: th } });
  const fmt = v => v < 1 ? `${Math.round(v * 1000)} ms` : `${v.toFixed(2)} s`;
  const box = ([name, v, c]) => `<div class="st"><div class="nm" style="color:${c};border-color:${c}">${name}</div><div class="tm">${fmt(v)}</div></div>`;
  const onGpu = stages.filter(([n]) => n === 'prefill' || n === 'decode'), before = stages.filter(s => !onGpu.includes(s));
  const arrow = '<div class="ar"></div>';
  await page.setContent(`<!doctype html><style>
    @font-face { font-family: JB; font-weight: 700; src: url(data:font/ttf;base64,${BOLD}); }
    @font-face { font-family: JB; font-weight: 400; src: url(data:font/ttf;base64,${REG}); }
    html, body { margin: 0; width: ${tw}px; height: ${th}px; overflow: hidden; font-family: JB; color: #E8EEF9;
                 background: radial-gradient(ellipse at 50% ${portrait ? 55 : 60}%, #0F1C36 0%, #060A13 70%); }
    h1 { position: absolute; margin: 0; ${portrait ? 'left: 80px; right: 80px; top: 110px; font-size: 100px;' : 'left: 0; right: 0; top: 52px; text-align: center; font-size: 72px;'}
         line-height: 1.08; letter-spacing: -2px; font-weight: 700; text-shadow: 0 0 28px rgba(59,228,255,.35); }
    h1 small { display: block; margin-top: ${portrait ? 24 : 14}px; font-size: ${portrait ? 54 : 40}px; letter-spacing: 0; color: #3BE4FF; text-shadow: none; }
    .row { position: absolute; display: flex; ${portrait
      ? 'flex-direction: column; align-items: center; left: 0; right: 0; top: 540px;'
      : 'align-items: flex-start; left: 0; right: 0; top: 300px; justify-content: center;'} }
    /* 16:9: every box sits on one line, level with the boxes inside the GPU (its padding + border) */
    .row > .st, .row > .end { ${portrait ? '' : 'margin-top: 47px;'} }
    .st { display: flex; ${portrait ? 'flex-direction: row; align-items: center; gap: 28px; width: 760px;' : 'flex-direction: column; align-items: center; gap: 14px; width: 124px;'} }
    .nm { border: 3px solid; border-radius: 14px; padding: 9px 0; font-weight: 700; font-size: ${portrait ? 50 : 23}px; line-height: 1.3;
          text-align: center; width: ${portrait ? 420 : 120}px; background: rgba(13,22,40,.9); }
    .tm { font-size: ${portrait ? 52 : 26}px; font-weight: 700; color: #E8EEF9; ${portrait ? 'width: 312px;' : ''} }
    .end { box-sizing: border-box; border: 3px solid #E8EEF9; border-radius: 14px; padding: 9px 0; width: ${portrait ? 420 : 104}px; text-align: center;
           font-weight: 700; font-size: ${portrait ? 50 : 23}px; line-height: 1.3; ${portrait ? 'margin-right: 340px;' : ''} }
    /* connectors with an arrowhead, level with the boxes' centres (16:9) or under them (9:16) */
    .ar { position: relative; flex: none; background: #4A5E88; ${portrait
      ? 'width: 4px; height: 40px; margin-right: 340px; margin-bottom: 10px;'
      : 'height: 3px; width: 18px; margin: 71px 8px 0 0;'} }
    .ar::after { content: ''; position: absolute; border: solid transparent; ${portrait
      ? 'left: -8px; bottom: -14px; border-width: 14px 10px 0; border-top-color: #4A5E88;'
      : 'right: -10px; top: -6px; border-width: 7.5px 0 7.5px 11px; border-left-color: #4A5E88;'} }
    .gpu { position: relative; display: flex; ${portrait ? 'flex-direction: column; gap: 18px; padding: 70px 24px 24px;' : 'gap: 10px; padding: 44px 14px 16px;'}
           border: 3px solid #3BE4FF; border-radius: 18px; box-shadow: 0 0 34px rgba(59,228,255,.3); background: rgba(59,228,255,.05); }
    .gpu::before { content: 'GPU'; position: absolute; ${portrait ? 'left: 24px; top: 14px; font-size: 40px;' : 'left: 14px; top: 8px; font-size: 22px;'} color: #3BE4FF; font-weight: 700; }
    .total { position: absolute; ${portrait ? 'left: 80px; top: 1730px;' : 'left: 64px; top: 560px;'} font-size: ${portrait ? 60 : 34}px; font-weight: 700; color: #FFB547; }
    .total small { display: block; margin-top: 8px; font-size: ${portrait ? 30 : 20}px; font-weight: 400; color: #7C8CAE; }
  </style>
  <h1>${portrait ? 'Tracing an LLM<br>API Request' : 'Tracing an LLM API Request'}<small>from client to GPU and back</small></h1>
  <div class="row"><div class="end">client</div>${arrow}${before.map(box).join(arrow)}${arrow}<div class="gpu">${onGpu.map(box).join('')}</div></div>
  <div class="total">total ${fmt(total)}<small>example timings</small></div>`);
  await shoot(page, 'path', aspect);
}
await browser.close();
