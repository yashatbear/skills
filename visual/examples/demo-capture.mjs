// Worked example: capture one screenshot per option of a real page at 390px.
// Options are CSS edits on the same render, so every card shows the same region.
// Usage: node demo-capture.mjs <out-dir>
// Playwright comes from the browse skill (or set VISUAL_PLAYWRIGHT to its index.mjs).
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const HERE = dirname(fileURLToPath(import.meta.url));
const PW = process.env.VISUAL_PLAYWRIGHT || resolve(HERE, "../../browse/node_modules/playwright/index.mjs");
const { chromium } = await import(pathToFileURL(PW).href);
const OUT = resolve(process.argv[2] || ".");

const OPTIONS = {
  today: "",
  fit: `.chips{gap:4px!important}.chip{padding:5px 8px!important;font-size:12px!important}`,
  fade: `.chips{-webkit-mask-image:linear-gradient(90deg,#000 0,#000 calc(100% - 44px),transparent);mask-image:linear-gradient(90deg,#000 0,#000 calc(100% - 44px),transparent)}`,
};

const b = await chromium.launch();
const pg = await b.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
await pg.goto(pathToFileURL(resolve(HERE, "demo-page.html")).href);
for (const [k, css] of Object.entries(OPTIONS)) {
  await pg.evaluate((css) => {
    let s = document.getElementById("opt");
    if (!s) { s = document.createElement("style"); s.id = "opt"; document.head.append(s); }
    s.textContent = css;
  }, css);
  await pg.waitForTimeout(100);
  // Measure, don't guess: log what decides the call.
  const m = await pg.evaluate(() => {
    const row = document.querySelector(".chips"); const r = row.getBoundingClientRect().right;
    return { clientWidth: row.clientWidth, scrollWidth: row.scrollWidth,
      hidden: [...row.querySelectorAll(".chip")].filter((c) => c.getBoundingClientRect().right > r + 0.5).map((c) => c.textContent) };
  });
  console.log(k, JSON.stringify(m));
  await pg.screenshot({ path: `${OUT}/demo-${k}.png`, clip: { x: 0, y: 0, width: 390, height: 260 } });
}
await b.close();
