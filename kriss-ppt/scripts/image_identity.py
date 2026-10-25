"""Validate embedded image bytes and presentation geometry against captured HTML.

This is correspondence, not visual similarity or authenticity certification.
No source URL, pixel content, slide number, or subject-specific exceptions.
"""
from __future__ import annotations
import hashlib
from collections import Counter
from pptx.oxml.ns import qn

EMU = 914400


def check_native_images(slide, model: dict, sx: float, sy: float) -> dict:
    errors, checked = [], 0
    expected = []
    for element in model.get('visual', {}).get('elements', []):
        if 'slide' in element.get('classes', []):
            continue  # The full template background has its own artwork contract.
        sources = ([element['backgroundUrl']] if element.get('backgroundUrl') else [])
        if element.get('tag') == 'img' and element.get('src'):
            sources.append(element['src'])
        for src in sources:
            expected.append((element, src))
    inherited={o['id']:o for o in model.get('native_objects',[]) if o['kind']=='master-image'}
    expected_names = Counter('kriss:image:' + e['id'] for e, _ in expected)
    # One owner with two image layers needs explicit layer IDs. Do not silently
    # guess the relation from z-order or treat one image as coverage for both.
    for name, count in expected_names.items():
        if count != 1:
            errors.append({'id': name, 'error': 'ambiguous captured image layers', 'count': count})
    for element, src in expected:
        identity = element['id']
        if identity in inherited:
            record=inherited[identity]
            asset=model.get('assets',{}).get(src)
            if not asset or record.get('image_sha256')!=asset.get('sha256'):
                errors.append({'id':identity,'error':'inherited layout picture digest mismatch'})
            checked+=1
            continue
        name = 'kriss:image:' + identity
        hits = [s for s in slide.shapes if s.name == name]
        if len(hits) != 1:
            errors.append({'id': identity, 'error': 'image must map to one native picture', 'count': len(hits)})
            continue
        shape = hits[0]
        if shape._element.tag != qn('p:pic'):
            errors.append({'id': identity, 'error': 'mapped image is not a picture'})
            continue
        asset = model.get('assets', {}).get(src)
        if not asset or not asset.get('sha256') or not isinstance(asset.get('bytes'), int):
            errors.append({'id': identity, 'error': 'missing captured image identity'})
            continue
        try:
            blip = shape._element.find('.//' + qn('a:blip'))
            if blip is None or not blip.get(qn('r:embed')) or blip.get(qn('r:link')):
                raise ValueError('Image must be embedded, not externally linked')
            data = shape.image.blob
            if len(data) != asset['bytes'] or hashlib.sha256(data).hexdigest() != asset['sha256']:
                errors.append({'id': identity, 'error': 'embedded image bytes mismatch'})
            # Effects could alter scientific figures without changing media bytes.
            if len(blip):
                errors.append({'id': identity, 'error': 'unexpected native image color/alpha effects'})
            if any(abs(float(v)) > 1e-9 for v in (shape.crop_left, shape.crop_top, shape.crop_right, shape.crop_bottom)):
                errors.append({'id': identity, 'error': 'unexpected native image crop'})
            xfrm = shape._element.spPr.find(qn('a:xfrm'))
            if xfrm is not None and (int(xfrm.get('rot', '0')) % 21600000 or any(xfrm.get(k) in ('1', 'true', 'on') for k in ('flipH','flipV'))):
                errors.append({'id': identity, 'error': 'unexpected native image rotation/flip'})
            rect = element['rect']
            actual = [shape.left/EMU/sx, shape.top/EMU/sy, shape.width/EMU/sx, shape.height/EMU/sy]
            wanted = [rect[k] for k in ('x','y','w','h')]
            if max(abs(a-b) for a,b in zip(actual,wanted)) > .10:
                errors.append({'id': identity, 'error': 'native image rectangle mismatch',
                               'delta_px': [round(a-b, 6) for a,b in zip(actual,wanted)]})
            geom = shape._element.spPr.find(qn('a:prstGeom'))
            if geom is None or geom.get('prst') != 'rect':
                errors.append({'id': identity, 'error': 'unexpected native image clipping shape'})
            fill = shape._element.find(qn('p:blipFill'))
            if fill is None or fill.find(qn('a:tile')) is not None or fill.find(qn('a:stretch')) is None:
                errors.append({'id': identity, 'error': 'unexpected native image fill mode'})
            elif any(int(v) for v in (fill.find('.//'+qn('a:fillRect')).attrib.values() if fill.find('.//'+qn('a:fillRect')) is not None else [])):
                errors.append({'id': identity, 'error': 'unexpected native image fill rectangle'})
            checked += 1
        except (AttributeError, KeyError, ValueError, TypeError, OSError) as error:
            errors.append({'id': identity, 'error': 'unreadable native image', 'detail': type(error).__name__})
    mapped = set(expected_names)
    for shape in slide.shapes:
        if shape._element.tag == qn('p:pic') and shape.name != 'kriss:background' and shape.name not in mapped:
            errors.append({'shape_id': shape.shape_id, 'error': 'unmapped native picture'})
    return {'pass': not errors, 'expected_images': len(expected), 'checked_images': checked, 'errors': errors}
