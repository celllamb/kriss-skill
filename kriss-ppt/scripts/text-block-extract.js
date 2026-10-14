(index) => {
  const slide=document.querySelectorAll('.slide')[index],sr=slide.getBoundingClientRect();
  const ignore='script,style,svg,.toolbar,.controls,.counter,.progress,.hint,.speaker-notes,[data-speaker-notes],[data-export-ignore="true"]';
  const px=v=>parseFloat(v)||0;
  const rel=r=>({x:r.left-sr.left,y:r.top-sr.top,w:r.width,h:r.height});
  const dom=[slide,...slide.querySelectorAll('*')],uid=e=>'s'+String(index+1).padStart(2,'0')+'.e'+String(dom.indexOf(e)).padStart(4,'0');
  const generated=window.__KRISS_GENERATED_CAPTURE?.[index]||{blocks:[],handled:[],warnings:[]};
  const markers=window.__KRISS_MARKER_CAPTURE?.[index]||{blocks:[],handled:[],warnings:[]};
  const warnings=[...generated.warnings,...markers.warnings],blocks=[],lineCache=new Map();
  const generatedById=new Map(generated.blocks.map(b=>[b.id,b]));
  const consumedGenerated=new Set();
  function inlinePseudo(e,name,out){
    const b=generatedById.get(uid(e)+'.'+name);
    if(!b?.generated?.inlineFlow)return;
    // Only inline run flow is merged; independent paint/block/positioned pseudo
    // content retains its own object and must pass its own parity checks.
    if([...e.children].some(k=>visible(k)&&!isInline(k,e)))return;
    for(const run of b.paragraphs[0].runs)out.push({...run,sourceGeneratedId:b.id});
    consumedGenerated.add(b.id);
  }
  function normalHeight(c){const key=c.fontFamily+'|'+c.fontSize+'|'+c.fontWeight+'|'+c.fontStyle;if(lineCache.has(key))return lineCache.get(key);
    const q=document.createElement('div');Object.assign(q.style,{position:'fixed',left:'-10000px',top:'0',visibility:'hidden',width:'max-content',height:'auto',margin:'0',padding:'0',border:'0',fontFamily:c.fontFamily,fontSize:c.fontSize,fontWeight:c.fontWeight,fontStyle:c.fontStyle,lineHeight:'normal',whiteSpace:'nowrap'});q.textContent='M';document.body.appendChild(q);const h=q.getBoundingClientRect().height;q.remove();lineCache.set(key,h);return h;
  }
  function visible(e){if(!e||e.closest(ignore))return false;const c=getComputedStyle(e),r=e.getBoundingClientRect();return c.display!=='none'&&c.visibility!=='hidden'&&px(c.opacity)>0&&r.width>0&&r.height>0;}
  function alpha(c){return c==='transparent'?0:((c.match(/rgba\([^)]*,\s*([\d.]+)\)/)||[])[1]??1);}
  function visual(e){const c=getComputedStyle(e);return Number(alpha(c.backgroundColor))>0||c.backgroundImage!=='none'||['Top','Right','Bottom','Left'].some(s=>px(c['border'+s+'Width'])&&c['border'+s+'Style']!=='none');}
  function content(e){const r=e.getBoundingClientRect(),c=getComputedStyle(e),l=px(c.borderLeftWidth)+px(c.paddingLeft),t=px(c.borderTopWidth)+px(c.paddingTop),rr=px(c.borderRightWidth)+px(c.paddingRight),b=px(c.borderBottomWidth)+px(c.paddingBottom);return {x:r.left-sr.left+l,y:r.top-sr.top+t,w:Math.max(0,r.width-l-rr),h:Math.max(0,r.height-t-b)};}
  function style(e){const c=getComputedStyle(e);let opacity=1;for(let n=e;n&&n!==slide.parentElement;n=n.parentElement)opacity*=px(getComputedStyle(n).opacity);
    return {fontFamily:c.fontFamily,fontSize:px(c.fontSize),fontWeight:c.fontWeight,fontStyle:c.fontStyle,color:c.color,textDecoration:c.textDecorationLine,lineHeightPx:c.lineHeight==='normal'?normalHeight(c):px(c.lineHeight),lineHeightNormal:c.lineHeight==='normal',letterSpacingPx:px(c.letterSpacing),textAlign:c.textAlign,opacity,whiteSpace:c.whiteSpace,verticalAlign:c.verticalAlign,textTransform:c.textTransform,lang:e.closest('[lang]')?.lang||document.documentElement.lang||'en-US',hyperlink:e.closest('a[href]')?.href||null,hyperlinkSourceId:e.closest('a[href]')?uid(e.closest('a[href]')):null};}
  const inline=new Set(['SPAN','B','STRONG','I','EM','SMALL','CODE','A','U','SUP','SUB','BR','MARK']);
  function isInline(e,root){return (e.tagName==='BR'||(inline.has(e.tagName)&&['inline','contents'].includes(getComputedStyle(e).display)))&&(!visual(e)||e===root)&&!['absolute','fixed'].includes(getComputedStyle(e).position);}
  function simple(e){if(!visible(e)||e===slide||e.matches('.deck,.content,[data-pptx-text-block="false"]')||!e.textContent.trim())return false;
    if(e.querySelector('img,svg,table,ul,ol,video,canvas'))return false;
    const kids=[...e.children].filter(visible);
    for(const k of kids){if(!isInline(k,e)&&!['block','list-item'].includes(getComputedStyle(k).display))return false;
      if(visual(k)||['absolute','fixed'].includes(getComputedStyle(k).position))return false;
      if(!isInline(k,e)){const cs=getComputedStyle(e),kr=content(k),er=content(e);if(cs.display.includes('grid')||cs.display.includes('flex')||Math.abs(kr.x-er.x)>1||Math.abs(kr.w-er.w)>1)return false;}
      if([...k.querySelectorAll('*')].some(d=>!isInline(d,e)))return false;
    }
    // Sequential anonymous inline groups and block children are paragraphs, not independent geometry.
    return true;
  }
  function runs(root,nodes=null){const out=[];function rec(n){if(n.nodeType===3){let t=n.nodeValue;if(!t)return;const st=style(n.parentElement);if(!/pre|break-spaces/.test(st.whiteSpace))t=t.replace(/[\t\n\r ]+/g,' ');if(['uppercase','lowercase'].includes(st.textTransform)){
      const ordinal=[...n.parentElement.childNodes].filter(q=>q.nodeType===3).indexOf(n);
      const key=uid(n.parentElement)+'.t'+ordinal, measured=window.__KRISS_DOM_PAINT?.[index]?.resolved_text?.[key];
      if(measured&&measured.raw===n.nodeValue)t=measured.rendered;
      else warnings.push({code:'unmeasured-browser-text-transform',id:uid(n.parentElement),detail:key});
    }
      // CSS pre/pre-wrap/break-spaces preserve newlines. DrawingML a:t does
      // not carry a hard-linebreak contract; serialize each LF as a:br via
      // semantic break runs, including blank lines. Text remains one block.
      if(/pre|break-spaces/.test(st.whiteSpace)&&/[\r\n]/.test(t)){
        const lines=t.replace(/\r\n?/g,'\n').split('\n');
        lines.forEach((line,i)=>{if(i)out.push({break:true});if(line)out.push({...st,text:line});});
      }else out.push({...st,text:t});return;}
      if(n.nodeType!==1||n.closest(ignore))return;if(n.tagName==='BR'){out.push({break:true});return;}if(!visible(n))return;
      inlinePseudo(n,'before',out);for(const k of n.childNodes)rec(k);inlinePseudo(n,'after',out);
    }if(nodes)nodes.forEach(rec);else rec(root);
    // Collapse inter-node whitespace without deleting spaces at style boundaries.
    let atStart=true,space=false;
    for(const r of out){if(r.break){atStart=true;space=false;continue;}if(!/pre|break-spaces/.test(r.whiteSpace)){if(atStart||space)r.text=r.text.replace(/^ +/,'');space=r.text.endsWith(' ');if(r.text)atStart=false;}}
    for(let i=out.length-1;i>=0;i--){if(out[i].break)continue;if(out[i].text){out[i].text=out[i].text.replace(/ +$/,'');break;}}
    return out.filter(x=>x.break||x.text);
  }
  function glyphs(e,nodes=null){const a=[];
    function text(n){if(!n.textContent.trim()||!visible(n.parentElement))return;const r=document.createRange();r.selectNodeContents(n);for(const q of r.getClientRects())if(q.width>.1)a.push(rel(q));}
    for(const root of nodes||[e]){if(root.nodeType===3){text(root);continue;}const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);for(let n;n=w.nextNode();)text(n);}
    return a;
  }
  function groups(e){
    const block=[...e.children].filter(k=>visible(k)&&!isInline(k,e));
    if(!block.length)return [{element:e}];
    const result=[];let pending=[];
    const flush=()=>{if(pending.some(n=>n.textContent.trim()||n.nodeName==='BR'))result.push({element:e,nodes:pending});pending=[];};
    for(const n of e.childNodes){
      if(n.nodeType===1&&block.includes(n)){flush();result.push({element:n});}
      else if(n.nodeType===3||(n.nodeType===1&&visible(n)))pending.push(n);
    }
    flush();return result;
  }
  function capture(e){const c=getComputedStyle(e),r=e.getBoundingClientRect(),cb=content(e),children=[...e.children].filter(visible);
    const pieces=groups(e),ps=pieces.map(g=>g.element);
    const paragraphs=pieces.map(g=>{const p=g.element,rr=runs(p,g.nodes),gr=glyphs(p,g.nodes);
      for(const id of new Set(rr.map(r=>r.sourceGeneratedId).filter(Boolean)))gr.push(...generatedById.get(id).paragraphs[0].glyphRects);
      let st=style(p),pr=content(p);
      if(g.nodes){
        const largest=rr.filter(x=>!x.break).sort((a,b)=>b.fontSize-a.fontSize)[0];
        if(largest)st={...largest};delete st.text;
        const top=gr.length?Math.min(...gr.map(q=>q.y)):cb.y,bottom=gr.length?Math.max(...gr.map(q=>q.y+q.h)):top+st.lineHeightPx;
        pr={x:cb.x,y:top,w:cb.w,h:bottom-top};
      }
      st.lineHeightPx=Math.max(st.lineHeightPx,...rr.filter(x=>!x.break).map(x=>x.lineHeightPx));
      const rows=[];for(const q of gr){if(!rows.some(y=>Math.abs(y-q.y)<Math.max(2,st.fontSize*.3)))rows.push(q.y);}rows.sort((a,b)=>a-b);
      return {id:uid(p),...st,rect:pr,glyphRects:gr,lineCount:Math.max(1,rows.length),runs:rr,spaceBefore:0,spaceAfter:0};});
    // CSS collapsed margins are measured from the actual positions, not added twice.
    for(let i=0;i<paragraphs.length-1;i++)paragraphs[i].spaceAfter=Math.max(0,paragraphs[i+1].rect.y-(paragraphs[i].rect.y+paragraphs[i].rect.h));
    let area={...cb};let valign='top';const flex=c.display.includes('flex'),grid=c.display.includes('grid');
    if(flex||grid){const vertical=flex?(c.flexDirection.startsWith('column')?c.justifyContent:c.alignItems):c.alignItems;
      if(vertical==='center')valign='middle';if(['end','flex-end'].includes(vertical))valign='bottom';
      const horizontal=flex?(c.flexDirection.startsWith('column')?c.alignItems:c.justifyContent):c.justifyItems;
      if(ps.length===1&&ps[0]===e&&['center','end','flex-end'].includes(horizontal))paragraphs[0].textAlign=horizontal==='center'?'center':'right';
    }else if(pieces.length>1||ps[0]!==e){area.y=paragraphs[0].rect.y;area.h=paragraphs.at(-1).rect.y+paragraphs.at(-1).rect.h-area.y;}
    const pseudo=['::before','::after'].map(p=>getComputedStyle(e,p).content).filter(t=>t&&t!=='none'&&t!=='normal'&&t!=='""');
    for(const name of ['before','after']){const pc=getComputedStyle(e,'::'+name),value=pc.content;if(pc.display!=='none'&&pc.visibility!=='hidden'&&value&&value!=='none'&&value!=='normal'&&value!=='""'&&!generated.handled.includes(uid(e)+'.'+name))warnings.push({code:'generated-content',id:uid(e)+'.'+name,detail:value});}
    if(c.transform!=='none'){const m=new DOMMatrix(c.transform);if(Math.abs(m.a-1)>1e-6||Math.abs(m.d-1)>1e-6||Math.abs(m.b)>1e-6||Math.abs(m.c)>1e-6)warnings.push({code:'transformed-text',id:uid(e),detail:c.transform});}
    if(paragraphs.some(p=>p.runs.some(r=>['super','sub'].includes(r.verticalAlign))))warnings.push({code:'baseline-shift',id:uid(e)});
    const glyphBounds=paragraphs.flatMap(p=>p.glyphRects);const glyphWidth=glyphBounds.length?Math.max(...glyphBounds.map(q=>q.x+q.w))-Math.min(...glyphBounds.map(q=>q.x)):0;
    const intrinsicMeasured=String(e.computedStyleMap?.().get('width')||'')==='auto'&&paragraphs.length===1&&paragraphs[0].lineCount===1&&Math.abs(cb.w-glyphWidth)<.15;
    blocks.push({sourceGeneratedIds:[...new Set(paragraphs.flatMap(p=>p.runs.map(r=>r.sourceGeneratedId).filter(Boolean)))],id:uid(e),tag:e.tagName.toLowerCase(),classes:[...e.classList],ownerRect:rel(r),contentRect:area,paragraphs,verticalAnchor:valign,mergeVisual:visual(e)&&c.backgroundImage==='none',wrap:e.dataset.pptxWrap||((intrinsicMeasured||['nowrap','pre'].includes(c.whiteSpace)||((['inline','inline-block'].includes(c.display)||(c.position==='absolute'&&String(e.computedStyleMap?.().get('right')||c.right)==='auto'))&&String(e.computedStyleMap?.().get('width')||'auto')==='auto'))?'intrinsic-nowrap':'native'),role:e.dataset.textRole||(/H[1-6]/.test(e.tagName)?'heading':'body'),plainText:paragraphs.map(p=>p.runs.map(r=>r.break?'\v':r.text).join('')).join('\n')});
  }
  function walk(e){if(!visible(e))return;if(simple(e)){capture(e);return;}
    // Mixed direct text with independent child geometry is explicit unsupported,
    // never silently dropped or split into per-character/line boxes.
    if([...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())&&!e.matches('script,style'))warnings.push({code:'mixed-independent-text',id:uid(e),text:[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim()});
    for(const ch of e.children)walk(ch);
  }walk(slide);
  // Never silently accept unsupported paint/marker semantics. These are release
  // blockers, not permission to rasterize the composed content.
  for(const e of slide.querySelectorAll('*')){if(!visible(e))continue;const c=getComputedStyle(e);
    if(c.clipPath&&c.clipPath!=='none')warnings.push({code:'unsupported-css-clip-path',id:uid(e),detail:c.clipPath});
    if(c.filter&&c.filter!=='none')warnings.push({code:'unsupported-css-filter',id:uid(e),detail:c.filter});
    if(c.borderImageSource&&c.borderImageSource!=='none')warnings.push({code:'unsupported-border-image',id:uid(e),detail:c.borderImageSource});
    if(e.tagName==='LI'&&c.display==='list-item'&&c.listStyleType!=='none'&&!markers.handled.includes(uid(e)+'.marker'))warnings.push({code:'list-marker-needs-native-support',id:uid(e),detail:c.listStyleType});
    if(e.namespaceURI==='http://www.w3.org/2000/svg'&&!['svg','line','defs','marker'].includes(e.tagName.toLowerCase()))warnings.push({code:'unsupported-svg-primitive',id:uid(e),detail:e.tagName});
    if(c.backgroundImage!=='none'&&!c.backgroundImage.startsWith('url(')&&e!==slide)warnings.push({code:'unsupported-component-background',id:uid(e)});
  }
  blocks.push(...generated.blocks.filter(b=>!consumedGenerated.has(b.id)),...markers.blocks);
  const fontFamilies=[...new Set(blocks.flatMap(b=>b.paragraphs.flatMap(p=>p.runs.filter(r=>!r.break).map(r=>r.fontFamily.split(',')[0].replace(/['"]/g,'').trim()))))];
  return {blocks,warnings,fontFamilies,slideRect:rel(sr),deck:{w:sr.width,h:sr.height}};
}
