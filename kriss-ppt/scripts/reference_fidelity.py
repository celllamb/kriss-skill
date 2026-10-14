"""Check authored standard-title defaults against the actual reference document.

Read-only. Does not force CSS, change the DOM, or recolor PPTX. Intentional default
changes require a property allowlist AND an authoring reason in the HTML.
"""
from __future__ import annotations
from pathlib import Path
import re

TITLE_JS = r'''() => [...document.querySelectorAll('.kriss-title,[data-reference-role="standard-title"]')].map(e=>{
  const t=e.querySelector('span')||e,c=getComputedStyle(e),s=getComputedStyle(t),slide=e.closest('.slide'),r=e.getBoundingClientRect(),sr=slide?.getBoundingClientRect();
  return {slide:slide?[...document.querySelectorAll('.slide')].indexOf(slide)+1:null,
    style:{fontFamily:s.fontFamily,fontSize:s.fontSize,fontWeight:s.fontWeight,fontStyle:s.fontStyle,color:s.color,letterSpacing:s.letterSpacing,lineHeight:s.lineHeight,whiteSpace:s.whiteSpace,display:c.display,alignItems:c.alignItems,height:c.height,left:c.left,top:c.top},
    allowed:(e.dataset.referenceOverrides||'').split(',').map(x=>x.trim()).filter(Boolean),reason:e.dataset.referenceOverrideReason||'',text:t.textContent};
})'''


def compare_titles(expected: dict, actual: list[dict]) -> dict:
    rows=[]
    for item in actual:
        differences=[]
        for prop,value in expected.items():
            got=item['style'].get(prop)
            if got!=value:
                approved=prop in item['allowed'] and bool(item['reason'].strip())
                differences.append({'property':prop,'reference':value,'authored':got,'declared_override':approved,'reason':item['reason'] if approved else ''})
        rows.append({'slide':item['slide'],'text':item['text'],'differences':differences,'pass':all(x['declared_override'] for x in differences)})
    return {'applicable':bool(actual),'pass':all(x['pass'] for x in rows),'reference_style':expected,'titles':rows,
            'scope':'Reference to authored-HTML standard-title defaults; not font-renderer parity. Unmarked synthetic .title fixtures are not reference design demonstrations.'}


def check_titles(browser, page, reference_path:Path, viewport:dict, offline:bool, actual_titles:list[dict]) -> dict:
    rp=browser.new_page(viewport=viewport,device_scale_factor=1)
    try:
        if offline:rp.route('**/*',lambda route:route.abort() if route.request.url.startswith(('http://','https://')) else route.continue_())
        # Defaults are CSS/DOM, not the legacy demo's interactive/adaptive scripts.
        reference_html=re.sub(r'<script\b[^>]*>[\s\S]*?</script>','',reference_path.read_text(),flags=re.I)
        rp.set_content(reference_html,wait_until='load',timeout=60000)
        rp.evaluate('document.fonts.ready')
        # Hidden display:none slides can return unresolved percentage geometry.
        # Measure the reference title only after normal activation on this
        # temporary reference page. Authored titles come from each settled
        # active capture, not from hidden slides or a changed style override.
        rp.evaluate("""()=>{const target=document.querySelector('.kriss-title,[data-reference-role=standard-title]')?.closest('.slide');document.querySelectorAll('.slide').forEach(s=>s.classList.toggle('active',s===target))}""")
        titles=rp.evaluate(TITLE_JS)
        if not titles:raise ValueError('No standard reference title found')
        report=compare_titles(titles[0]['style'],actual_titles)
        missing=page.evaluate("""() => [...document.querySelectorAll('.slide')].flatMap((e,i)=>e.classList.contains('std')&&!e.querySelector('.kriss-title,[data-reference-role="standard-title"]')?[i+1]:[])""")
        diagnostic=page.locator('meta[name="kriss-diagnostic"][content="true"]').count()>0
        report['diagnostic_fixture']=diagnostic
        report['unbound_standard_title_slides']=missing
        if missing and not diagnostic:
            report['pass']=False
            report['error']='Standard slides must bind their title to reference defaults; an unmarked custom title is not a verified title.'
        return report
    finally:rp.close()
