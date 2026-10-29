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
