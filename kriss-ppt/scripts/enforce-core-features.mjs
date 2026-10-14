#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
const input=path.resolve(process.argv[2]||'presentation.html');
if(!fs.existsSync(input)){console.error(`Input not found: ${input}`);process.exit(2)}
let html=fs.readFileSync(input,'utf8');
if(!/window\.open\(/.test(html)){
  const js=`<script id="kriss-core-features-enforced">\n(function(){\nlet notesWin=null;\nfunction activeSlide(){return document.querySelector('.slide.active')||document.querySelector('.slide')}\nfunction esc(s){return String(s||'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]))}\nwindow.toggleNotes=function(){const s=activeSlide();if(!s)return;if(notesWin&&!notesWin.closed){notesWin.close();notesWin=null;return}notesWin=window.open('','KRISSNotes','width=520,height=460');if(!notesWin)return;const tag=s.querySelector('.pattern-tag')?.innerText||'';const note=s.dataset.notes||'';notesWin.document.open();notesWin.document.write('<!doctype html><html><meta charset=utf-8><title>KRISS Notes</title><style>body{font-family:system-ui,sans-serif;background:#f4f6f5;margin:0;padding:22px;color:#27312f}.card{background:#fff;border:1px solid #d6dddb;border-radius:14px;padding:18px 20px}.e{font:700 12px monospace;color:#f47b20}.t{font-weight:800;font-size:22px;margin:8px 0}.p{font-size:16px;line-height:1.55;color:#596563}</style><div class=card><div class=e>CURRENT</div><div class=t>'+esc(tag)+'</div><div class=p>'+esc(note)+'</div></div></html>');notesWin.document.close()};\nwindow.toggleFullscreen=window.toggleFullscreen||function(){if(document.fullscreenElement){document.exitFullscreen?.()}else{document.documentElement.requestFullscreen?.()}};\ndocument.addEventListener('keydown',e=>{if(e.key==='s'||e.key==='S')window.toggleNotes();if(e.key==='f'||e.key==='F')window.toggleFullscreen()});\n})();\n</script>`;
  html=html.replace(/<\/body>/i,js+'\n</body>');
  fs.writeFileSync(input,html);
  console.log(`Core feature fallback injected: ${input}`);
}else console.log(`Core feature popup already present: ${input}`);
