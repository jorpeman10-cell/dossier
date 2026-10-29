# -*- coding: utf-8 -*-
"""assemble_testset.py — DB TSV dump -> per-resume synthetic text files.

Input:  testset_raw2.tsv  (rows: id, company, position, begin, end, description, self_eval)
Output: testset_raw_files/resume-<id>.txt  (synthetic resume text, still UNSANITIZED)
Then testset_tools sanitize scrubs PII. Selection: 20 files, multi-event first.

The description column is split into bullet lines at 。；; boundaries —
this mirrors how duties appear in real resumes fed to the converter.
"""
from __future__ import annotations
import re
import sys
from collections import defaultdict
from pathlib import Path


def unescape(s: str) -> str:
    return s.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "").replace("\\0", "\0")


def split_duties(desc: str) -> list[str]:
    parts = re.split(r"(?<=[。；;])", desc)
    lines = [p.strip(" \t，,、") for p in parts]
    return [l for l in lines if len(l) >= 6][:8]


def main(tsv_path: str, out_dir: str, pick: int = 20):
    rows = defaultdict(lambda: {"eval": "", "jobs": []})
    for line in Path(tsv_path).read_text(encoding="utf-8", errors="replace").splitlines():
        f = line.split("\t")
        if len(f) != 7 or not f[0].isdigit():
            continue
        rid, company, position, begin, end, desc, se = f
        r = rows[int(rid)]
        if se and not r["eval"]:
            r["eval"] = unescape(se).strip()
        duties = split_duties(unescape(desc))
        if duties:
            r["jobs"].append((unescape(company).strip(), unescape(position).strip(), begin, end, duties))

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # prefer resumes with >=2 experience blocks (harder test), then single
    ranked = sorted(rows.items(), key=lambda kv: -len(kv[1]["jobs"]))
    chosen = []
    for rid, r in ranked:
        if len(chosen) >= pick:
            break
        if not r["jobs"]:
            continue
        parts = [f"候选人{rid}（待脱敏）"]
        if r["eval"]:
            parts += ["", "自我评价", r["eval"]]
        parts += ["", "工作经历"]
        for company, position, begin, end, duties in r["jobs"]:
            parts += ["", f"{company} · {position} · {begin}—{end}"]
            parts += [f"- {d}" for d in duties]
        (out / f"resume-{rid}.txt").write_text("\n".join(parts), encoding="utf-8")
        chosen.append(rid)
    print(f"[ok] assembled {len(chosen)} files (from {len(rows)} resumes) -> {out}")
    print("     multi-event:", sum(1 for _, r in ranked[:len(chosen)] if len(r["jobs"]) >= 2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../testset_raw2.tsv",
         sys.argv[2] if len(sys.argv) > 2 else "../testset_raw_files",
         int(sys.argv[3]) if len(sys.argv) > 3 else 20)
