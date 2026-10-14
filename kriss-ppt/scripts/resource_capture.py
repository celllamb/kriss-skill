"""Bind each native image to the bytes used by the browser; never re-download it."""
from __future__ import annotations
import base64
import hashlib
from pathlib import Path
from urllib.parse import unquote, urlparse


def read_source_bytes(src: str, responses: dict[str, bytes]) -> bytes:
    if src in responses:
        return responses[src]
    if src.startswith('data:'):
        header, body = src.split(',', 1)
        return base64.b64decode(body) if ';base64' in header else unquote(body).encode('utf-8')
    if src.startswith('file:'):
        return Path(unquote(urlparse(src).path)).read_bytes()
    raise ValueError('No browser-captured image response: ' + src[:200])


def freeze_images(visual: dict, responses: dict[str, bytes], work: Path) -> tuple[dict, list[dict]]:
    assets, errors = {}, []
    for element in visual['elements']:
        sources = ([element['backgroundUrl']] if element.get('backgroundUrl') else [])
        if element.get('tag') == 'img' and element.get('src'):
            sources.append(element['src'])
        for src in sources:
            if src in assets:
                continue
            try:
                data = read_source_bytes(src, responses)
                digest = hashlib.sha256(data).hexdigest()
                target = work / 'assets' / (digest + '.bin')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                assets[src] = {'path': str(target.relative_to(work)), 'sha256': digest,
                               'bytes': len(data)}
            except (OSError, ValueError) as error:
                errors.append({'code': 'image-bytes-unavailable', 'id': element['id'], 'detail': str(error)})
    return assets, errors


BACKGROUND_CHECK_JS = r'''async index=>{
  const slide=document.querySelectorAll('.slide')[index],failures=[];
  for(const e of [slide,...slide.querySelectorAll('*')]){
    const c=getComputedStyle(e),r=e.getBoundingClientRect();
    if(c.display==='none'||c.visibility==='hidden'||!r.width||!r.height)continue;
    const match=c.backgroundImage.match(/^url\(["']?(.*?)["']?\)$/);
    if(!match)continue;
    const image=new Image();image.src=match[1];
    try{await image.decode();if(!image.naturalWidth)throw Error('empty size');}
    catch(error){failures.push({code:'background-image-decode-failed',src:match[1],detail:String(error)});}
  }
  return failures;
}'''
