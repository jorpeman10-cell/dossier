# -*- coding: utf-8 -*-
"""testset_tools.py — acceptance-test harness for the P1 five-tuple engine.

Usage:
  python p1/testset_tools.py sanitize <raw_dir> <clean_dir>   # PII scrub + split
  python p1/testset_tools.py run <clean_dir> <out_dir>        # batch convert (object+workflows)
  python p1/testset_tools.py score <out_dir>                  # aggregate acceptance metrics

Privacy contract: testset files NEVER leave the local machine;
the whole testset dir is gitignored. Sanitizer strips PII before
anything enters the pipeline.

Acceptance metric (PRD §6): five-tuple accuracy >= 85% on 50 real resumes.
Mechanical parts scored automatically; field-level accuracy is estimated
from a stratified node sample reviewed by a human (prints the sample).
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).parent
PY = sys.executable

# ---------------- sanitize ----------------
PATTERNS = [
    (re.compile(r"1[3-9]\d{9}"), "[手机]"),                     # mobile
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[邮箱]"),          # email
    (re.compile(r"\d{17}[\dXx]"), "[身份证]"),                   # CN ID
    (re.compile(r"\d{3,4}-\d{7,8}"), "[座机]"),                  # landline
    (re.compile(r"[\w-]+QQ\W*\d{5,12}", re.I), "[QQ]"),          # QQ
    (re.compile(r"微信号?\s*[:：]?\s*[\w-]{6,20}"), "[微信]"),     # wechat
]


def sanitize_text(t: str, idx: int) -> str:
    t = re.sub(r"\s+", "\n", t)
    for pat, rep in PATTERNS:
        t = pat.sub(rep, t)
    # anonymize name on the first non-empty line if it looks like a name card
    lines = [l for l in t.split("\n") if l.strip()]
    if lines and len(lines[0].strip()) <= 12 and re.match(r"^[一-龥A-Za-z·\s]+$", lines[0].strip()):
        first = lines.pop(0).strip()
        t = f"候选人{chr(65 + idx % 26)}（原名已脱敏）\n" + "\n".join(lines)
        # also scrub remaining occurrences of the name
        if 2 <= len(first) <= 6:
            t = t.replace(first, f"候选人{chr(65 + idx % 26)}")
    else:
        t = f"候选人{chr(65 + idx % 26)}（无名行）\n" + t
    return t


def cmd_sanitize(raw_dir: str, clean_dir: str):
    raw, clean = Path(raw_dir), Path(clean_dir)
    clean.mkdir(parents=True, exist_ok=True)
    n = 0
    for i, f in enumerate(sorted(raw.glob("*.txt"))):
        (clean / f.name).write_text(sanitize_text(f.read_text(encoding="utf-8", errors="replace"), i), encoding="utf-8")
        n += 1
    # also support the TSV dump format produced from the DB pull (id\tcontent)
    tsv = raw / "testset_raw.tsv"
    if tsv.exists():
        for i, line in enumerate(tsv.read_text(encoding="utf-8", errors="replace").splitlines()):
            parts = line.split("\t", 1)
            if len(parts) != 2 or not parts[0].isdigit():
                continue
            rid, content = parts
            content = content.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "")
            if len(content) < 400:
                continue
            (clean / f"resume-{rid}.txt").write_text(sanitize_text(content, i), encoding="utf-8")
            n += 1
    print(f"[ok] sanitized {n} files -> {clean}")


# ---------------- batch run ----------------
def cmd_run(clean_dir: str, out_dir: str):
    clean, out = Path(clean_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    files = sorted(clean.glob("*.txt"))
    for i, f in enumerate(files, 1):
        r = subprocess.run([PY, str(HERE.parent / "p0" / "convert.py"), str(f), "-o", str(out / f.stem)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           cwd=str(HERE.parent / "p0"), timeout=600)
        ok = "[ok]" in r.stdout
        line = f"{i}/{len(files)} {f.name}: {'OK' if ok else 'FAIL'}"
        print(line, flush=True)
        results.append({"file": f.name, "ok": ok, "stdout": r.stdout[-400:], "stderr": r.stderr[-200:]})
    (out / "_batch.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    n_ok = sum(1 for x in results if x["ok"])
    print(f"[done] {n_ok}/{len(results)} converted")


# ---------------- score ----------------
def cmd_score(out_dir: str):
    out = Path(out_dir)
    verbs = set(yaml.safe_load((HERE / "pharma-verbs.yaml").read_text(encoding="utf-8")).keys())
    stats = dict(files=0, events=0, nodes=0, edges=0, inferred=0,
                 anchored=0, verb_dict_hits=0, rejected_events=0, degraded_files=0)
    node_sample = []
    for j in sorted(out.glob("*/talent-object.json")):
        stats["files"] += 1
        d = json.loads(j.read_text(encoding="utf-8"))
        evs = d.get("career_events", [])
        stats["events"] += len(evs)
        if not evs:
            stats["degraded_files"] += 1
        for w in d.get("workflows", []):
            if w.get("notes") and str(w["notes"][0]).startswith(("EXTRACTION REJECTED", "MOCK")):
                stats["rejected_events"] += 1
            for n in w.get("nodes", []):
                stats["nodes"] += 1
                if isinstance(n.get("sentence_idx"), int) and 0 <= n["sentence_idx"] < len(evs[w["event_index"]].get("highlights", [])) if w["event_index"] < len(evs) else False:
                    stats["anchored"] += 1
                if n.get("verb") in verbs:
                    stats["verb_dict_hits"] += 1
                if len(node_sample) < 120:
                    ev = evs[w["event_index"]] if w["event_index"] < len(evs) else {}
                    sent = (ev.get("highlights") or [None] * 99)[n["sentence_idx"]] if isinstance(n.get("sentence_idx"), int) and n["sentence_idx"] < len(ev.get("highlights") or []) else "(句子缺失)"
                    node_sample.append({"file": j.parent.name, "verb": n.get("verb"), "object": n.get("object"),
                                        "tool": n.get("tool"), "output": n.get("output"), "sentence": sent})
            for e in w.get("edges", []):
                stats["edges"] += 1
                if e.get("inferred"):
                    stats["inferred"] += 1
    a = stats["anchored"]; nds = stats["nodes"] or 1
    print("=" * 46)
    print("P1 验收报告（机械可测部分）")
    print("=" * 46)
    for k, v in stats.items():
        print(f"  {k:18} {v}")
    print(f"  锚定率            {a}/{stats['nodes']} = {a/nds*100:.1f}%  (validator强制=100%才对，低于即bug)")
    print(f"  动词词典命中率     {stats['verb_dict_hits']}/{stats['nodes']} = {stats['verb_dict_hits']/nds*100:.1f}%")
    print(f"  推断边占比         {stats['inferred']}/{stats['edges']} = {(stats['inferred']/(stats['edges'] or 1))*100:.1f}%")
    print()
    print("人工抽检清单（从下面 sample 中抽 40 个核对五元组字段 vs 原句，")
    print("正确数/40 折算准确率；加机械分合成 ≥85% 判定）：")
    (out / "_review_sample.json").write_text(json.dumps(node_sample, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {out/'_review_sample.json'} ({len(node_sample)} nodes)")


if __name__ == "__main__":
    cmds = {"sanitize": cmd_sanitize, "run": cmd_run, "score": cmd_score}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(1)
    cmds[sys.argv[1]](*sys.argv[2:])
