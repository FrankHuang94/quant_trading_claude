#!/usr/bin/env node
// Validate every ```mermaid block in the given markdown files (or all of docs/) with the real
// Mermaid parser running in headless Chromium.
//
// Usage: node scripts/check_mermaid.mjs [file.md ...]
// Needs: the `playwright` package and mermaid's browser bundle. Set MERMAID_JS to the path of
// mermaid.min.js, or install it with `npm install --no-save mermaid@11.4.1` in the repo root.
import { createRequire } from "module";
import fs from "fs";
import path from "path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const candidates = [
  process.env.MERMAID_JS,
  path.join(repo, "node_modules/mermaid/dist/mermaid.min.js"),
  "/home/user/tools/node_modules/mermaid/dist/mermaid.min.js",
].filter(Boolean);
const mermaidJs = candidates.find((p) => fs.existsSync(p));
if (!mermaidJs) {
  console.error("mermaid.min.js not found; set MERMAID_JS or npm install --no-save mermaid@11.4.1");
  process.exit(2);
}

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) =>
    d.isDirectory() ? walk(path.join(dir, d.name)) : d.name.endsWith(".md") ? [path.join(dir, d.name)] : []);
}

function blocks(file) {
  const lines = fs.readFileSync(file, "utf8").split("\n");
  const out = [];
  let inside = false, fence = "", buf = [], start = 0;
  lines.forEach((line, i) => {
    const s = line.trim();
    if (!inside) {
      const m = s.match(/^(`{3,}|~{3,})\s*mermaid\s*$/);
      if (m) { inside = true; fence = m[1]; buf = []; start = i + 1; }
    } else if (s.startsWith(fence) && /^[`~]+$/.test(s)) {
      const ind = Math.min(...buf.filter((l) => l.trim()).map((l) => l.match(/^ */)[0].length), 99);
      out.push({ file, line: start, code: buf.map((l) => l.slice(ind)).join("\n") });
      inside = false;
    } else {
      buf.push(line);
    }
  });
  return out;
}

const files = process.argv.length > 2 ? process.argv.slice(2) : walk(path.join(repo, "docs"));
const all = files.flatMap(blocks);
const browser = await chromium.launch();
const page = await browser.newPage();
await page.setContent("<html><body></body></html>");
await page.addScriptTag({ path: mermaidJs });
await page.evaluate(() => window.mermaid.initialize({ startOnLoad: false }));
let bad = 0;
for (const b of all) {
  const err = await page.evaluate(async (code) => {
    try { await window.mermaid.parse(code); return null; } catch (e) { return String(e.message || e).split("\n").slice(0, 4).join(" | "); }
  }, b.code);
  if (err) {
    bad++;
    console.log(`FAIL ${path.relative(repo, b.file)}:${b.line}  ${err}`);
  }
}
await browser.close();
console.log(`\ncheck_mermaid: ${all.length} diagrams, ${bad} failing`);
process.exit(bad ? 1 : 0);
