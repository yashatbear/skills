#!/usr/bin/env node
// /visual board composer: one real screenshot per option -> side-by-side PNG board(s).
// Usage: node render.mjs <spec.json> [--out <dir>]
// Prints one PNG path per line. Local only: Playwright from the browse skill, no network.
//
// Spec:
// { "ref": "optional label", "date": "optional", "question": "...", "why": "one line for the Rec",
//   "options": [ { "name": "Today", "image": "/abs/today.png", "note": "one line", "baseline": true,
//                  "zoom": {"x":0,"y":120,"w":390,"h":56} },          // optional, CSS px of the shot
//                { "name": "Fit all five", "image": "...", "note": "...", "rec": true } ] }
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, join, resolve, basename } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import os from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
// Playwright: $VISUAL_PLAYWRIGHT, else the sibling browse skill's install.
const PW = process.env.VISUAL_PLAYWRIGHT || resolve(HERE, "../browse/node_modules/playwright/index.mjs");
const MAX_COLS = 3; // more options -> more boards, so each shot stays phone-readable
const COL_W = 390; // CSS px per column; a 390px phone shot shows at 1:1

const die = (m) => (console.error(`visual: ${m}`), process.exit(2));
const args = process.argv.slice(2);
const outIdx = args.indexOf("--out");
const specPath = args.find((a, i) => !a.startsWith("--") && (outIdx < 0 || i !== outIdx + 1));
if (!specPath) die("usage: node render.mjs <spec.json> [--out <dir>]");
const spec = JSON.parse(readFileSync(specPath, "utf8"));
const specDir = dirname(resolve(specPath));
const outDir =
  outIdx >= 0 ? resolve(args[outIdx + 1]) : join(os.tmpdir(), "visual", process.env.CLAUDE_CODE_SESSION_ID || "manual");
mkdirSync(outDir, { recursive: true });

// ---- validate: a half-drawn decision is worse than none
if (!spec.question) die("spec.question is required");
if (!Array.isArray(spec.options) || spec.options.length < 2) die("spec.options needs 2+ entries");
if (spec.options.filter((o) => o.rec).length > 1) die("mark at most one option rec:true");
for (const o of spec.options) {
  if (!o.name) die("every option needs a name");
  if (!o.image) die(`option "${o.name}" needs an image (a real screenshot of the result)`);
  o.image = resolve(specDir, o.image);
  if (!existsSync(o.image)) die(`option "${o.name}": image not found: ${o.image}`);
}

const esc = (s) =>
  String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// Letters skip baselines: Today, A, B, C.
let n = 0;
for (const o of spec.options) o.letter = o.baseline ? "" : String.fromCharCode(65 + n++);

function card(o, natW) {
  const scale = COL_W / natW; // shots are drawn at column width
  const zoom = o.zoom
    ? (() => {
        const z = 2; // zoom crop shown at 2x of the column scale, capped to column width
        const k = Math.min(z, COL_W / (o.zoom.w * scale)) * scale;
        return `<div class="zoom" style="width:${o.zoom.w * k}px;height:${o.zoom.h * k}px">
          <img src="${pathToFileURL(o.image)}" style="width:${natW * k}px;left:${-o.zoom.x * k}px;top:${-o.zoom.y * k}px"></div>`;
      })()
    : "";
  return `<section class="card ${o.rec ? "rec" : ""} ${o.baseline ? "base" : ""}">
    <div class="head">${o.letter ? `<span class="letter">${o.letter}</span>` : ""}<h2>${esc(o.name)}</h2>${
      o.rec ? '<span class="badge">Rec</span>' : ""
    }</div>
    <div class="shot"><img src="${pathToFileURL(o.image)}"></div>
    ${zoom}
    ${o.note ? `<p class="note">${esc(o.note)}</p>` : ""}
  </section>`;
}

function page(opts, natW, part, parts) {
  const cols = opts.length;
  const rec = spec.options.find((o) => o.rec);
  const why =
    part === parts && rec && spec.why
      ? `<div class="why"><b>Rec: ${rec.letter ? rec.letter + ", " : ""}${esc(rec.name)}.</b> ${esc(spec.why)}</div>`
      : "";
  return `<!doctype html><html><head><meta charset="utf-8"><style>
:root{--bg:#1d2127;--fg:#e8eaed;--mid:#7a8594;--glass:rgba(232,234,237,.07);--line:rgba(232,234,237,.2);--dim:rgba(232,234,237,.66)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font:500 20px/1.35 "Helvetica Neue",Helvetica,Arial,sans-serif;padding:30px 28px 24px;width:${
    cols * (COL_W + 24) + (cols - 1) * 16 + 56
  }px}
.top{display:flex;justify-content:flex-start;align-items:baseline;color:var(--dim);font-size:16px}
.brand{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-weight:700;font-size:20px;color:var(--fg)}
h1{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-weight:700;letter-spacing:-.01em;font-size:31px;line-height:1.2;margin:4px 0 20px}
.grid{display:grid;grid-template-columns:repeat(${cols},${COL_W + 24}px);gap:16px;align-items:start}
.card{background:var(--glass);border:1.5px solid var(--line);border-radius:22px;padding:12px;display:flex;flex-direction:column;gap:10px}
.card.rec{border:3px solid var(--fg);padding:10.5px}
.card.base{opacity:.92}
.head{display:flex;align-items:center;gap:10px;padding:2px 4px 0;min-height:40px}
.letter{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-weight:700;font-size:19px;flex:0 0 38px;height:38px;border-radius:50%;border:1.5px solid var(--line);display:flex;align-items:center;justify-content:center}
.rec .letter{background:var(--fg);color:var(--bg);border-color:var(--fg)}
h2{font-size:23px;font-weight:700;line-height:1.15;flex:1}
.base h2{color:var(--dim)}
.badge{background:var(--fg);color:var(--bg);font-weight:700;font-size:16px;padding:4px 12px;border-radius:999px}
.shot{border-radius:14px;overflow:hidden;line-height:0}
.shot img{width:${COL_W}px;display:block}
.zoom{position:relative;overflow:hidden;border-radius:12px;outline:2px solid var(--fg);outline-offset:-1px;align-self:center}
.zoom img{position:absolute;max-width:none}
.note{font-size:19px;line-height:1.3;padding:0 4px 4px}
.why{margin-top:18px;padding:14px 18px;border-radius:16px;background:var(--glass);border:1.5px solid var(--line)}
.foot{margin-top:12px;color:var(--dim);font-size:14px;display:flex;justify-content:space-between;gap:16px}
</style></head><body>
<div class="top"><span>${esc(spec.ref || "")}${parts > 1 ? ` · ${part}/${parts}` : ""}</span></div>
<h1>${esc(spec.question)}</h1>
<div class="grid">${opts.map((o) => card(o, natW[o.image])).join("")}</div>
${why}
<div class="foot"><span>${esc(spec.source || "")}</span><span>${esc(spec.date || "")}</span></div>
</body></html>`;
}

const { chromium } = await import(pathToFileURL(PW).href).catch(() =>
  die(`Playwright missing at ${PW}; run the browse skill's Setup step`)
);

const total = spec.options.length;
const parts = Math.ceil(total / MAX_COLS);
const per = Math.ceil(total / parts);
const chunks = [];
for (let i = 0; i < total; i += per) chunks.push(spec.options.slice(i, i + per));
const slug =
  (spec.slug || spec.ref || spec.question).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) ||
  basename(specPath, ".json");

const browser = await chromium.launch();
try {
  const pg = await (await browser.newContext({ deviceScaleFactor: 2, viewport: { width: 1400, height: 900 } })).newPage();
  // Natural width of each shot in CSS px, from the PNG header (screenshots are usually DSF 2).
  const natW = {};
  for (const o of spec.options) {
    const buf = readFileSync(o.image);
    if (buf.toString("ascii", 1, 4) !== "PNG") die(`option "${o.name}": image must be a PNG`);
    natW[o.image] = buf.readUInt32BE(16) / (o.dsf || 2);
  }
  for (let i = 0; i < chunks.length; i++) {
    const htmlPath = join(outDir, `${slug}-${i + 1}.html`);
    writeFileSync(htmlPath, page(chunks[i], natW, i + 1, chunks.length));
    await pg.goto(pathToFileURL(htmlPath).href);
    await pg.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map((im) => im.decode().catch(() => {}))); });
    const png = join(outDir, `${slug}-${i + 1}.png`);
    await pg.locator("body").screenshot({ path: png });
    console.log(png);
  }
} finally {
  await browser.close();
}
