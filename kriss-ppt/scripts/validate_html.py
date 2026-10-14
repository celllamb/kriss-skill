#!/usr/bin/env python3
"""Shared static preflight used by authoring, export and release (no CLI on import)."""
from __future__ import annotations
import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path


class Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.slides: list[dict] = []
        self.ids: set[str] = set()
        self.errors: list[dict] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            if a['id'] in self.ids:
                self.errors.append({'code': 'duplicate-id', 'id': a['id']})
            self.ids.add(a['id'])
        if 'slide' in (a.get('class') or '').split():
            self.slides.append(a)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def validate_text(text: str) -> dict:
    parser = Check()
    parser.feed(text)
    parser.close()
    if not parser.slides:
        parser.errors.append({'code': 'no-slides'})
    for i, slide in enumerate(parser.slides, 1):
        if not (slide.get('data-notes') or '').strip():
            parser.errors.append({'code': 'missing-speaker-notes', 'slide': i})
    return {'pass': not parser.errors, 'slides': len(parser.slides),
            'errors': parser.errors, 'warnings': []}


def validate_file(path: Path) -> dict:
    return validate_text(path.read_text(encoding='utf-8'))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('html', type=Path)
    args = ap.parse_args()
    try:
        result = validate_file(args.html)
    except (OSError, UnicodeError, ValueError) as error:
        result = {'pass': False, 'errors': [{'code': 'unreadable-input', 'detail': str(error)}]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
