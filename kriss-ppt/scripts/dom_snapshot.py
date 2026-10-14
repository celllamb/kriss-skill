"""Read Chromium paint-layer order and resolved pseudo text without DOM mutation.

DOMSnapshot paintOrders identify co-painted layers, not unique draw commands.
Within a layer we retain the browser snapshot tree order. Native QA binds that
order independently to native owners; local render parity remains mandatory.
"""
from __future__ import annotations
from collections import defaultdict


def capture_dom_paint(page, index: int) -> dict:
    session = page.context.new_cdp_session(page)
    try:
        snap = session.send('DOMSnapshot.captureSnapshot', {
            'computedStyles': [], 'includePaintOrder': True, 'includeDOMRects': True})
    finally:
        session.detach()
    strings = snap['strings']
    doc = snap['documents'][0]
    nodes, layout = doc['nodes'], doc['layout']
    parents = nodes['parentIndex']
    def string(v): return strings[v] if v >= 0 else ''
    def attrs(i):
        values = nodes['attributes'][i]
        return {string(values[k]): string(values[k+1]) for k in range(0, len(values), 2)}
    slides = [i for i, kind in enumerate(nodes['nodeType'])
              if kind == 1 and 'slide' in attrs(i).get('class', '').split()]
    target = slides[index]
    pseudo = {i: string(v) for i, v in zip(nodes.get('pseudoType', {}).get('index', []),
                                         nodes.get('pseudoType', {}).get('value', []))}
    descendants, in_pseudo, identity = {}, {}, {}
    for i, parent in enumerate(parents):
        descendants[i] = i == target or descendants.get(parent, False)
        in_pseudo[i] = i in pseudo or in_pseudo.get(parent, False)
        if descendants[i] and nodes['nodeType'][i] == 1 and not in_pseudo[i]:
            identity[i] = f's{index+1:02d}.e{len(identity):04d}'
    entries = defaultdict(list)
    for j, node in enumerate(layout['nodeIndex']): entries[node].append(j)
    if 'paintOrders' not in layout:
        raise RuntimeError('Chromium did not return independently measured paint order')
    order, generated, errors, resolved_text = {}, {}, [], {}
    def paint(node):
        current = node
        while current >= 0:
            if entries[current]: return layout['paintOrders'][entries[current][0]]
            current = parents[current]
        return None
    for node, uid in identity.items():
        value = paint(node)
        if value is not None:
            order[uid] = {'layer': value, 'sequence': node, 'measurement': 'Chromium DOMSnapshot'}
    for node, kind in pseudo.items():
        owner = identity.get(parents[node])
        if owner is None: continue
        uid = owner + '.' + kind
        value = paint(node)
        if value is not None:
            order[uid] = {'layer': value, 'sequence': node, 'measurement': 'Chromium DOMSnapshot'}
        # Generated text can be attached directly to a pseudo node or a text
        # child of it. Read rendered layout text, never the CSS counter syntax.
        candidates = []
        for j, descendant in enumerate(layout['nodeIndex']):
            current = descendant
            while current >= 0 and current != node: current = parents[current]
            if current == node and string(layout['text'][j]):
                candidates.append((j, string(layout['text'][j]), layout['bounds'][j]))
        if candidates:
            generated[uid] = {'text': ''.join(x[1] for x in candidates),
                              'fragments': [{'text': t, 'bounds': r} for _, t, r in candidates],
                              'measurement': 'Chromium DOMSnapshot resolved generated text'}
    # Browser-resolved textTransform honors language rules (e.g. Turkish i).
    # Direct text-node ordinals exclude pseudo nodes and require no DOM mutation.
    ordinals = defaultdict(int)
    for node, parent in enumerate(parents):
        if nodes['nodeType'][node] != 3 or parent not in identity: continue
        key = identity[parent] + '.t' + str(ordinals[parent]); ordinals[parent] += 1
        fragments = [string(layout['text'][j]) for j in entries[node]]
        if fragments:
            resolved_text[key] = {'raw': string(nodes['nodeValue'][node]),
                                  'rendered': ''.join(fragments)}
    result = {'schema': 'kriss-dom-paint-v1', 'order': order,
              'generated': generated, 'resolved_text': resolved_text, 'errors': errors}
    page.evaluate('(a)=>{window.__KRISS_DOM_PAINT??={};window.__KRISS_DOM_PAINT[a.index]=a.result;}',
                  {'index': index, 'result': result})
    return result


def bind_paint_order(text: dict, visual: dict, snapshot: dict) -> None:
    """Bind already captured order to exporters; never infer it from PPTX order."""
    for item in text['blocks'] + visual['elements'] + visual['svgLines'] + visual.get('svgShapes', []):
        value = snapshot['order'].get(item['id'])
        if value is None:
            text['warnings'].append({'code': 'unmeasured-browser-paint-order', 'id': item['id']})
        else:
            item['domPaintOrder'] = value
