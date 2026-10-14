#!/usr/bin/env python3
"""Opt-in authoring migration: restore original standard artwork from reference.html.

Not run during export. Only known legacy chrome selectors/elements are removed;
unknown content is preserved and the release checker must verify the result.
"""
from __future__ import annotations
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re

class Tag(HTMLParser):
    def __init__(self,text):super().__init__();self.attrs={};self.feed(text)
    def handle_starttag(self,tag,attrs):self.attrs=dict(attrs)

def set_attr(tag,name,value):
    escaped=value.replace('&','&amp;').replace('"','&quot;')
    pat=rf'\s{re.escape(name)}\s*=\s*(?:"[^"]*"|\x27[^\x27]*\x27)'
    tag=re.sub(pat,'',tag,flags=re.I)
    return tag[:-1]+f' {name}="{escaped}">'

def migrate(html:str,reference:str)->tuple[str,dict]:
    standard=None
    for tag in re.findall(r'<section\b[^>]*>',reference,re.I):
        a=Tag(tag).attrs
        if 'std' in a.get('class','').split():standard=a;break
    if not standard:raise ValueError('Reference does not contain .slide.std')
    match=re.search(r'background-image\s*:\s*(url\([^)]*\))',standard.get('style',''))
    if not match:raise ValueError('Original standard background is missing')
    background=match[1]
    # Known old architecture chrome reconstruction. Keep its .content z-index:
    # stacking repair belongs to the native mapper, not an HTML workaround.
    selectors=['.slide.kriss-std-template','.slide.kriss-std-template::before',
      '.slide.kriss-std-template .kriss-title','.slide.kriss-std-template .kriss-title span',
      '.slide.kriss-std-template .template-dot','.slide.kriss-std-template .template-dot.d1',
      '.slide.kriss-std-template .template-dot.d2','.slide.kriss-std-template .template-footer',
      '.slide.variant-dark','.slide.variant-dark .kriss-title']
    for selector in selectors:
        html=re.sub(re.escape(selector)+r'\s*\{[^{}]*\}','',html)
    removed=[]
    pattern=r'<div\b[^>]*class=["\']([^"\']*)["\'][^>]*>\s*</div>'
    def remove(m):
        if set(m[1].split())&{'template-dot','template-footer'}:removed.append(m[1]);return ''
        return m[0]
    html=re.sub(pattern,remove,html)
    html=re.sub(r'<style\b[^>]*id=["\']kriss-standard-chrome["\'][^>]*>[\s\S]*?</style>\n?','',html,flags=re.I)
    count=0;dark=0
    def slide(m):
        nonlocal count,dark
        tag,body=m[1],m[2];a=Tag(tag).attrs;classes=a.get('class','').split()
        if not (set(classes)&{'std','kriss-std-template','variant-dark'}):return m[0]
        if 'variant-dark' in classes:
            dark+=1
            if 'std' not in classes:classes.append('std');tag=set_attr(tag,'class',' '.join(classes))
            if not re.search(r'class=["\'][^"\']*\bkriss-title\b',body):body='<div class="kriss-title"><span>[핵심 메시지 / 강조]</span></div>'+body
        tag=set_attr(tag,'data-template-family','standard')
        style=a.get('style','')
        # Exact image URI copied without decoding/re-encoding/resampling.
        style=re.sub(r'background-image\s*:\s*url\([^)]*\)\s*(?:!important)?\s*;?','',style).strip().rstrip(';')
        style=(style+';' if style else '')+'background-image:'+background
        tag=set_attr(tag,'style',style)
        count+=1
        return tag+body+'</section>'
    html=re.sub(r'(<section\b[^>]*>)([\s\S]*?)</section>',slide,html,flags=re.I)
    # Derive shared title rules verbatim from reference; no new title calibration.
    rules=[]
    for selector in ['.kriss-title','.kriss-title span']:
        found=re.findall(re.escape(selector)+r'\s*\{([^{}]*)\}',reference)
        for body in found:rules.append('.slide[data-template-family="standard"] '+selector+'{'+body+'}')
    font=re.search(r'--font\s*:\s*([^;}]+)',reference)
    if font:rules.append('.slide[data-template-family="standard"] .kriss-title span{font-family:'+font[1]+'!important}')
    rules.append('.slide[data-template-family="standard"]{background-color:#fff;background-position:center;background-size:cover;background-repeat:no-repeat}')
    # Dark emphasis is a BODY variant, not a replacement institutional master.
    rules.extend(['.slide.variant-dark .v-dark-emphasis{left:5.1%;right:4.2%;top:13.8%;bottom:6.8%;background:#4f5d5b}',
                  '.slide.variant-dark .pattern-tag{color:#8c9694}'])
    block='<style id="kriss-standard-chrome">\n/* Original artwork and title rules from reference.html; body variation only. */\n'+'\n'.join(rules)+'\n</style>\n'
    html=html.replace('</head>',block+'</head>',1)
    return html,{'standard_slides':count,'restored_dark_body_variants':dark,'removed_known_reconstruction_nodes':removed}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input',type=Path)
    parser.add_argument('--reference',type=Path,default=Path(__file__).resolve().parents[1]/'references/reference.html')
    parser.add_argument('--in-place',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.in_place and args.output:parser.error('Choose --in-place or --output')
    target=args.input if args.in_place else (args.output or args.input.with_name(args.input.stem+'.chrome.html'))
    result,report=migrate(args.input.read_text(encoding='utf-8'),args.reference.read_text(encoding='utf-8'))
    target.write_text(result,encoding='utf-8');print(report);print(target)
if __name__=='__main__':main()
