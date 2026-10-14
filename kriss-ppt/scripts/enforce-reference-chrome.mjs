#!/usr/bin/env node
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const [inputArg, referenceArg] = process.argv.slice(2);
if (!inputArg) {
  console.error('Usage: node scripts/enforce-reference-chrome.mjs <presentation.html> [reference.html]');
  process.exit(2);
}
const here = path.dirname(fileURLToPath(import.meta.url));
const input = path.resolve(inputArg);
const reference = path.resolve(referenceArg || path.join(here, '..', 'references', 'reference.html'));
if (!fs.existsSync(input)) throw new Error(`Input not found: ${input}`);
if (!fs.existsSync(reference)) throw new Error(`Reference not found: ${reference}`);

execFileSync(process.env.PYTHON || 'python3',[path.join(here,'sync_reference_chrome.py'),input,'--reference',reference,'--in-place'],{stdio:'inherit'});
let html = fs.readFileSync(input, 'utf8');
const ref = fs.readFileSync(reference, 'utf8');
const roles = ['cover-logo', 'cover-wordmark', 'cover-anniv'];

function extractImg(role) {
  const re = new RegExp(`<img\\b[^>]*class=["'][^"']*\\b${role}\\b[^>]*>`, 'i');
  const m = ref.match(re);
  if (!m) throw new Error(`Reference is missing .${role}`);
  return m[0].replace(/\sdata-template-fixed=(['"]).*?\1/gi, '')
             .replace(/\sdata-template-role=(['"]).*?\1/gi, '')
             .replace(/<img\b/i, `<img data-template-fixed="true" data-template-role="${role}"`);
}
function extractCss(role) {
  const re = new RegExp(`\\.${role}\\s*\\{[^}]*\\}`, 'i');
  const m = ref.match(re);
  if (!m) throw new Error(`Reference CSS is missing .${role}`);
  return m[0];
}
const imgTags = Object.fromEntries(roles.map(r => [r, extractImg(r)]));
const cssRules = roles.map(extractCss);

// Ensure the fixed cover chrome CSS exists in the generated deck.
const missingCss = cssRules.filter((rule, i) => !new RegExp(`\\.${roles[i]}\\s*\\{`, 'i').test(html));
if (missingCss.length) {
  const css = `\n/* KRISS fixed cover chrome copied from references/reference.html */\n${missingCss.join('\n')}\n`;
  if (/<\/style>/i.test(html)) html = html.replace(/<\/style>/i, `${css}</style>`);
  else if (/<\/head>/i.test(html)) html = html.replace(/<\/head>/i, `<style>${css}</style></head>`);
  else html = `<style>${css}</style>` + html;
}

// Preserve every cover's immutable foreground assets. Only .cover-copy is content-editable.
const sectionRe = /<section\b([^>]*)class=(["'])([^"']*\bcover\b[^"']*)\2([^>]*)>([\s\S]*?)<\/section>/gi;
let covers = 0;
html = html.replace(sectionRe, (full, a, q, cls, b, body) => {
  covers++;
  let next = body;
  const additions = [];
  for (const role of roles) {
    if (!new RegExp(`<img\\b[^>]*class=["'][^"']*\\b${role}\\b`, 'i').test(next)) additions.push(imgTags[role]);
  }
  if (additions.length) {
    const block = `\n<!-- KRISS immutable cover chrome: sourced verbatim from reference.html -->\n${additions.join('\n')}\n`;
    if (/<div\b[^>]*class=["'][^"']*\bpattern-tag\b/i.test(next)) {
      next = next.replace(/(<div\b[^>]*class=["'][^"']*\bpattern-tag\b)/i, block + '$1');
    } else next += block;
  }
  // Mark pre-existing reference assets as immutable too.
  for (const role of roles) {
    const re = new RegExp(`<img\\b([^>]*class=["'][^"']*\\b${role}\\b[^"']*["'][^>]*)>`, 'i');
    next = next.replace(re, (m, attrs) => {
      if (/data-template-fixed=/i.test(m)) return m;
      return `<img data-template-fixed="true" data-template-role="${role}"${attrs}>`;
    });
  }
  next = next.replace(/<div\b([^>]*)class=(["'])([^"']*\bcover-copy\b[^"']*)\2([^>]*)>/i,
    (m, x, qq, cc, y) => /data-template-slot=/i.test(m) ? m : `<div${x}class=${qq}${cc}${qq}${y} data-template-slot="cover-copy">`);
  return `<section${a}class=${q}${cls}${q}${b}>${next}</section>`;
});

if (!covers) console.warn('No .cover slide found; no cover chrome inserted.');
fs.writeFileSync(input, html);
console.log(`Reference chrome enforced on ${covers} cover slide(s): ${input}`);
