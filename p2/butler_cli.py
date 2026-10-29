# -*- coding: utf-8 -*-
"""butler_cli.py — CLI front for the career butler (for harnesses without MCP).

Usage:
  python butler_cli.py ask "做过医保测算吗" [--token T]
  python butler_cli.py profile career_events [--token T]
  python butler_cli.py preferences --token T
  python butler_cli.py reveal --token T
  python butler_cli.py verify claim-rwe-x
  python butler_cli.py schedule "2026-11-05 15:00" --note "一面"
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from butler import Butler  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["ask", "profile", "preferences", "reveal", "verify", "schedule"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--note", default="")
    ap.add_argument("--token", default=None)
    ap.add_argument("--object", default=os.environ.get("TALENT_OBJECT") or str(Path(__file__).parent / "demo" / "talent-object.json"))
    a = ap.parse_args()

    b = Butler(a.object)
    if a.cmd == "ask":
        r = b.ask(a.arg or "", a.token)
    elif a.cmd == "profile":
        r = b.get_profile(a.arg or "meta", a.token)
    elif a.cmd == "preferences":
        r = b.get_preferences(a.token)
    elif a.cmd == "reveal":
        r = b.reveal_identity(a.token)
    elif a.cmd == "verify":
        r = b.verify(a.arg or "")
    else:
        r = b.schedule_interview(a.arg or "", a.note, a.token)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
