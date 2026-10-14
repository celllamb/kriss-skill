"""Resolve independently captured source roles to actual native shape IDs."""
from __future__ import annotations


def check_coverage(source: dict, objects: list[dict], text: dict) -> dict:
    errors = list(source.get('errors', []))
    rows = []
    for node in source['nodes']:
        role, identity = node['role'], node['id']
        candidates = []
        if role == 'static-background':
            candidates = [o for o in objects if o['kind'] == 'background']
        elif role == 'text':
            owners = set(node['ancestors'])
            candidates = [o for o in objects if o['id'] in owners and o['kind'] in ('text', 'shape-text')]
        elif role == 'hyperlink':
            # One anchor may span several native text blocks (e.g. block children).
            # Every contributing run must retain the independently captured URL.
            linked = [(b['id'], r) for b in text.get('blocks', [])
                      for p in b.get('paragraphs', []) for r in p.get('runs', [])
                      if r.get('hyperlinkSourceId') == identity and not r.get('break')]
            owners = {owner for owner, _ in linked}
            candidates = [o for o in objects if o['id'] in owners
                          and o['kind'] in ('text', 'shape-text')]
            if not linked or any(r.get('hyperlink') != node.get('href') for _, r in linked):
                errors.append({'code': 'source-hyperlink-mismatch', 'id': identity})
            # Compare the entire independently browser-rendered anchor text, not
            # only existence of one linked run. Soft/hard whitespace is not a
            # separate click target; every non-whitespace character must survive.
            if 'text' in node:
                expected_text = ''.join(node['text'].split())
                actual_text = ''.join(''.join(r.get('text', '') for _, r in linked).split())
                if actual_text != expected_text:
                    errors.append({'code': 'source-hyperlink-text-mismatch', 'id': identity})
        elif role == 'generated':
            # A literal in normal inline flow belongs to its coherent textbox,
            # just like an ordinary differently styled span. Positioned/painted
            # pseudo content still needs its own independent native owner.
            owners = {b['id'] for b in text.get('blocks', [])
                      if identity in b.get('sourceGeneratedIds', [])}
            candidates = [o for o in objects if
                          (o['id'] == identity and o['kind'] in ('text','shape-text','shape')) or
                          (o['id'] in owners and o['kind'] in ('text','shape-text'))]
        else:
            kinds = {
                'paint': ('shape', 'shape-text'), 'image': ('image',),
                'background-image': ('image',), 'svg-primitive': ('svg-shape', 'connector','svg-stroke'),
                'generated': ('text', 'shape-text', 'shape'), 'list-marker': ('text',),
            }.get(role, ())
            candidates = [o for o in objects if o['id'] == identity and o['kind'] in kinds]
        # One role -> one owner. Different direct text nodes may share a textbox.
        valid = (bool(candidates) and len(candidates) == len(owners)) if role == 'hyperlink' else len(candidates) == 1
        if not valid:
            errors.append({'code': 'source-native-coverage', 'id': identity,
                           'role': role, 'count': len(candidates)})
        rows.append({'id': identity, 'role': role, 'shape_ids': [o['shape_id'] for o in candidates], 'pass': valid})
    return {'pass': not errors, 'source_role_count': len(rows), 'rows': rows, 'errors': errors}
