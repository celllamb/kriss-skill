/* KRISS adaptive runtime. HTML geometry only; no slide-number or subject rules. */
(() => {
  'use strict';
  const VERSION = 'kriss-ppt-v1.1';
  if(window.__KRISS_ADAPTIVE_VERSION===VERSION)return;
  const BASE = new WeakMap();
  const PROPS = ['height','min-height','max-height','width','min-width','max-width',
    'padding-top','padding-right','padding-bottom','padding-left','gap','row-gap','column-gap',
    'align-self','font-size','left','right','top','bottom','transform'];
  const EXCLUDE = '[data-export-ignore="true"],.speaker-notes,[data-speaker-notes],.toolbar,.controls';
  let running = false;
  const num = x => parseFloat(x) || 0;
  const all = (r,s) => [...(r.matches?.(s)?[r]:[]), ...r.querySelectorAll(s)];
  const visible = e => {const c=getComputedStyle(e),r=e.getBoundingClientRect();
    if(e.closest(EXCLUDE)||c.display==='none'||c.visibility==='hidden'||r.width<=0||r.height<=0)return false;
    for(let n=e;n;n=n.parentElement){const a=getComputedStyle(n);if(a.display==='none'||num(a.opacity)<=0)return false;}return true;};
  function remember(e) {if (!BASE.has(e)) BASE.set(e, Object.fromEntries(PROPS.map(p=>[p,[e.style.getPropertyValue(p),e.style.getPropertyPriority(p)]])));}
  function reset(e) {const b=BASE.get(e);if(b)for(const [p,[v,q]] of Object.entries(b)){
    // CSSOM serializes percentages with less precision than the parsed value.
    // Reassigning an unchanged declaration can move it by a layout quantum.
    // Restore only changed properties; leave unmodified author geometry intact.
    if(e.style.getPropertyValue(p)===v&&e.style.getPropertyPriority(p)===q)continue;
    v?e.style.setProperty(p,v,q):e.style.removeProperty(p);
  }}
  function path(e) {if(e.id)return '#'+e.id;const a=[];while(e&&e.nodeType===1){a.unshift(e.tagName.toLowerCase()+':nth-child('+([...e.parentElement?.children||[]].indexOf(e)+1)+')');if(e.classList.contains('slide'))break;e=e.parentElement;}return a.join('>');}
  function set(e,p,v,reason,log) {remember(e);const old=getComputedStyle(e).getPropertyValue(p);e.style.setProperty(p,v,'important');const val=getComputedStyle(e).getPropertyValue(p);if(old!==val)log.push({element:path(e),property:p,from:old,to:val,reason});}
  function inner(e) {const r=e.getBoundingClientRect(),c=getComputedStyle(e);return {left:r.left+num(c.borderLeftWidth)+num(c.paddingLeft),right:r.right-num(c.borderRightWidth)-num(c.paddingRight),top:r.top+num(c.borderTopWidth)+num(c.paddingTop),bottom:r.bottom-num(c.borderBottomWidth)-num(c.paddingBottom)};}
  function over(e) {
    if(!visible(e))return false;const a=inner(e),outer=e.getBoundingClientRect();let bad=false;
    const w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);
    for(let n;n=w.nextNode();){if(!n.textContent.trim()||!visible(n.parentElement))continue;const rr=document.createRange();rr.selectNodeContents(n);
      // A positioned badge may intentionally occupy its owner's padding area.
      // It is not normal-flow pressure: compare it with the owner's outer box,
      // without ignoring genuine escape beyond that owner. No class-name rules.
      let positioned=false;for(let p=n.parentElement;p&&p!==e;p=p.parentElement){if(['absolute','fixed'].includes(getComputedStyle(p).position)){positioned=true;break;}}
      const bound=positioned?outer:a;
      for(const b of rr.getClientRects())if(b.width>.2&&(b.left<bound.left-1.5||b.right>bound.right+1.5||b.top<bound.top-1.5||b.bottom>bound.bottom+1.5))bad=true;}
    for(const ch of e.children){if(!visible(ch)||['absolute','fixed'].includes(getComputedStyle(ch).position))continue;const b=ch.getBoundingClientRect();if(b.right>a.right+1.5||b.bottom>a.bottom+1.5)bad=true;}
    return bad;
  }
  function policy(e) {return e.dataset.sizePolicy || 'preserve';}
  function textOwners(e) {return all(e,'h1,h2,h3,h4,p,li,span,b,strong,small,td,th,div,code,label').filter(x=>visible(x)&&[...x.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()));}
  function shrinkGap(e,log) {const c=getComputedStyle(e);let change=false;for(const p of ['row-gap','column-gap']){const old=num(c.getPropertyValue(p)),floor=num(e.dataset.minGap||'4');if(old>floor+.2){set(e,p,Math.max(floor,old*.9)+'px','measured-overflow:gap',log);change=true;}}return change;}
  function shrinkPadding(e,log) {const c=getComputedStyle(e);let change=false;for(const p of ['padding-top','padding-right','padding-bottom','padding-left']){const old=num(c.getPropertyValue(p));const floor=num(e.dataset.minPadding||'6');if(old>floor+.2){set(e,p,Math.max(floor,old*.9)+'px','measured-overflow:padding',log);change=true;}}return change;}
  function fit(e,log) {
    // No-pressure elements are untouched. 'preserve' permits pressure relief only.
    if(!over(e))return;
    for(let i=0;i<24&&over(e);i++)if(!shrinkGap(e,log))break;
    for(let i=0;i<24&&over(e);i++)if(!shrinkPadding(e,log))break;
    if(e.dataset.fontFit==='false')return;
    const owners=textOwners(e), min=new Map(owners.map(t=>{const b=num(getComputedStyle(t).fontSize);return [t,Math.min(b,num(t.dataset.minFontPx||e.dataset.minFontPx||String(b*.85)))];}));
    // Parent and inline child may both own text: freeze every current computed size
    // before the batch so inherited sizes are not multiplied twice.
    for(let i=0;i<40&&over(e);i++){const sizes=owners.map(t=>[t,num(getComputedStyle(t).fontSize)]);let changed=false;
      for(const [t,s]of sizes)if(s>min.get(t)+.05){set(t,'font-size',Math.max(min.get(t),s-.4)+'px','measured-overflow:font-last',log);changed=true;}
      if(!changed)break;
    }
  }
  function uniform(root,log) {
    const groups=all(root,'[data-size-policy="uniform"],[data-uniform-group]');
    for(const g of groups){const peers=[...g.children].filter(x=>visible(x)&&x.dataset.noUniform!=='true');if(peers.length<2)continue;
      const max=Math.max(...peers.map(x=>x.getBoundingClientRect().height));
      // Equalize heights only. Authored column widths are not rewritten.
      for(const e of peers){const c=getComputedStyle(e),extra=c.boxSizing==='border-box'?0:num(c.paddingTop)+num(c.paddingBottom)+num(c.borderTopWidth)+num(c.borderBottomWidth);
        set(e,'height',Math.max(0,max-extra)+'px','explicit-uniform-group',log);}
    }
  }
  function updateConnectors(root=document) {
    const report=[];const get=(r,s)=>{try{return r.querySelector(s);}catch(_){return null;}};
    // Unannotated legacy SVG coordinates are preserved, not guessed.
    for(const svg of all(root,'svg[data-connector-source]')){
      const scope=svg.closest('.slide')||document,source=get(scope,svg.dataset.connectorSource);
      let targets=[];try{const t=svg.dataset.connectorTargets;targets=t?.startsWith('[')?JSON.parse(t).map(s=>get(scope,s)):[...scope.querySelectorAll(t||'[data-connector-target]')];}catch(_){report.push({error:'invalid-target-selector'});continue;}
      if(!source||!targets.length||targets.some(x=>!x)){report.push({error:'missing-connector-endpoint'});continue;}
      const sr=source.getBoundingClientRect(),sc={x:(sr.left+sr.right)/2,y:(sr.top+sr.bottom)/2};
      const m=svg.getScreenCTM();if(!m){report.push({error:'missing-svg-ctm'});continue;}const inv=m.inverse();
      function anchor(e,to){const r=e.getBoundingClientRect(),c={x:(r.left+r.right)/2,y:(r.top+r.bottom)/2},dx=to.x-c.x,dy=to.y-c.y;
        const ellipse=e.dataset.geometry==='circle'||getComputedStyle(e).borderTopLeftRadius.endsWith('%');
        const f=ellipse?1/Math.sqrt((dx/(r.width/2))**2+(dy/(r.height/2))**2):Math.min(Math.abs(dx)>1e-9?r.width/2/Math.abs(dx):Infinity,Math.abs(dy)>1e-9?r.height/2/Math.abs(dy):Infinity);
        return Number.isFinite(f)?{x:c.x+dx*f,y:c.y+dy*f}:c;}
      let lines=[...svg.querySelectorAll('line[data-kriss-connector],line[data-connector-target]')];
      if(!lines.length&&svg.querySelectorAll('line').length===targets.length)lines=[...svg.querySelectorAll('line')];
      while(lines.length<targets.length){const l=document.createElementNS('http://www.w3.org/2000/svg','line');l.dataset.krissConnector='true';svg.appendChild(l);lines.push(l);}
      if(lines.length!==targets.length){report.push({error:'connector-count-mismatch'});continue;}
      targets.forEach((t,i)=>{const tr=t.getBoundingClientRect(),tc={x:(tr.left+tr.right)/2,y:(tr.top+tr.bottom)/2};const a=anchor(source,tc),b=anchor(t,sc);const pa=new DOMPoint(a.x,a.y).matrixTransform(inv),pb=new DOMPoint(b.x,b.y).matrixTransform(inv);
        for(const [k,v]of Object.entries({x1:pa.x,y1:pa.y,x2:pb.x,y2:pb.y}))lines[i].setAttribute(k,String(v));lines[i].dataset.krissConnector='true';
        report.push({source:path(source),target:path(t),start:a,end:b});});
    }window.__KRISS_CONNECTOR_REPORT=report;return report;
  }
  function mirror(root,log) {
    // Explicit paired peers only; do not infer a layout from item count.
    for(const g of all(root,'[data-symmetry="mirror"]')){const r=g.getBoundingClientRect(),pairs=new Map();
      for(const e of g.querySelectorAll('[data-mirror-pair]')){const k=e.dataset.mirrorPair;if(!pairs.has(k))pairs.set(k,[]);pairs.get(k).push(e);}
      for(const peers of pairs.values()){if(peers.length!==2||peers.some(e=>getComputedStyle(e).position!=='absolute'))continue;
        const sorted=peers.sort((a,b)=>a.getBoundingClientRect().left-b.getBoundingClientRect().left),[a,b]=sorted,ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect();
        const axis=r.left+r.width/2,dist=(Math.abs((ra.left+ra.right)/2-axis)+Math.abs((rb.left+rb.right)/2-axis))/2,cy=((ra.top+ra.bottom)/2+(rb.top+rb.bottom)/2)/2;
        sorted.forEach((e,i)=>{const q=e.getBoundingClientRect(),targetX=axis+(i?dist:-dist)-q.width/2,targetY=cy-q.height/2;set(e,'left',(e.offsetLeft+targetX-q.left)+'px','explicit-mirror-pair',log);set(e,'top',(e.offsetTop+targetY-q.top)+'px','explicit-mirror-pair',log);});
      }
    }
  }
  function apply(root=document) {if(running)return;running=true;try{
    const scopes=root.matches?.('.slide')?[root]:all(root,'.slide').filter(visible);if(!scopes.length)scopes.push(root);
    const logs=[];
    for(const scope of scopes){all(scope,'*').forEach(reset);
      const comps=all(scope,'[data-density-component],[data-size-policy],[data-fit-box]').filter(visible);comps.forEach(remember);
      comps.filter(e=>policy(e)==='content-fit').forEach(e=>{set(e,'height','auto','explicit-content-fit',logs);set(e,'min-height','0px','explicit-content-fit',logs);set(e,'align-self','start','explicit-content-fit',logs);});
      uniform(scope,logs);comps.slice().reverse().forEach(e=>fit(e,logs));uniform(scope,logs);mirror(scope,logs);updateConnectors(scope);
      comps.forEach(e=>{e.dataset.adaptiveOverflow=String(over(e));e.dataset.adaptiveDone=VERSION;});
    }
    window.__KRISS_ADAPTIVE_LOG=logs;window.__KRISS_ADAPTIVE_READY=true;
  }finally{running=false;}}
  window.applyAdaptiveLayout=apply;window.applyAdaptiveTypography=apply;window.updateSemanticConnectors=updateConnectors;
  window.prepareAdaptiveMetadata=()=>{};window.resetAdaptiveState=(r=document)=>all(r,'*').forEach(reset);
  window.__KRISS_ADAPTIVE_VERSION=VERSION;
  window.__KRISS_ADAPTIVE_CAPABILITIES={version:VERSION,preserveByDefault:true,explicitUniform:true,contentFitOptIn:true,sequentialPressureRelief:true,semanticConnectors:true,explicitMirrorPairs:true,overrideLog:true};
  // All presentation activation paths and export await this same state machine.
  // Observe only slide activation attributes, not every adaptive child mutation.
  let pending=null, observer=null, requested=0, completed=0;
  const frames=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  function finishVisibleAnimations() {
    const errors=[];
    for(const scope of all(document,'.slide').filter(visible)) {
      for(const animation of scope.getAnimations({subtree:true})) {
        const timing=animation.effect?.getComputedTiming();
        if(!timing||!Number.isFinite(timing.endTime)) {
          errors.push({code:'unsupported-infinite-animation',detail:'A static release requires a finite final visual state'});
          continue;
        }
        try { animation.finish(); } catch(error) {errors.push({code:'animation-finish-failed',detail:String(error)});}
      }
    }
    return errors;
  }
  async function settleVisible() {
    await document.fonts.ready;
    const resources=[];
    await Promise.all([...document.images].map(async image=>{
      try { await image.decode(); }
      catch(error) { if(image.currentSrc||image.getAttribute('src')) resources.push({code:'image-decode-failed',src:image.currentSrc||image.getAttribute('src'),detail:String(error)}); }
      if((image.currentSrc||image.getAttribute('src'))&&(!image.naturalWidth||!image.naturalHeight))
        resources.push({code:'image-empty-natural-size',src:image.currentSrc||image.getAttribute('src')});
    }));
    await frames();
    resources.push(...finishVisibleAnimations());
    await frames();
    apply();
    resources.push(...finishVisibleAnimations());
    window.__KRISS_RESOURCE_REPORT=resources;
    await frames();
    window.__KRISS_LAYOUT_EPOCH=(window.__KRISS_LAYOUT_EPOCH||0)+1;
    return {epoch:window.__KRISS_LAYOUT_EPOCH,resources};
  }
  function schedule() {
    requested++;
    if(!pending) {
      pending=(async()=>{
        let result;
        while(completed<requested) {
          const target=requested;
          result=await settleVisible();
          completed=target;
        }
        return result;
      })().finally(()=>{pending=null;});
      window.__KRISS_LAYOUT_SETTLED=pending;
    }
    return pending;
  }
  window.krissSettleLayout=schedule;
  window.krissActivateSlide=async index=>{
    const slides=all(document,'.slide');
    if(!Number.isInteger(index)||!slides[index])throw new Error('Invalid slide index '+index);
    // Do not invent display, position, opacity or column widths in the exporter.
    slides.forEach((slide,i)=>slide.classList.toggle('active',i===index));
    window.scrollTo(0,0);
    await schedule();
    const rect=slides[index].getBoundingClientRect();
    if(rect.width<1||rect.height<1)throw new Error('Active slide has no geometry; check authored .active CSS');
    return {width:rect.width,height:rect.height,display:getComputedStyle(slides[index]).display};
  };
  const boot=()=>{
    observer=new MutationObserver(()=>{schedule().catch(error=>{window.__KRISS_LAYOUT_ERROR=String(error);});});
    for(const slide of all(document,'.slide'))observer.observe(slide,{attributes:true,attributeFilter:['class','style']});
    schedule().catch(error=>{window.__KRISS_LAYOUT_ERROR=String(error);});
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
  let timer;
  window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(()=>schedule(),80);});
  document.addEventListener('load',event=>{if(event.target instanceof HTMLImageElement)schedule();},true);
  document.fonts.addEventListener?.('loadingdone',()=>schedule());
})();
