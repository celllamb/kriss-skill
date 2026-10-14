"""Read-only original KRISS artwork gate, independent of authored CSS overrides.

The reference HTML is authoritative. Original image bytes, background placement
and the visible immutable header/footer are checked separately. This module never
repairs the user's DOM or substitutes a different PPTX background.
"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import base64
import hashlib
import re
import numpy as np
from PIL import Image, ImageDraw
from resource_capture import read_source_bytes


class ReferenceChrome:
    def __init__(self, browser, reference: Path, viewport: dict):
        self.page = browser.new_page(viewport=viewport, device_scale_factor=1)
        self.page.route('**/*', lambda r:r.abort() if r.request.url.startswith(('http://','https://')) else r.continue_())
        text = re.sub(r'<script\b[^>]*>[\s\S]*?</script>', '', reference.read_text(encoding='utf-8'), flags=re.I)
        self.page.set_content(text, wait_until='load')
        self.page.evaluate('document.fonts.ready')
        self.page.add_style_tag(content='.progress,.counter,.toolbar,.hint,.controls,.speaker-notes,[data-speaker-notes],[data-export-ignore="true"]{display:none!important}.deck{box-shadow:none!important}')
        self.reference_sha256 = hashlib.sha256(reference.read_bytes()).hexdigest()
        self.families = {}
        for family, selector in [('standard','.slide.std'),('cover','.slide.cover'),('divider','.slide.divider')]:
            if not self.page.locator(selector).count():continue
            meta=self.page.evaluate('''selector=>{
              const e=document.querySelector(selector), all=[...document.querySelectorAll('.slide')];
              all.forEach(s=>s.classList.toggle('active',s===e));
              const c=getComputedStyle(e),r=e.getBoundingClientRect();
              const rel=n=>{const q=n.getBoundingClientRect();return {x:q.x-r.x,y:q.y-r.y,w:q.width,h:q.height};};
              return {backgroundImage:c.backgroundImage,backgroundSize:c.backgroundSize,
                backgroundPosition:c.backgroundPosition,backgroundRepeat:c.backgroundRepeat,
                rect:rel(e),content:e.querySelector('.content')?rel(e.querySelector('.content')):null,
                title:e.querySelector('.kriss-title')?rel(e.querySelector('.kriss-title')):null};
            }''',selector)
            m=re.fullmatch(r'url\(["\']?(.*?)["\']?\)',meta.pop('backgroundImage'))
            if not m:raise ValueError('Reference family lacks one original background image: '+family)
            data=read_source_bytes(m[1],{})
            meta.update(src=m[1],asset_sha256=hashlib.sha256(data).hexdigest(),asset_bytes=data)
            # Visibility applies only to this temporary reference page.
            sheet=self.page.add_style_tag(content='.slide *{visibility:hidden!important}')
            meta['background_render']=Image.open(BytesIO(self.page.locator(selector).first.screenshot(animations='disabled'))).convert('RGB')
            sheet.evaluate('(e)=>e.remove()')
            self.families[family]=meta

    def close(self):self.page.close()

    def check(self,page,index:int,snapshot:bytes)->dict:
        actual=page.evaluate('''index=>{
          const e=document.querySelectorAll('.slide')[index],c=getComputedStyle(e),r=e.getBoundingClientRect();
          const family=e.dataset.templateFamily||((e.matches('.cover'))?'cover':e.matches('.divider')?'divider':
            (e.matches('.std,.kriss-std-template,.variant-dark')||e.querySelector('.kriss-title'))?'standard':null);
          const rect=n=>{const q=n.getBoundingClientRect();return {x:q.x-r.x,y:q.y-r.y,w:q.width,h:q.height};};
          return {family,backgroundImage:c.backgroundImage,backgroundSize:c.backgroundSize,backgroundPosition:c.backgroundPosition,
            backgroundRepeat:c.backgroundRepeat,rect:rect(e),labels:[...e.querySelectorAll('.pattern-tag,.candidate-label')].map(rect)};
        }''',index)
        family=actual['family']
        row={'slide':index+1,'family':family,'applicable':bool(family),'pass':True,'errors':[]}
        if not family:return row
        expected=self.families.get(family)
        if not expected:
            row['errors'].append({'code':'unknown-reference-template-family','family':family});row['pass']=False;return row
        row['reference_asset_sha256']=expected['asset_sha256']
        m=re.fullmatch(r'url\(["\']?(.*?)["\']?\)',actual['backgroundImage'])
        if m:
            try:row['authored_asset_sha256']=hashlib.sha256(read_source_bytes(m[1],{})).hexdigest()
            except ValueError:row['authored_asset_sha256']=None
        else:row['authored_asset_sha256']=None
        row['asset_bytes_equal']=row['authored_asset_sha256']==expected['asset_sha256']
        if not row['asset_bytes_equal']:row['errors'].append({'code':'original-template-image-missing-or-replaced'})
        row['placement_equal']=all(actual[k]==expected[k] for k in ['backgroundSize','backgroundPosition','backgroundRepeat','rect'])
        if not row['placement_equal']:row['errors'].append({'code':'original-template-image-placement-changed'})
        # Standard content may vary; header/footer artwork may not. Mask only the
        # reference's content/title slots and explicit small pattern annotations.
        if family=='standard':
            image=Image.open(BytesIO(snapshot)).convert('RGB');reference=expected['background_render']
            if image.size!=reference.size:
                row['errors'].append({'code':'template-viewport-mismatch'})
            else:
                mask=Image.new('1',image.size,1);draw=ImageDraw.Draw(mask)
                def exclude(r,pad=1):
                    if r:draw.rectangle([int(r['x'])-pad,int(r['y'])-pad,int(r['x']+r['w'])+pad,int(r['y']+r['h'])+pad],fill=0)
                exclude(expected['content'])
                title=expected['title']
                if title:exclude({**title,'w':image.width-title['x']},pad=2)
                for label in actual['labels']:
                    if label['w']<=image.width*.5 and label['h']<=image.height*.05 and label['y']>=image.height*.9:exclude(label,pad=2)
                # Blank slide margins may contain legitimate body shadows. Compare the
                # original artwork ink itself, not white margin pixels. No pixel
                # tolerance is applied to the selected fixed artwork.
                artwork=(255-np.asarray(reference).astype(np.int16)).max(2)>16
                pixels=np.asarray(mask).astype(bool)&artwork
                diff=np.abs(np.asarray(image).astype(np.int16)-np.asarray(reference).astype(np.int16))
                delta=diff[pixels]
                row['fixed_region']={'pixel_count':int(pixels.sum()),'mean':float(delta.mean()),
                    'changed_pixels':int((delta.max(1)>0).sum()),'max_channel_difference':int(delta.max()),'pass':bool(not delta.any())}
                if not row['fixed_region']['pass']:row['errors'].append({'code':'original-template-artwork-covered-or-altered'})
        row['pass']=not row['errors']
        return row

    def original_asset_for(self,check):
        if check.get('asset_bytes_equal') and check.get('placement_equal'):
            meta=self.families[check['family']]
            return {'src':meta['src'],'sha256':meta['asset_sha256'],'bytes':meta['asset_bytes']}
        return None
