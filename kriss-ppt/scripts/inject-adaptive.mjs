#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const args=process.argv.slice(2);
if (!args.length) { console.error('Usage: inject-adaptive.mjs input.html [output.html]'); process.exit(2); }
const script=fileURLToPath(new URL('./runtime_prepare.py',import.meta.url));
const r=spawnSync(process.env.PYTHON||process.env.PYTHON3||'python3',[script,...args],{stdio:'inherit'});
if (r.error) console.error(r.error.message);
process.exit(r.status??1);
