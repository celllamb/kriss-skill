#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const [inputArg, outputArg] = process.argv.slice(2);
if (!inputArg) {
  console.error('Usage: node scripts/export-pptx.mjs <presentation.html> [presentation.pptx]');
  process.exit(2);
}
const here = path.dirname(fileURLToPath(import.meta.url));
const py = process.env.PYTHON || process.env.PYTHON3 || 'python3';
const script = path.join(here, 'export-pptx.py');
const args = [script, inputArg];
if (outputArg) args.push(outputArg);
const r = spawnSync(py, args, { stdio: 'inherit' });
if (r.error) {
  console.error(r.error.message);
  process.exit(2);
}
process.exit(r.status ?? 1);
