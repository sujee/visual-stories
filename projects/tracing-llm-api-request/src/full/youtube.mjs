// Writes the chapter lines into youtube-publishing-full.md: everything between the line `Chapters:` and the next line `---` is replaced
// from the page's own timeline (window.CHAPTERS in src/full/full2d.html), so the chapters always match the render. The rest of the
// file is left untouched (it is edited by hand). YouTube shows chapters only if the first starts at 0:00, there are at least three,
// and each is at least 10 seconds: this checks all three and fails if one is broken.
//
//   node src/shared/capture.mjs --page src/full/full2d.html --print-chapters | node src/full/youtube.mjs [youtube-publishing-full.md]
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const file = resolve(process.argv[2] || 'youtube-publishing-full.md');
const { chapters, duration } = JSON.parse(readFileSync(0, 'utf8'));
const ts = t => { t = Math.floor(t); const h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60), s = t % 60; return (h ? `${h}:${String(m).padStart(2, '0')}` : `${m}`) + `:${String(s).padStart(2, '0')}`; };
const bad = [];
if (chapters.length < 3) bad.push('YouTube needs at least 3 chapters');
if (Math.floor(chapters[0][1]) !== 0) bad.push('the first chapter must start at 0:00');
chapters.forEach(([title, start], i) => { const end = i + 1 < chapters.length ? chapters[i + 1][1] : duration; if (Math.floor(end) - Math.floor(start) < 10) bad.push(`"${title}" lasts ${(end - start).toFixed(1)} s: each chapter needs at least 10 s`); });
if (bad.length) { console.error('chapters not written:\n  ' + bad.join('\n  ')); process.exit(1); }
const lines = readFileSync(file, 'utf8').split('\n'), a = lines.indexOf('Chapters:'), b = lines.indexOf('---', a + 1);
if (a < 0 || b < 0) { console.error(`${file}: no "Chapters:" line followed by "---"`); process.exit(1); }
lines.splice(a + 1, b - a - 1, ...chapters.map(([title, start]) => `${ts(start)} ${title}`));
writeFileSync(file, lines.join('\n'));
console.log(`wrote ${chapters.length} chapters to ${file}`);
