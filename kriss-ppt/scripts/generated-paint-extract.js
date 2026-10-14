/* Measure literal ::before/::after paint in the browser, then restore the DOM.
 * No marker coordinates are guessed. The pseudo is temporarily replaced with an
 * identically computed-style element. Parent/descendant geometry must not move.
 * Counters, URLs, text quote keywords and compound generated content are blocked.
 */
(index) => {
  const slide=document.querySelectorAll('.slide')[index], sr=slide.getBoundingClientRect();
  const dom=[slide,...slide.querySelectorAll('*')];
  const ignore='script,style,svg,.toolbar,.controls,.counter,.progress,.hint,.speaker-notes,[data-speaker-notes],[data-export-ignore="true"]';
  const px=x=>parseFloat(x)||0, rel=r=>({x:r.left-sr.left,y:r.top-sr.top,w:r.width,h:r.height});
  const alpha=c=>c==='transparent'?0:Number((c.match(/rgba\([^)]*,\s*([\d.]+)\)/)||[])[1]??1);
  const uid=e=>'s'+String(index+1).padStart(2,'0')+'.e'+String(dom.indexOf(e)).padStart(4,'0');
  const visible=e=>{const c=getComputedStyle(e),r=e.getBoundingClientRect();return !e.closest(ignore)&&c.display!=='none'&&c.visibility!=='hidden'&&Number(c.opacity)>.001&&r.width>0&&r.height>0;};
  const blocks=[],elements=[],handled=[],warnings=[],probes=[];
  function stack(e){const p=[];for(let n=e;n&&n!==slide;n=n.parentElement){let z=getComputedStyle(n).zIndex;if(z!=='auto')p.unshift(parseInt(z)||0);}return p.length?p:[0];}
  function st(c,e,lh){let opacity=Number(c.opacity);for(let n=e;n&&n!==slide.parentElement;n=n.parentElement)opacity*=Number(getComputedStyle(n).opacity);
    return {fontFamily:c.fontFamily,fontSize:px(c.fontSize),fontWeight:c.fontWeight,fontStyle:c.fontStyle,color:c.color,textDecoration:c.textDecorationLine,lineHeightPx:c.lineHeight==='normal'?lh:px(c.lineHeight),lineHeightNormal:c.lineHeight==='normal',letterSpacingPx:px(c.letterSpacing),textAlign:c.textAlign,opacity,whiteSpace:c.whiteSpace,verticalAlign:c.verticalAlign,textTransform:c.textTransform,lang:e.closest('[lang]')?.lang||document.documentElement.lang||'en-US'};}
  for(const e of dom){if(!visible(e))continue;
    for(const pseudo of ['before','after']){
      const cs=getComputedStyle(e,'::'+pseudo),raw=cs.content;
      if(!raw||raw==='none'||raw==='normal'||cs.display==='none'||cs.visibility==='hidden'||Number(cs.opacity)<=.001)continue;
      const id=uid(e)+'.'+pseudo;
      let literal;
      try{literal=JSON.parse(raw);if(typeof literal!=='string')throw Error();}
      catch{
        const actual=window.__KRISS_DOM_PAINT?.[index]?.generated?.[id];
        if(actual&&/^counter(?:s)?\(/.test(raw)){literal=actual.text;}
        else {warnings.push({code:'unsupported-generated-content',id,detail:raw});continue;}
      }
      const painted=alpha(cs.backgroundColor)>0||cs.backgroundImage!=='none'||['Top','Right','Bottom','Left'].some(s=>px(cs['border'+s+'Width'])>0&&cs['border'+s+'Style']!=='none');
      if(!literal&&!painted){handled.push(id);continue;}
      // Rotations/scales require native transform mapping and are not silently flattened.
      if(cs.transform!=='none'){
        const m=new DOMMatrix(cs.transform);
        if(Math.abs(m.a-1)>.00001||Math.abs(m.d-1)>.00001||Math.abs(m.b)>.00001||Math.abs(m.c)>.00001){warnings.push({code:'unsupported-generated-transform',id,detail:cs.transform});continue;}
      }
      const values=Object.fromEntries([...cs].map(k=>[k,cs.getPropertyValue(k)]));
      const before=[e,...e.querySelectorAll('*')].filter(n=>!n.matches('script,style')).map(n=>[n,n.getBoundingClientRect()]);
      const token='kriss-probe-'+index+'-'+dom.indexOf(e)+'-'+pseudo;
      const attr='data-kriss-generated-probe',oldAttr=e.getAttribute(attr);
      const sheet=document.createElement('style');sheet.textContent=`[${attr}="${token}"]::${pseudo}{content:none!important;display:none!important}`;
      const span=document.createElement('span');span.setAttribute('data-export-ignore','true');
      for(const [k,v]of Object.entries(values))span.style.setProperty(k,v,'important');
      span.style.setProperty('content','normal','important');span.textContent=literal;
      let succeeded=false;
      try{
        e.setAttribute(attr,token);document.head.appendChild(sheet);
        pseudo==='before'?e.insertBefore(span,e.firstChild):e.appendChild(span);
        const r=span.getBoundingClientRect(),c=getComputedStyle(span);
        let drift=0;
        for(const[n,b]of before){const a=n.getBoundingClientRect();drift=Math.max(drift,Math.abs(a.x-b.x),Math.abs(a.y-b.y),Math.abs(a.width-b.width),Math.abs(a.height-b.height));}
        if(drift>.10){warnings.push({code:'generated-probe-layout-drift',id,deltaPx:drift});continue;}
        if(r.width<=0||r.height<=0){warnings.push({code:'generated-empty-geometry',id});continue;}
        const measure=document.createElement('span');measure.textContent='M';
        Object.assign(measure.style,{position:'fixed',visibility:'hidden',left:'-10000px',fontFamily:c.fontFamily,fontSize:c.fontSize,fontWeight:c.fontWeight,fontStyle:c.fontStyle,lineHeight:'normal'});
        document.body.appendChild(measure);const lh=measure.getBoundingClientRect().height;measure.remove();
        const style=st(c,e,lh),borders={};for(const side of ['Top','Right','Bottom','Left'])borders['border'+side]={width:px(c['border'+side+'Width']),color:c['border'+side+'Color'],style:c['border'+side+'Style']};
        const pad={left:px(c.paddingLeft),right:px(c.paddingRight),top:px(c.paddingTop),bottom:px(c.paddingBottom)};
        const cb={x:r.left-sr.left+pad.left+px(c.borderLeftWidth),y:r.top-sr.top+pad.top+px(c.borderTopWidth),w:r.width-pad.left-pad.right-px(c.borderLeftWidth)-px(c.borderRightWidth),h:r.height-pad.top-pad.bottom-px(c.borderTopWidth)-px(c.borderBottomWidth)};
        const hasPaint=alpha(c.backgroundColor)>0||c.backgroundImage!=='none'||Object.values(borders).some(b=>b.width>0&&b.style!=='none'&&alpha(b.color)>0);
        const isPct=c.borderTopLeftRadius.includes('%'),radius=isPct?px(c.borderTopLeftRadius)*Math.min(r.width,r.height)/100:px(c.borderTopLeftRadius);
        if(hasPaint)elements.push({id,order:dom.indexOf(e),stackPath:stack(e),zIndex:0,tag:'span',classes:['generated-'+pseudo],rect:rel(r),opacity:style.opacity,rotation:0,geometry:'',clipPath:c.clipPath,backgroundColor:c.backgroundColor,backgroundImage:c.backgroundImage,backgroundUrl:null,borderRadius:c.borderTopLeftRadius,borderRadiusPx:radius,boxShadow:c.boxShadow,...borders,padding:pad,generated:true});
        if(literal){
          const range=document.createRange();range.selectNodeContents(span);const gr=[...range.getClientRects()].filter(r=>r.width>.1).map(rel);
          let text=literal;if(c.textTransform==='uppercase')text=text.toUpperCase();if(c.textTransform==='lowercase')text=text.toLowerCase();
          const par={id,...style,rect:cb,glyphRects:gr,lineCount:1,runs:[{...style,text}],spaceBefore:0,spaceAfter:0};
          blocks.push({id,tag:'span',classes:['generated-'+pseudo],ownerRect:rel(r),contentRect:cb,paragraphs:[par],verticalAnchor:'top',mergeVisual:hasPaint&&c.backgroundImage==='none',wrap:'intrinsic-nowrap',role:'generated-marker',plainText:text,generated:{owner:uid(e),pseudo,raw,inlineFlow:values.display==='inline'&&values.position==='static'&&!hasPaint&&c.boxShadow==='none'&&values.transform==='none'&&['padding-top','padding-right','padding-bottom','padding-left','margin-top','margin-right','margin-bottom','margin-left'].every(k=>px(values[k])===0)&&values['vertical-align']==='baseline'},stackPath:stack(e)});
        }
        handled.push(id);probes.push({id,layoutDeltaPx:drift,rect:rel(r),content:literal});succeeded=true;
      }finally{
        span.remove();sheet.remove();oldAttr===null?e.removeAttribute(attr):e.setAttribute(attr,oldAttr);
        if(succeeded){for(const[n,b]of before){const a=n.getBoundingClientRect();if(Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y),Math.abs(a.width-b.width),Math.abs(a.height-b.height))>.1)warnings.push({code:'generated-probe-restoration-drift',id});}}
      }
    }
  }
  const result={blocks,elements,handled,warnings,probes};
  window.__KRISS_GENERATED_CAPTURE??={};window.__KRISS_GENERATED_CAPTURE[index]=result;
  return result;
}
