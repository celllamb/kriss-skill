#!/usr/bin/env python3
"""Idempotent, fingerprinted migration of bundled legacy adaptive runtimes.

Only our versioned runtime ID and the exact bundled legacy bodies are removed.
Unrecognized competing runtime assignments fail rather than execute concurrently.
Unrelated author scripts (navigation, charts, notes) are preserved byte for byte.
"""
from __future__ import annotations
import argparse
import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY_BODIES = {'9451e5aec0052c8725a1d361df0b88dbcabe1352cab7814539a9c83e0491e3a4': 'reference.html', '75c42686b14935cde1a7e6ba28242c6b3cda0673a07a266f12f30faedbc85b2e': 'approved-visual-variants.html'}
SCRIPT_RE = re.compile(r'<script\b[^>]*>[\s\S]*?</script>', re.I)



def document_body_end(text: str) -> int | None:
    """Find a document end tag, excluding markup in scripts, comments and attributes."""
    line_starts = [0] + [m.end() for m in re.finditer(r'\n', text)]

    class BodyEndParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.raw = None
            self.offsets = []

        def handle_starttag(self, tag, attrs):
            if self.raw is None and tag in ('script', 'style', 'textarea', 'title'):
                self.raw = tag

        def handle_endtag(self, tag):
            if self.raw:
                if tag == self.raw:
                    self.raw = None
                return
            if tag == 'body':
                line, column = self.getpos()
                self.offsets.append(line_starts[line-1] + column)

    parser = BodyEndParser()
    parser.feed(text)
    parser.close()
    return parser.offsets[-1] if parser.offsets else None

def prepare_html(text: str) -> str:
    def replace(match):
        script = match.group(0)
        tag = script[:script.index('>')+1]
        body = re.sub(r'^<script\b[^>]*>|</script>$', '', script, flags=re.I).strip().replace('\r\n', '\n')
        digest = hashlib.sha256(body.encode('utf-8')).hexdigest()
        owned = re.search(r'\bid\s*=\s*[\'"]kriss-adaptive-runtime[\'"]', tag, re.I)
        if owned or digest in LEGACY_BODIES:
            return ''
        if re.search(r'(?:(?:window|globalThis)\.)?(?:applyAdaptiveLayout|applyAdaptiveTypography)\s*=', body):
            raise ValueError('unrecognized-adaptive-runtime: migrate the competing script explicitly; user scripts are not silently deleted')
        return script
    text = SCRIPT_RE.sub(replace, text)
    text = re.sub(r'<style\b[^>]*\bid=[\"\']kriss-final-render-state[\"\'][^>]*>[\s\S]*?</style>', '', text, flags=re.I)
    runtime = (HERE / 'adaptive-runtime.js').read_text(encoding='utf-8')
    block = '<script id="kriss-adaptive-runtime" data-version="kriss-ppt-v1.1">\n' + runtime + '\n</script>'
    # An author script (e.g. popup speaker notes) may contain the literal
    # "</body>". Insert only at a real document end tag, never inside a script,
    # style, or comment. Keep all unrelated bytes intact and remain idempotent.
    offset = document_body_end(text)
    if offset is not None:
        return text[:offset].rstrip() + '\n' + block + '\n' + text[offset:]
    return text.rstrip() + '\n' + block + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input', type=Path)
    ap.add_argument('output', nargs='?', type=Path)
    args = ap.parse_args()
    output = args.output or args.input.with_name(args.input.stem + '.prepared.html')
    output.write_text(prepare_html(args.input.read_text(encoding='utf-8')), encoding='utf-8')
    print(output)


if __name__ == '__main__':
    main()
