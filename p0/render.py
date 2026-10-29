# -*- coding: utf-8 -*-
"""render.py — Talent Object JSON -> self-contained HTML page (P0 views).

v4 "terminal" paradigm — designed for the AI community's native taste:
GitHub-dark palette, monospace-first type, README section headers,
career rendered as a git log, hero as a neofetch card, evidence as
stats output. No fake hashes (dates are the identifiers — honesty first).

Views: V1 career (git log), V3 dual stack, V4 evidence (stats).
All claims carry the honest P0 watermark: ○ self-reported, watermark V1.
Motion: jump-proof scroll reveal, typing tagline, reduced-motion + print.
"""
from __future__ import annotations
import json

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>✦dossier — __NAME__</title>
<style>
  :root{
    --bg:#0d1117; --panel:#161b22; --line:#30363d; --fg:#c9d1d9; --dim:#8b949e;
    --green:#3fb950; --cyan:#58a6ff; --amber:#d29922; --red:#f85149;
    --mono:ui-monospace,"JetBrains Mono","Cascadia Code",Consolas,"Noto Sans SC","Microsoft YaHei",monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  ::selection{background:#1f6feb55;}
  body{
    background:var(--bg) radial-gradient(circle,#161b2288 1px,transparent 1px);
    background-size:26px 26px;
    color:var(--fg); font-family:var(--mono); font-size:15px; line-height:1.8;
  }
  main{max-width:880px;margin:0 auto;padding:48px 28px 40px;}
  .dim{color:var(--dim);} .green{color:var(--green);} .cyan{color:var(--cyan);} .amber{color:var(--amber);}

  /* terminal window */
  .term{border:1px solid var(--line);border-radius:8px;background:var(--panel);overflow:hidden;box-shadow:0 8px 30px #0008;}
  .term-bar{display:flex;align-items:center;gap:8px;padding:10px 14px;border-bottom:1px solid var(--line);background:#010409;}
  .term-bar i{width:12px;height:12px;border-radius:50%;display:inline-block;}
  .term-bar .r{background:#ff5f57;} .term-bar .y{background:#febc2e;} .term-bar .g{background:#28c840;}
  .term-bar .title{margin-left:10px;color:var(--dim);font-size:13px;}
  .term-body{padding:22px 24px 26px;}
  .pline{margin-bottom:14px;}
  .prompt{color:var(--green);} .path{color:var(--cyan);}
  h1{font-size:30px;font-weight:600;color:#f0f6fc;letter-spacing:.02em;margin:2px 0 4px;}
  h1 .en{color:var(--dim);font-weight:400;font-size:20px;}
  .tagline{color:var(--fg);min-height:1.8em;}
  .cursor{display:inline-block;width:9px;height:1.1em;background:var(--green);vertical-align:text-bottom;animation:blink 1s steps(1) infinite;}
  @keyframes blink{50%{opacity:0;}}
  .badges{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 4px;}
  .badge{border:1px solid var(--line);border-radius:4px;font-size:12.5px;overflow:hidden;display:flex;}
  .badge b{background:#21262d;color:var(--dim);padding:2px 8px;font-weight:400;}
  .badge span{padding:2px 10px;}
  .badge .v-g{background:#1b3a25;color:var(--green);} .badge .v-c{background:#12283f;color:var(--cyan);} .badge .v-a{background:#3a2d10;color:var(--amber);}
  .wm{margin-top:14px;color:var(--amber);font-size:13px;}

  /* README-style sections */
  section{margin-top:56px;}
  h2{font-size:19px;font-weight:600;color:#f0f6fc;border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:22px;}
  h2 .hash{color:var(--cyan);margin-right:8px;} h2 .cm{color:var(--dim);font-size:13.5px;font-weight:400;margin-left:12px;}

  /* git log career */
  .commit{display:grid;grid-template-columns:22px 1fr;gap:4px 10px;padding:4px 0 26px;}
  .commit .rail{color:var(--green);text-align:center;}
  .commit .rail::after{content:"│";display:block;color:var(--line);margin-top:2px;}
  .commit:last-child .rail::after{content:"";}
  .chead{color:#f0f6fc;}
  .chead .date{color:var(--cyan);}
  .chead .ref{color:var(--green);border:1px solid #1b3a25;border-radius:10px;padding:0 8px;font-size:12px;margin-left:8px;}
  .cdesc{color:var(--dim);}
  .cdesc li{list-style:none;padding-left:18px;position:relative;}
  .cdesc li::before{content:"-";position:absolute;left:4px;color:var(--dim);}
  .chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
  .chip{border:1px solid var(--line);background:var(--panel);border-radius:4px;padding:1px 10px;font-size:13px;}
  .chip::before{content:"→ ";color:var(--green);}
  .empty{border:1px dashed var(--line);border-radius:6px;padding:20px;color:var(--dim);}
  .empty::before{content:"// ";}

  /* stack */
  .cols{display:grid;grid-template-columns:1fr 1fr;gap:36px;}
  .cols h3{font-size:14px;font-weight:400;color:var(--dim);margin-bottom:12px;}
  .cols h3 b{color:var(--cyan);font-weight:400;}

  /* evidence stats */
  .stats{border:1px solid var(--line);border-radius:8px;background:var(--panel);padding:8px 18px;}
  .stat{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-bottom:1px dashed #21262d;font-size:14.5px;}
  .stat:last-child{border-bottom:none;}
  .stat .num{color:#f0f6fc;}
  .stat .num::before{content:"+ ";color:var(--green);}
  .stat .src{color:var(--dim);font-size:12.5px;text-align:right;}
  .stat .mk{color:var(--dim);}

  footer{margin-top:64px;border-top:1px solid var(--line);padding-top:18px;color:var(--dim);font-size:12.5px;line-height:2.1;overflow-wrap:anywhere;}

  /* workflows (V2) */
  .wfl{margin-bottom:34px;}
  .wfl-title{color:#f0f6fc;margin-bottom:10px;}
  .wfl-title .org{color:var(--dim);font-size:13px;}
  .wfl svg{display:block;}
  .wfl .nbox{fill:#161b22;stroke:#30363d;rx:6;}
  .wfl .nbox.confirmed{stroke:#3fb950;}
  .wfl text{font-family:var(--mono);}
  .wfl .nt{fill:#f0f6fc;font-size:13px;} .wfl .ns{fill:#8b949e;font-size:11px;}
  .wfl .edge{stroke:#3fb950;stroke-width:1.5;fill:none;}
  .wfl .edge.inf{stroke:#8b949e;stroke-dasharray:5 4;cursor:pointer;}
  .wfl .edge.inf:hover{stroke:#d29922;}
  .wfl .elabel{fill:#8b949e;font-size:10.5px;cursor:pointer;}
  .wfl .legend{color:var(--dim);font-size:12.5px;margin:6px 0 8px;}
  .btn{margin:18px 0 0;display:inline-block;border:1px solid #1b3a25;border-radius:6px;background:#0d1117;color:var(--green);padding:8px 18px;cursor:pointer;font-family:var(--mono);font-size:13.5px;}
  .btn:hover{background:#1b3a25;}
  footer::before{content:"// ";}

  /* motion (jump-proof: fold-line reveal) */
  .reveal{opacity:0;transform:translateY(14px);transition:opacity .5s ease,transform .5s ease;}
  .reveal.in{opacity:1;transform:none;}
  @media (prefers-reduced-motion: reduce){
    .reveal{opacity:1;transform:none;transition:none;}
    .cursor{animation:none;}
    html{scroll-behavior:auto;}
  }
  @media print{ .reveal{opacity:1!important;transform:none!important;} body{background:#fff;color:#111;} }
  @media (max-width:640px){ main{padding:32px 16px;} .cols{grid-template-columns:1fr;} h1{font-size:24px;} .stat{flex-direction:column;gap:2px;} }
</style>
</head>
<body>
<main>
  <div class="term reveal">
    <div class="term-bar"><i class="r"></i><i class="y"></i><i class="g"></i><span class="title">__USER__@tstar — ~/dossier</span></div>
    <div class="term-body">
      <div class="pline"><span class="prompt">__USER__@tstar</span>:<span class="path">~</span>$ whoami<span class="cursor"></span></div>
      <h1 id="name"></h1>
      <div class="tagline" id="tagline"></div>
      <div class="badges" id="badges"></div>
      <div class="wm">[ ○ all self-reported · watermark V1 · generated by ✦dossier P0 ]</div>
    </div>
  </div>

  <section class="reveal">
    <h2><span class="hash">##</span>career<span class="cm">git log --career --reverse</span></h2>
    <div id="traj"></div>
  </section>

  <section class="reveal">
    <h2><span class="hash">##</span>stack<span class="cm">dual-stack · silicon × carbon</span></h2>
    <div class="cols">
      <div><h3><b>silicon</b> · AI / 数据栈</h3><div class="chips" id="silicon"></div></div>
      <div><h3><b>carbon</b> · 医药领域栈</h3><div class="chips" id="carbon"></div></div>
    </div>
  </section>

  <section class="reveal">
    <h2><span class="hash">##</span>evidence<span class="cm">cat claims.json | grep -v unverified</span></h2>
    <div class="stats" id="stats"></div>
  </section>

  <section class="reveal" id="wsec">
    <h2><span class="hash">##</span>workflows<span class="cm">five-tuple extraction · 实线=原文明示 · 虚线=AI推断(点击确认)</span></h2>
    <div id="wfl"></div>
    <button class="btn" id="exportBtn" style="display:none">↓ export confirmed talent-object.json</button>
  </section>

  <footer id="foot"></footer>
</main>
<script>
const T = window.TALENT_OBJECT;
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function year(v){ if(v==null) return null; const m=String(v).match(/(19|20)\d{2}/); return m?parseInt(m[0]):null; }

// ---- hero ----
const nameEl=document.getElementById('name');
const nm=(T.identity&&T.identity.display_name)||'unknown';
const m=nm.match(/^([一-龥·]+)\s*(.*)$/);
nameEl.innerHTML=m?`${esc(m[1])} <span class="en">${esc(m[2])}</span>`:esc(nm);

// typing tagline (instant under reduced motion)
const tag=(T.meta&&T.meta.tagline)||'';
const tagEl=document.getElementById('tagline');
if(matchMedia('(prefers-reduced-motion: reduce)').matches){ tagEl.textContent=tag; }
else{ let i=0; tagEl.dataset.full=tag; (function t(){ tagEl.textContent=tag.slice(0,i++); if(i<=tag.length) setTimeout(t,34); })(); }

// badges derived from data only
const evs=(T.career_events||[]);
const nums=evs.flatMap(e=>e.evidence_numbers||[]);
document.getElementById('badges').innerHTML=[
  ['identity','human','v-g'],['watermark','V1','v-a'],
  ['events',evs.length,'v-c'],['claims',nums.length,'v-c'],
].map(([k,v,c])=>`<span class="badge"><b>${k}</b><span class="${c}">${esc(String(v))}</span></span>`).join('');

// ---- career as git log ----
function buildLog(){
  const host=document.getElementById('traj');
  if(!evs.length){ host.innerHTML='<div class="empty">no structured events — 访谈补全后此处生成 git log</div>'; return; }
  const ys=evs.flatMap(e=>[year(e.start),year(e.end)]).filter(v=>v!=null);
  if(!ys.length){ host.innerHTML='<div class="empty">no datable events — 简历信息量不足，需访谈补充</div>'; return; }
  const now=2026;
  const ordered=[...evs].sort((a,b)=>(year(b.start)??0)-(year(a.start)??0)); // newest first, like git log
  host.innerHTML=ordered.map((e,i)=>{
    const y0=year(e.start), y1=year(e.end)??now;
    const range=(y0===y1)?`${e.start?esc(String(e.start)):'?'}—now`.replace('—now',(e.end?`—${esc(String(e.end))}`:'—now')):`${esc(String(e.start??'?'))}—${e.end?esc(String(e.end)):'now'}`;
    const dur=Math.max(1,y1-y0);
    const head=(i===0)?'<span class="ref">HEAD → main</span>':'';
    const highs=(e.highlights||[]).slice(0,3).map(x=>`<li>${esc(String(x))}</li>`).join('');
    const chips=(e.evidence_numbers||[]).slice(0,5).map(n=>`<span class="chip">${esc(String(n))}</span>`).join('');
    return `<div class="commit reveal">
      <div class="rail">*</div>
      <div>
        <div class="chead"><span class="date">${range}</span> · ${esc(String(e.role||''))} @ ${esc(String(e.org||''))} ${head} <span class="dim">(~${dur}y)</span></div>
        <ul class="cdesc">${highs}</ul>
        ${chips?`<div class="chips">${chips}</div>`:''}
      </div>
    </div>`;
  }).join('');
}

// ---- stack ----
function chips(id,arr){ document.getElementById(id).innerHTML=(arr||[]).map(x=>`<span class="chip">${esc(String(x))}</span>`).join('')||'<span class="dim">// none</span>'; }

// ---- evidence stats ----
function stats(){
  let out='';
  evs.forEach(e=>{ (e.evidence_numbers||[]).forEach(n=>{
    out+=`<div class="stat"><span class="num">${esc(String(n))}</span><span class="src">${esc(String(e.org||'')).slice(0,26)} · ${esc(String(e.start||''))} <span class="mk">[○]</span></span></div>`;
  });});
  document.getElementById('stats').innerHTML=out||'<div class="empty">no quantified evidence — 建议访谈补数</div>';
}

buildLog(); chips('silicon',(T.skills||{}).silicon); chips('carbon',(T.skills||{}).carbon); stats();

// ---- workflows (V2): read-only flow projection + minimal confirm loop ----
const WEDGES_CONFIRMED={};   // key "e<ei>:<from>-><to>" -> true (user confirmed)
function buildWorkflows(){
  const host=document.getElementById('wfl');
  const sec=document.getElementById('wsec');
  const wfs=T.workflows||[];
  const usable=wfs.filter(w=>w.nodes&&w.nodes.length);
  if(!usable.length){ host.innerHTML='<div class="empty">// no workflows extracted'+(wfs.length&&wfs[0].notes&&wfs[0].notes[0]?' — '+esc(String(wfs[0].notes[0]).slice(0,90)):'')+'</div>'; sec.style.display=(wfs.length?'':'none'); return; }
  let html='';
  usable.forEach(w=>{
    const ev=(T.career_events||[])[w.event_index]||{};
    const nInf=w.edges.filter(e=>e.inferred).length;
    html+=`<div class="wfl"><div class="wfl-title">▸ ${esc(String(ev.role||''))} @ ${esc(String(ev.org||''))} <span class="org">// ${w.nodes.length} steps · ${nInf} inferred</span></div>`;
    html+=`<svg data-ei="${w.event_index}" width="820" height="${0}" xmlns="http://www.w3.org/2000/svg"></svg></div>`;
  });
  host.innerHTML=html;
  host.querySelectorAll('svg[data-ei]').forEach(svg=>{
    const w=wfs.find(x=>x.event_index===+svg.dataset.ei);
    drawFlow(svg,w);
  });
  // export confirmed json
  const btn=document.getElementById('exportBtn');
  btn.style.display='inline-block';
  btn.onclick=()=>{
    const out=JSON.parse(JSON.stringify(T));
    (out.workflows||[]).forEach(w=>{ (w.edges||[]).forEach(e=>{
      if(WEDGES_CONFIRMED[`e${w.event_index}:${e.from}->${e.to}`]) e.inferred=false; });});
    delete out._generated_at;
    const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});
    const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
    a.download='talent-object.confirmed.json'; a.click();
  };
}
function drawFlow(svg,w){
  const NW=176,NH=62,GX=54,GY=26,PAD=18;
  svg.innerHTML='';   // full redraw (no duplicate elements on confirm)
  // layering: longest path from edges (cycle-safe)
  const id2n={}; w.nodes.forEach(n=>id2n[n.id]=n);
  const layer={}; w.nodes.forEach(n=>layer[n.id]=0);
  for(let it=0;it<w.nodes.length;it++){ let ch=false;
    w.edges.forEach(e=>{ if(layer[e.to]<layer[e.from]+1){ layer[e.to]=layer[e.from]+1; ch=true; } });
    if(!ch)break; }
  const cols={}; w.nodes.forEach(n=>{ (cols[layer[n.id]]=cols[layer[n.id]]||[]).push(n); });
  const keys=Object.keys(cols).map(Number).sort((a,b)=>a-b);
  let H=0;
  keys.forEach(k=>{ H=Math.max(H,PAD+cols[k].length*(NH+GY)); });
  const W=PAD*2+keys.length*(NW+GX)-GX;
  svg.setAttribute('width',Math.max(W,300)); svg.setAttribute('height',H);
  const pos={};
  keys.forEach(k=>{ cols[k].forEach((n,j)=>{ pos[n.id]={x:PAD+k*(NW+GX),y:PAD+j*(NH+GY)}; }); });
  const NS='http://www.w3.org/2000/svg';
  const mk=(t,at,parent)=>{const el=document.createElementNS(NS,t);for(const a in at)el.setAttribute(a,at[a]);(parent||svg).appendChild(el);return el;};
  const defs=mk('defs',{}); defs.innerHTML='<marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#8b949e"/></marker>';
  // nodes first (below)
  w.nodes.forEach(n=>{
    const p=pos[n.id];
    const g=mk('g',{});
    g.innerHTML=`<rect class="nbox" x="${p.x}" y="${p.y}" width="${NW}" height="${NH}" rx="6"/>
      <text class="nt" x="${p.x+10}" y="${p.y+22}">${esc(String(n.verb||'').slice(0,10))} ${esc(String(n.object||'').slice(0,8))}</text>
      <text class="ns" x="${p.x+10}" y="${p.y+40}">${esc([n.tool?'🛠'+String(n.tool).slice(0,10):'',n.collaborator?'👥'+String(n.collaborator).slice(0,8):''].filter(Boolean).join(' '))||'—'}</text>
      <text class="ns" x="${p.x+10}" y="${p.y+55}">→ ${esc(String(n.output||'').slice(0,16))}</text>`;
  });
  // edges: adjacent layers -> bezier in the gap; skipping layers -> corridor polyline (never crosses a box)
  const labels=[];
  w.edges.forEach(e=>{
    const a=pos[e.from],b=pos[e.to]; if(!a||!b)return;
    const key=`e${w.event_index}:${e.from}->${e.to}`;
    const inf=e.inferred&&!WEDGES_CONFIRMED[key];
    const cls='edge'+(inf?' inf':'');
    const dl=layer[e.to]-layer[e.from];
    let d,lx,ly;
    const x1=a.x+NW,y1=a.y+NH/2,x2=b.x,y2=b.y+NH/2;
    if(dl<=1){ d=`M${x1},${y1} C${x1+24},${y1} ${x2-24},${y2} ${x2-2},${y2}`; lx=(x1+x2)/2; ly=(y1+y2)/2-7; }
    else{ const mx=a.x+NW+GX/2; d=`M${x1},${y1} L${mx},${y1} L${mx},${y2} L${x2-2},${y2}`; lx=mx+0; ly=(y1+y2)/2; }
    mk('path',{class:cls,d,'marker-end':'url(#arw)'});
    if(e.inferred) labels.push({key,lx,ly,confirmed:!!WEDGES_CONFIRMED[key]});
  });
  // labels last (on top, clickable)
  labels.forEach(o=>{
    const t=mk('text',{class:'elabel',x:o.lx,y:o.ly,'text-anchor':'middle'});
    t.textContent=o.confirmed?'已确认':'推断'; t.dataset.key=o.key;
    t.addEventListener('click',()=>{ WEDGES_CONFIRMED[o.key]=!WEDGES_CONFIRMED[o.key]; drawFlow(svg,w); });
  });
}

buildWorkflows();
document.getElementById('foot').innerHTML=
  `backend: ${esc(T._backend||'?')} · ${esc(T._elapsed_s!=null?T._elapsed_s+'s':'')} · ${esc(T._generated_at||'')}<br>`+
  `inference: ${(T.inference_notes||[]).length?esc(T.inference_notes.join(' ； ')):'none'}<br>`+
  `rendered by ✦dossier P0 · source of truth: talent-object.json · 主副本归本人所有`;

// ---- motion: single scroll handler (jump-proof) ----
(function(){
  document.querySelectorAll('.reveal').forEach((el,i)=>{ el.style.transitionDelay=(i%4)*70+'ms'; });
  let ticking=false;
  function upd(){
    ticking=false;
    const atEnd=scrollY+innerHeight>=document.documentElement.scrollHeight-4;
    const line=atEnd?1e9:innerHeight*0.9;
    document.querySelectorAll('.reveal:not(.in)').forEach(el=>{
      if(el.getBoundingClientRect().top<line) el.classList.add('in');
    });
  }
  addEventListener('scroll',()=>{ if(!ticking){ ticking=true; requestAnimationFrame(upd); } },{passive:true});
  addEventListener('resize',()=>upd(),{passive:true});
  upd();
})();
</script>
</body>
</html>
"""

def render(obj: dict) -> str:
    import datetime
    import re as _re
    obj = dict(obj)
    obj["_generated_at"] = datetime.date.today().isoformat()
    payload = json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
    name = (obj.get("identity", {}).get("display_name") or "unknown")
    user = _re.sub(r"[^a-zA-Z]", "", name).lower()[:10] or "user"
    return (TEMPLATE
            .replace("__NAME__", name)
            .replace("__USER__", user)
            .replace("window.TALENT_OBJECT;", "window.TALENT_OBJECT = " + payload + ";"))
