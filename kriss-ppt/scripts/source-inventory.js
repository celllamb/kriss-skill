/* Independent pre-export inventory. Never derive this list from exported objects.
 * Every visible content role must map to a native object or explicitly block.
 */
(index) => {
  const slide=document.querySelectorAll('.slide')[index],sr=slide.getBoundingClientRect();
  const dom=[slide,...slide.querySelectorAll('*')];
  const uid=e=>'s'+String(index+1).padStart(2,'0')+'.e'+String(dom.indexOf(e)).padStart(4,'0');
  const ignore='script,style,.toolbar,.controls,.counter,.progress,.hint,.speaker-notes,[data-speaker-notes],[data-export-ignore="true"]';
  const px=v=>parseFloat(v)||0;
  const rect=r=>({x:r.left-sr.left,y:r.top-sr.top,w:r.width,h:r.height});
  const alpha=value=>value==='transparent'||value==='none'?0:Number((String(value).match(/rgba\([^)]*,\s*([\d.]+)\)/)||[])[1]??1);
  const opacity=e=>{let a=1;for(let n=e;n&&n!==slide.parentElement;n=n.parentElement)a*=Number(getComputedStyle(n).opacity);return a;};
  const visible=e=>{
    if(e.closest(ignore)||e.closest('defs,clipPath,mask,pattern,marker,symbol'))return false;
    for(let n=e;n&&n!==slide.parentElement;n=n.parentElement){const s=getComputedStyle(n);if(s.display==='none'||Number(s.opacity)<=0)return false;}
    const c=getComputedStyle(e),r=e.getBoundingClientRect();
    return c.visibility!=='hidden'&&c.visibility!=='collapse'&&((r.width>0&&r.height>0)||(e.localName==='line'&&(r.width>0||r.height>0)));
  };
  const stack=e=>{const a=[];for(let n=e;n&&n!==slide;n=n.parentElement){const z=getComputedStyle(n).zIndex;if(z!=='auto')a.unshift(parseInt(z)||0);}return a.length?a:[0];};
  const nodes=[],errors=[],svgShapes=[],svgLines=[],resources=[],overflow=[],styles=[];
  // Final computed styles are captured independently of converter selections.
  const styleKeys=['display','position','visibility','opacity','zIndex','transform','transformOrigin',
    'boxSizing','width','height','minWidth','maxWidth','minHeight','maxHeight','overflow','overflowX','overflowY',
    'paddingTop','paddingRight','paddingBottom','paddingLeft','marginTop','marginRight','marginBottom','marginLeft',
    'gap','rowGap','columnGap','alignItems','justifyContent','alignSelf','flexDirection','gridTemplateColumns','gridTemplateRows',
    'fontFamily','fontSize','fontWeight','fontStyle','fontVariantCaps','fontKerning','fontFeatureSettings','fontVariationSettings',
    'lineHeight','letterSpacing','wordSpacing','textAlign','textIndent','textTransform','textDecoration','textShadow','verticalAlign',
    'whiteSpace','wordBreak','overflowWrap','direction','writingMode','color','backgroundColor','backgroundImage',
    'backgroundSize','backgroundPosition','backgroundRepeat','backgroundClip','boxShadow','clipPath','filter','mixBlendMode',
    'borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth','borderTopStyle','borderRightStyle','borderBottomStyle','borderLeftStyle',
    'borderTopColor','borderRightColor','borderBottomColor','borderLeftColor',
    'borderTopLeftRadius','borderTopRightRadius','borderBottomRightRadius','borderBottomLeftRadius',
    'content','listStyleType','listStylePosition','objectFit','objectPosition','fill','stroke','strokeWidth','strokeLinecap','strokeDasharray'];
  const recordStyle=(id,c)=>styles.push({id,computed:Object.fromEntries(styleKeys.map(k=>[k,c[k]||'']))});
  function add(e,role,extra={}){const row={id:uid(e),role,tag:e.localName,rect:rect(e.getBoundingClientRect()),...extra};nodes.push(row);return row;}
  function error(e,code,detail){errors.push({id:uid(e),code,detail});}
  const hasPaint=c=>alpha(c.backgroundColor)>0||c.backgroundImage!=='none'||c.boxShadow!=='none'||['Top','Right','Bottom','Left'].some(side=>px(c['border'+side+'Width'])>0&&!['none','hidden'].includes(c['border'+side+'Style'])&&alpha(c['border'+side+'Color'])>0);
  for(const e of dom){
    if(!visible(e))continue;
    const c=getComputedStyle(e),r=e.getBoundingClientRect();
    recordStyle(uid(e),c);
    // Links are semantic content even when their pixels match ordinary text.
    // Capture them before exporter filtering, independently of text extraction.
    if(e.localName==='a'&&e.hasAttribute('href')){
      const raw=e.getAttribute('href')||'',href=typeof e.href==='string'?e.href:'';
      const supported=/^(https?:|mailto:|tel:)/i.test(raw.trim()) && !e.hasAttribute('download');
      const textOnly=Boolean(e.textContent.trim())&&!e.querySelector('img,svg,video,canvas');
      add(e,'hyperlink',{href,rawHref:raw,text:e.innerText||''});
      if(!supported)error(e,'unsupported-hyperlink-target',raw);
      if(!textOnly)error(e,'unsupported-nontext-hyperlink','Only text hyperlinks have an implemented native mapping');
      const generatedLink=[e,...e.querySelectorAll('*')].some(n=>['::before','::after'].some(p=>{
        const pc=getComputedStyle(n,p);return pc.display!=='none'&&!['none','normal','""'].includes(pc.content);
      }));
      if(generatedLink)error(e,'unsupported-generated-hyperlink-content','Pseudo-element link text needs an independent native hyperlink mapping');
    }
    if(e.dataset.adaptiveOverflow==='true'){
      const decorative=e.dataset.overflowRole==='decoration'&&!e.textContent.trim()&&Boolean(e.dataset.overflowReason?.trim());
      overflow.push({id:uid(e),rect:rect(r),role:e.dataset.overflowRole||'content',reason:e.dataset.overflowReason||'',allowed:decorative});
    }
    for(const [property,code]of [['clipPath','unsupported-css-clip-path'],['filter','unsupported-css-filter'],['backdropFilter','unsupported-backdrop-filter'],['maskImage','unsupported-css-mask'],['borderImageSource','unsupported-border-image']]){
      if(c[property]&&c[property]!=='none'&&!(property==='clipPath'&&c.clipPath.startsWith('polygon(')))error(e,code,c[property]);
    }
    if(c.mixBlendMode&&c.mixBlendMode!=='normal')error(e,'unsupported-blend-mode',c.mixBlendMode);
    if(e.shadowRoot||e.localName.includes('-'))error(e,'unsupported-shadow-or-custom-element',e.localName);
    const radii=['borderTopLeftRadius','borderTopRightRadius','borderBottomRightRadius','borderBottomLeftRadius'].map(k=>c[k]);
    if(c.outlineStyle!=='none'&&px(c.outlineWidth)>0)error(e,'unsupported-css-outline',c.outline);
    if(c.textShadow&&c.textShadow!=='none')error(e,'unsupported-text-shadow',c.textShadow);
    if(!['none','uppercase','lowercase'].includes(c.textTransform))error(e,'unsupported-text-transform',c.textTransform);
    if(c.writingMode!=='horizontal-tb')error(e,'unsupported-writing-mode',c.writingMode);
    if(c.direction==='rtl')error(e,'unsupported-rtl-text',c.direction);
    if(px(c.wordSpacing)!==0)error(e,'unsupported-word-spacing',c.wordSpacing);
    if(c.fontVariantCaps&&c.fontVariantCaps!=='normal')error(e,'unsupported-font-variant-caps',c.fontVariantCaps);
    if(c.textDecorationLine.includes('line-through')||c.textDecorationLine.includes('overline'))error(e,'unsupported-text-decoration',c.textDecorationLine);
    if(c.textDecorationLine.includes('underline')&&c.textDecorationStyle!=='solid')error(e,'unsupported-underline-style',c.textDecorationStyle);
    for(const key of ['color','backgroundColor','borderTopColor','borderRightColor','borderBottomColor','borderLeftColor']){
      if(c[key]&&!/^(?:rgba?\(|#[a-f\d]{3,8}$|transparent$|none$)/i.test(c[key]))error(e,'unsupported-color-space',{property:key,value:c[key]});
    }
    if(c.boxShadow!=='none'){
      const simple=/^(rgba?\([^)]*\))\s+(-?[\d.]+)px\s+(-?[\d.]+)px\s+([\d.]+)px(?:\s+(-?[\d.]+)px)?$/;
      const sh=c.boxShadow.match(simple);
      const flat=/^(?:inset\s+)?rgba?\([^)]*\)\s+0px\s+0px\s+0px\s+[\d.]+px(?:\s+inset)?$/.test(c.boxShadow);
      if((!sh||Number(sh[5]||0)!==0)&&!flat)error(e,'unsupported-shadow-syntax',c.boxShadow);
    }

    if(c.transform!=='none'){
      const m=new DOMMatrix(c.transform);
      const capturedBySvgCTM=e.namespaceURI==='http://www.w3.org/2000/svg'&&m.is2D&&m.a>0&&m.d>0&&Math.abs(m.b)<1e-6&&Math.abs(m.c)<1e-6;
      if(!capturedBySvgCTM&&(!m.is2D||Math.abs(m.a-1)>1e-6||Math.abs(m.d-1)>1e-6||Math.abs(m.b)>1e-6||Math.abs(m.c)>1e-6))
        error(e,'unsupported-css-transform',c.transform);
    }
    if(e.namespaceURI==='http://www.w3.org/2000/svg'){
      const tag=e.localName;
      if(['svg','g','a','title','desc'].includes(tag))continue;
      if(!['line','circle','ellipse','rect'].includes(tag)){add(e,'unsupported-svg');error(e,'unsupported-svg-primitive',tag);continue;}
      if(tag==='line'&&(c.stroke==='none'||px(c.strokeWidth)===0||Number(c.strokeOpacity)===0))continue;
      if((c.fill==='none'||alpha(c.fill)*Number(c.fillOpacity)===0)&&(c.stroke==='none'||px(c.strokeWidth)===0||Number(c.strokeOpacity)===0))continue;
      add(e,'svg-primitive');
      const m=e.getScreenCTM();
      if(!m||Math.abs(m.b)>1e-6||Math.abs(m.c)>1e-6||m.a<=0||m.d<=0){error(e,'unsupported-svg-transform',m?.toString());continue;}
      if(/url\(/.test(c.fill+' '+c.stroke)||['markerStart','markerMid','markerEnd'].some(k=>c[k]&&c[k]!=='none')){error(e,'unsupported-svg-paint-server','SVG gradients/patterns/markers require native support');continue;}
      const nonScaling=c.vectorEffect==='non-scaling-stroke';
      const axisLine=tag==='line'&&(Math.abs(e.x2.baseVal.value-e.x1.baseVal.value)<1e-9||Math.abs(e.y2.baseVal.value-e.y1.baseVal.value)<1e-9)&&c.strokeLinecap==='butt';
      const affineLine=tag==='line'&&c.strokeLinecap==='butt';
      if(c.stroke!=='none'&&Math.abs(m.a-m.d)>1e-6&&!nonScaling&&!axisLine&&!affineLine){error(e,'unsupported-svg-nonuniform-stroke',m.toString());continue;}
      if(c.strokeDasharray!=='none'){error(e,'unsupported-svg-dasharray',c.strokeDasharray);continue;}
      const base={id:uid(e),order:dom.indexOf(e),stackPath:stack(e),opacity:opacity(e),
        fill:c.fill,fillOpacity:Number(c.fillOpacity),stroke:c.stroke,strokeOpacity:Number(c.strokeOpacity),
        strokeWidth:px(c.strokeWidth)*(nonScaling?1:(axisLine&&Math.abs(e.y2.baseVal.value-e.y1.baseVal.value)<1e-9?m.d:m.a)),linecap:c.strokeLinecap};
      if(tag==='line'){
        const a=new DOMPoint(e.x1.baseVal.value,e.y1.baseVal.value).matrixTransform(m),b=new DOMPoint(e.x2.baseVal.value,e.y2.baseVal.value).matrixTransform(m);
        let strokePolygon=null;
        if(affineLine&&!axisLine&&!nonScaling&&Math.abs(m.a-m.d)>1e-6){
          const ax=e.x1.baseVal.value,ay=e.y1.baseVal.value,bx=e.x2.baseVal.value,by=e.y2.baseVal.value;
          const length=Math.hypot(bx-ax,by-ay),half=px(c.strokeWidth)/2;
          const nx=-(by-ay)/length*half,ny=(bx-ax)/length*half;
          strokePolygon=[[ax+nx,ay+ny],[bx+nx,by+ny],[bx-nx,by-ny],[ax-nx,ay-ny]].map(([x,y])=>{const p=new DOMPoint(x,y).matrixTransform(m);return [p.x-sr.left,p.y-sr.top];});
        }
        svgLines.push({...base,kind:'svgline',strokePolygon,x1:a.x-sr.left,y1:a.y-sr.top,x2:b.x-sr.left,y2:b.y-sr.top});
      }else{
        let rx=0,ry=0;
        if(tag==='rect'){rx=e.rx.baseVal.value*m.a;ry=e.ry.baseVal.value*m.d;}
        if(tag==='rect'&&Math.abs(rx-ry)>1e-5){error(e,'unsupported-svg-elliptical-rect-corner',{rx,ry});continue;}
        svgShapes.push({...base,kind:'svgshape',tag,rect:rect(r),radius:rx});
      }
      continue;
    }
    if(['canvas','video','audio','iframe','object','embed','input','select','textarea','math'].includes(e.localName)){
      add(e,'unsupported-replaced-element');error(e,'unsupported-replaced-element',e.localName);
    }
    const direct=[...e.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim()).map(n=>n.textContent).join('');
    if(direct){const ancestors=[];for(let n=e;n&&n!==slide.parentElement;n=n.parentElement)ancestors.push(uid(n));add(e,'text',{text:direct,ancestors});}
    if(e===slide){add(e,'static-background');}
    else if(hasPaint(c)&&(alpha(c.backgroundColor)>0||c.boxShadow!=='none'||(c.backgroundImage!=='none'&&!c.backgroundImage.startsWith('url('))||['Top','Right','Bottom','Left'].some(side=>px(c['border'+side+'Width'])>0&&!['none','hidden'].includes(c['border'+side+'Style'])))){add(e,'paint');}
    if(e.localName==='img'){
      if(['paddingTop','paddingRight','paddingBottom','paddingLeft','borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth'].some(k=>px(c[k])>0))error(e,'unsupported-image-border-padding','Use an independently authored wrapper until image content-box support is implemented');
      if(radii.some(v=>px(v)>0))error(e,'unsupported-rounded-image-clipping',radii);

      add(e,'image');resources.push({id:uid(e),src:e.currentSrc||e.src,width:e.naturalWidth,height:e.naturalHeight,complete:e.complete});
      if(!e.complete||!e.naturalWidth||!e.naturalHeight)error(e,'image-not-loaded',e.currentSrc||e.src);
      if(c.objectFit!=='fill'){
        const innerW=r.width-px(c.paddingLeft)-px(c.paddingRight)-px(c.borderLeftWidth)-px(c.borderRightWidth);
        const innerH=r.height-px(c.paddingTop)-px(c.paddingBottom)-px(c.borderTopWidth)-px(c.borderBottomWidth);
        if(Math.abs(innerW/Math.max(1,innerH)-e.naturalWidth/Math.max(1,e.naturalHeight))>.002)
          error(e,'unsupported-image-object-fit',c.objectFit);
      }
      if(opacity(e)<.99999)error(e,'unsupported-image-opacity',opacity(e));
    }
    if(e!==slide&&c.backgroundImage.startsWith('url(')){
      add(e,'background-image');
      if(radii.some(v=>px(v)>0)||['borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth'].some(k=>px(c[k])>0))error(e,'unsupported-background-image-clipping','Native background images currently require an unbordered rectangular content region');
      if(c.backgroundPosition!=='0% 0%'&&c.backgroundPosition!=='50% 50%')error(e,'unsupported-background-image-position',c.backgroundPosition);

      if(c.backgroundSize!=='100% 100%')error(e,'unsupported-background-image-sizing',c.backgroundSize);
    }
    if(c.display==='list-item'&&(c.listStyleType!=='none'||c.listStyleImage!=='none')){recordStyle(uid(e)+'.marker',getComputedStyle(e,'::marker'));nodes.push({id:uid(e)+'.marker',role:'list-marker',tag:'::marker',owner:uid(e),rect:rect(r)});if(c.listStyleImage!=='none')error(e,'unsupported-list-marker-image',c.listStyleImage);}
    for(const pseudo of ['before','after']){
      const pc=getComputedStyle(e,'::'+pseudo),raw=pc.content;
      if(!raw||['none','normal'].includes(raw)||pc.display==='none'||pc.visibility==='hidden'||Number(pc.opacity)===0)continue;
      if(raw==='""'&&!hasPaint(pc))continue;
      recordStyle(uid(e)+'.'+pseudo,pc);
      nodes.push({id:uid(e)+'.'+pseudo,role:'generated',tag:'::'+pseudo,owner:uid(e),rect:rect(r),content:raw});
    }
  }
  const speakerNotes={schema:'kriss-speaker-notes-v1',attributePresent:slide.hasAttribute('data-notes'),text:slide.getAttribute('data-notes')};
  return {schema:'kriss-source-inventory-v1',speakerNotes,nodes,errors,svgShapes,svgLines,resources,overflow,styles};
}
