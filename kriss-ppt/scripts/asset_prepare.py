"""Embed local image/CSS/script resources without rasterization or font bundling.

The input is never modified. Final HTML and the browser/native exporters consume
identical image bytes. Local fonts must be installed; this tool never packages fonts.
"""
from __future__ import annotations
import base64
import hashlib
import html as html_lib
import mimetypes
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

ATTR = re.compile(r'''(?P<key>[\w:-]+)\s*=\s*(?P<quote>["'])(?P<value>.*?)(?P=quote)''', re.S)
FONT_EXTENSIONS = {'.woff', '.woff2', '.ttf', '.otf', '.ttc', '.eot'}


def prepare_assets(text: str, root: Path) -> tuple[str, list[dict]]:
    root=root.resolve();records=[];seen_css=set()

    def path_for(value: str, base: Path) -> Path | None:
        value=html_lib.unescape(value.strip())
        if not value or value.startswith(('#','data:','http://','https://','//','blob:')):
            return None
        parsed=urlparse(value)
        if parsed.scheme not in ('','file'):
            raise ValueError('Unsupported asset scheme: '+parsed.scheme)
        path=(Path(unquote(parsed.path)) if parsed.scheme=='file' else base/unquote(parsed.path)).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Local asset escapes the document directory: '+value)
        if path.suffix.lower() in FONT_EXTENSIONS:
            raise ValueError('Install fonts locally; font files are never embedded in generated HTML: '+value)
        if not path.is_file():raise ValueError('Missing local asset: '+value)
        return path

    def read(path: Path, kind: str) -> bytes:
        data=path.read_bytes()
        records.append({'source':str(path.relative_to(root)),'kind':kind,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
        return data

    def data_url(value: str, base: Path) -> str:
        path=path_for(value,base)
        if path is None:return value
        mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        if not mime.startswith('image/'):
            raise ValueError('CSS/img assets must be images; install fonts rather than embedding them: '+value)
        return 'data:'+mime+';base64,'+base64.b64encode(read(path,'image')).decode('ascii')

    def css(source: str, base: Path) -> str:
        def replace_import(match):
            value=match.group('url')
            path=path_for(value,base)
            if path is None:return match.group(0)
            if path in seen_css:raise ValueError('Cyclic CSS import: '+str(path))
            if match.group('media').strip():raise ValueError('Local CSS imports with media qualifiers require explicit authoring: '+value)
            seen_css.add(path)
            result=css(read(path,'stylesheet').decode('utf-8'),path.parent)
            seen_css.remove(path)
            return result
        source=re.sub(r'''@import\s+(?:url\(\s*)?["'](?P<url>[^"']+)["']\s*\)?(?P<media>[^;]*);''',replace_import,source,flags=re.I)
        def replace_url(match):
            value=match.group(2).strip()
            result=data_url(value,base)
            return 'url("'+result+'")' if result!=value else match.group(0)
        return re.sub(r'''url\(\s*(["']?)(.*?)\1\s*\)''',replace_url,source,flags=re.S|re.I)

    def attributes(tag: str) -> dict[str,str]:
        return {m['key'].lower():html_lib.unescape(m['value']) for m in ATTR.finditer(tag)}

    def rewrite_tag(match):
        tag=match.group(0);name=re.match(r'<\s*([\w:-]+)',tag)[1].lower();attrs=attributes(tag)
        if name=='link' and attrs.get('rel','').lower()=='stylesheet' and attrs.get('href'):
            path=path_for(attrs['href'],root)
            if path is not None:
                extra=' media="'+html_lib.escape(attrs['media'],quote=True)+'"' if attrs.get('media') else ''
                body=css(read(path,'stylesheet').decode('utf-8'),path.parent)
                return '<style'+extra+' data-kriss-local-stylesheet="'+html_lib.escape(attrs['href'],quote=True)+'">'+body.replace('</style','<\\/style')+'</style>'
        if name=='img' and attrs.get('srcset'):
            # Srcset parsing is not equivalent to splitting on commas (data URLs).
            raise ValueError('Responsive image srcset must be resolved to one explicit src before release')
        def replace_attr(m):
            key=m['key'].lower();value=m['value'];new=value
            if key=='style':new=css(html_lib.unescape(value),root)
            elif name=='img' and key=='src':new=data_url(html_lib.unescape(value),root)
            if new==value:return m.group(0)
            return m['key']+'='+m['quote']+html_lib.escape(new,quote=True)+m['quote']
        return ATTR.sub(replace_attr,tag)

    # Keep script bodies out of all tag/CSS rewrites. In particular '<img ...>' in
    # a JavaScript string is not a DOM resource to edit behind the author's back.
    chunks=re.split(r'(<script\b[^>]*>[\s\S]*?</script>)',text,flags=re.I)
    for i,chunk in enumerate(chunks):
        if i%2:
            opening=chunk[:chunk.index('>')+1];attrs=attributes(opening)
            if attrs.get('src'):
                path=path_for(attrs['src'],root)
                if path is not None:
                    if attrs.get('type')=='module':raise ValueError('Bundle module imports explicitly before release')
                    body=read(path,'script').decode('utf-8').replace('</script','<\\/script')
                    opening=ATTR.sub(lambda m:'' if m['key'].lower()=='src' else m.group(0),opening)
                    chunks[i]=opening+body+'</script>'
            continue
        chunk=re.sub(r'<style\b[^>]*>([\s\S]*?)</style>',lambda m:m.group(0)[:m.group(0).index('>')+1]+css(m.group(1),root)+'</style>',chunk,flags=re.I)
        chunks[i]=re.sub(r'<[A-Za-z][^>]*>',rewrite_tag,chunk)
    return ''.join(chunks),records
