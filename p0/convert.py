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


def _syntax_guard(html: str) -> None:
    """Fail-closed: extract the inline <script> and node --check it."""
    import shutil
    import subprocess
    import tempfile
    s = html[html.find("<script>") + 9: html.find("</script>")]
    node = shutil.which("node")
    if not node:
        print("[warn] node not found — skipped JS syntax guard")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(s)
        path = f.name
    try:
        r = subprocess.run([node, "--check", path], capture_output=True, text=True)
        if r.returncode != 0:
            print("[fail] rendered page has a JS syntax error — page NOT written:")
            print(r.stderr[:500])
            sys.exit(1)
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--out", default=None, help="output dir (default: p0/out/<stem>)")
    ap.add_argument("--backend", default="auto", choices=["auto", "anthropic", "mock"])
    ap.add_argument("--no-workflows", action="store_true", help="skip P1 five-tuple workflow extraction")
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

    # P1: five-tuple workflow extraction (fail-closed per event)
    if not args.no_workflows:
        sys.path.insert(0, str(Path(__file__).parent.parent / "p1"))
        from extract_steps import extract_all
        obj["workflows"] = extract_all(obj)
        n_nodes = sum(len(w.get("nodes", [])) for w in obj["workflows"])
        n_inf = sum(1 for w in obj["workflows"] for e in w.get("edges", []) if e.get("inferred"))
        rejected = sum(1 for w in obj["workflows"] if w.get("notes") and str(w["notes"][0]).startswith("EXTRACTION REJECTED"))
        print(f"     workflows: nodes={n_nodes} inferred_edges={n_inf} rejected_events={rejected}")

    outdir = Path(args.out) if args.out else Path(__file__).parent / "out" / src.stem
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "talent-object.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    html = render(obj)
    _syntax_guard(html)   # never ship a page whose script cannot parse
    (outdir / "page.html").write_text(html, encoding="utf-8")

    n_ev = len(obj.get("career_events", []))
    n_num = sum(len(e.get("evidence_numbers", [])) for e in obj.get("career_events", []))
    print(f"[ok] {src.name} -> {outdir}/")
    print(f"     backend={obj.get('_backend')} elapsed={obj.get('_elapsed_s','—')}s "
          f"events={n_ev} evidence_numbers={n_num} notes={len(obj.get('inference_notes', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
