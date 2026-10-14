#!/usr/bin/env python3
"""Materialize the byte-identical canonical HTML reference from its Git transport."""
from pathlib import Path
import gzip, hashlib, json, sys
ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'PACKAGE-MANIFEST.json'

def restore():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    target = ROOT / 'references/reference.html'
    archived = ROOT / 'references/reference.html.gz'
    expected = manifest['generated_files']['references/reference.html']
    raw = gzip.decompress(archived.read_bytes())
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected:
        raise ValueError(f'restored reference digest differs from release manifest: {digest}')
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError('existing reference.html differs from official reference; refusing overwrite')
    else:
        target.write_bytes(raw)
    return {'path':str(target), 'sha256':digest, 'bytes':len(raw)}

if __name__ == '__main__':
    import json
    try:
        print(json.dumps(restore(),ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,gzip.BadGzipFile) as error:
        print(f'ERROR: {error}',file=sys.stderr);sys.exit(1)
