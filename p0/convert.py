# -*- coding: utf-8 -*-
"""convert.py — P0 pipeline CLI: resume file -> Talent Object JSON + page.html

Usage:
  python convert.py <resume.(txt|md|docx|pdf)> [-o outdir] [--backend auto|anthropic|mock]
Outputs:
  <outdir>/talent-object.json   projection B (machine-readable)
  <outdir>/page.html            projection A-lite (V1/V3/V4 views)
Exit code 1 with a clear message on any validation failure (fail-closed).
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ingest import ingest          # noqa: E402
from extract import extract, validate  # noqa: E402
from render import render          # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out", default=None, help="output dir (default: p0/out/<stem>)")
    ap.add_argument("--backend", default="auto", choices=["auto", "anthropic", "mock"])
    args = ap.parse_args()

    src = Path(args.input)
    text = ingest(src)
    if len(text.strip()) < 40:
        print(f"[fail] input too short ({len(text.strip())} chars) — is this a real resume?")
        return 1

    obj = extract(text, backend=args.backend)
    problems = validate(obj)
    if problems:
        print("[fail] extraction did not pass schema validation:")
        for p in problems:
            print("   -", p)
        return 1

    outdir = Path(args.out) if args.out else Path(__file__).parent / "out" / src.stem
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "talent-object.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "page.html").write_text(render(obj), encoding="utf-8")

    n_ev = len(obj.get("career_events", []))
    n_num = sum(len(e.get("evidence_numbers", [])) for e in obj.get("career_events", []))
    print(f"[ok] {src.name} -> {outdir}/")
    print(f"     backend={obj.get('_backend')} elapsed={obj.get('_elapsed_s','—')}s "
          f"events={n_ev} evidence_numbers={n_num} notes={len(obj.get('inference_notes', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
