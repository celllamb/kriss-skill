"""Read actual Chromium ::marker layout/text; no guessed marker coordinates.

Uses DOMSnapshot.captureSnapshot. The original DOM is never rewritten to measure
list counters. Unsupported/missing marker layout remains a source-coverage error.
"""
from __future__ import annotations

PROPERTIES = ['font-family','font-size','font-weight','font-style','color','line-height',
              'letter-spacing','text-align','white-space','text-decoration-line']


def capture_markers(page, index: int) -> dict:
    if not page.locator('.slide').nth(index).locator('li').count():
        result={'blocks': [], 'handled': [], 'warnings': []}
        page.evaluate('(a)=>{window.__KRISS_MARKER_CAPTURE??={};window.__KRISS_MARKER_CAPTURE[a.index]=a.result;}',{'index':index,'result':result})
        return result
    session=page.context.new_cdp_session(page)
    try:
        snapshot=session.send('DOMSnapshot.captureSnapshot',{'computedStyles':PROPERTIES,'includeDOMRects':True})
    finally:
        session.detach()
    strings=snapshot['strings'];document=snapshot['documents'][0]
    nodes=document['nodes'];layout=document['layout'];parents=nodes['parentIndex']
    def string(n):return strings[n] if n>=0 else ''
    def attrs(i):
        values=nodes['attributes'][i]
        return {string(values[k]):string(values[k+1]) for k in range(0,len(values),2)}
    slides=[i for i,t in enumerate(nodes['nodeType']) if t==1 and 'slide' in attrs(i).get('class','').split()]
    target=slides[index]
    pseudo={i:string(v) for i,v in zip(nodes.get('pseudoType',{}).get('index',[]),nodes.get('pseudoType',{}).get('value',[]))}
    descendants={};identity={}
    for i in range(len(parents)):
        descendants[i]=i==target or descendants.get(parents[i],False)
        if descendants[i] and nodes['nodeType'][i]==1 and i not in pseudo:
            identity[i]=f's{index+1:02d}.e{len(identity):04d}'
    origins=page.locator('.slide').nth(index).bounding_box()
    sx,sy=origins['x'],origins['y']
    def rect(bounds):return {'x':bounds[0]-sx,'y':bounds[1]-sy,'w':bounds[2],'h':bounds[3]}
    def px(value):
        try:return float(value.removesuffix('px'))
        except ValueError:return 0.0
    owner_info=page.evaluate('''index=>{
      const s=document.querySelectorAll('.slide')[index],dom=[s,...s.querySelectorAll('*')],result={};
      dom.forEach((e,i)=>{if(getComputedStyle(e).display!=='list-item')return;
        let opacity=1;for(let n=e;n&&n!==s.parentElement;n=n.parentElement)opacity*=Number(getComputedStyle(n).opacity);
        const stack=[];for(let n=e;n&&n!==s;n=n.parentElement){const z=getComputedStyle(n).zIndex;if(z!=='auto')stack.unshift(parseInt(z)||0);}
        result['s'+String(index+1).padStart(2,'0')+'.e'+String(i).padStart(4,'0')]={opacity,stackPath:stack.length?stack:[0],lang:e.closest('[lang]')?.lang||document.documentElement.lang||'en-US'};
      });return result;
    }''',index)
    blocks=[];warnings=[];handled=[]
    for node,kind in pseudo.items():
        if kind!='marker' or parents[node] not in identity:continue
        owner=identity[parents[node]];uid=owner+'.marker'
        entries=[i for i,n in enumerate(layout['nodeIndex']) if n==node]
        textual=[i for i in entries if string(layout['text'][i])]
        if not textual:continue
        if len(textual)!=1:
            warnings.append({'code':'unsupported-multi-fragment-marker','id':uid});continue
        j=textual[0];text=string(layout['text'][j]);style=dict(zip(PROPERTIES,[string(n) for n in layout['styles'][j]]))
        if not text.strip():continue
        outer=rect(layout['bounds'][entries[0]]);glyph=rect(layout['bounds'][j])
        meta=owner_info.get(owner)
        if not meta or meta['opacity']<=0:continue
        if outer['w']<=0 or outer['h']<=0:
            warnings.append({'code':'empty-marker-layout','id':uid});continue
        st={'fontFamily':style['font-family'],'fontSize':px(style['font-size']),
            'fontWeight':style['font-weight'],'fontStyle':style['font-style'],'color':style['color'],
            'lineHeightPx':outer['h'],'lineHeightNormal':style['line-height']=='normal',
            'letterSpacingPx':px(style['letter-spacing']),'textAlign':'left','whiteSpace':'nowrap',
            'textDecoration':style['text-decoration-line'],'verticalAlign':'baseline','textTransform':'none',
            'opacity':meta['opacity'],'lang':meta['lang']}
        paragraph={'id':uid,**st,'rect':outer,'glyphRects':[glyph],'lineCount':1,
                   'runs':[{**st,'text':text}],'spaceBefore':0,'spaceAfter':0}
        blocks.append({'id':uid,'tag':'::marker','classes':['generated-marker'],'ownerRect':outer,
            'contentRect':outer,'paragraphs':[paragraph],'verticalAnchor':'top','mergeVisual':False,
            'wrap':'intrinsic-nowrap','role':'generated-marker','plainText':text,
            'stackPath':meta['stackPath'],'generated':{'owner':owner,'pseudo':'marker','measurement':'Chromium DOMSnapshot'}})
        handled.append(uid)
    result={'blocks':blocks,'handled':handled,'warnings':warnings}
    page.evaluate('(a)=>{window.__KRISS_MARKER_CAPTURE??={};window.__KRISS_MARKER_CAPTURE[a.index]=a.result;}',{'index':index,'result':result})
    return result
