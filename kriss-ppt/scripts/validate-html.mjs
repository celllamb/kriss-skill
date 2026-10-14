#!/usr/bin/env node
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const script=fileURLToPath(new URL('./validate_html.py',import.meta.url));
const r=spawnSync(process.env.PYTHON||process.env.PYTHON3||'python3',[script,...process.argv.slice(2)],{stdio:'inherit'});
if(r.error)console.error(r.error.message);
process.exit(r.status??1);
