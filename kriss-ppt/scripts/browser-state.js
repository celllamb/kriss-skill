/* Export delegates to the same public activation contract as presentation mode. */
async (index) => {
  if(typeof window.krissActivateSlide!=='function')throw new Error('Shared activation runtime is missing');
  let timer;
  try {
    const state=await Promise.race([
      window.krissActivateSlide(index),
      new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('Slide activation did not settle within 30 seconds')),30000);})
    ]);
    if(window.__KRISS_LAYOUT_ERROR)throw new Error(window.__KRISS_LAYOUT_ERROR);
    const temporal=(window.__KRISS_RESOURCE_REPORT||[]).filter(r=>r.code==='unsupported-infinite-animation'||r.code==='animation-finish-failed');
    if(temporal.length)throw new Error('No finite source state: '+JSON.stringify(temporal));
    return state;
  } finally {clearTimeout(timer);}
}
