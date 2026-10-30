# -*- coding: utf-8 -*-
"""butler_cli.py — CLI front for the career butler (for harnesses without MCP).

Personal edition: resume & position management + external Q&A face.
Usage:  python butler_cli.py <cmd> [args] [--object OBJ]
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
    ap.add_argument("cmd", choices=[
        # external Q&A face
        "ask", "profile", "preferences", "reveal", "verify", "schedule",
        # resume management
        "summary", "add-event", "add-highlight", "add-skills", "regen",
        # position management
        "jobs-add", "jobs", "jobs-status", "match"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--note", default="")
    ap.add_argument("--token", default=None)
    ap.add_argument("--role", default=None)
    ap.add_argument("--org", default=None)
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--hl", action="append", default=[])
    ap.add_argument("--ev", action="append", default=[])
    ap.add_argument("--idx", type=int, default=None)
    ap.add_argument("--text", default=None)
    ap.add_argument("--silicon", action="append", default=[])
    ap.add_argument("--carbon", action="append", default=[])
    ap.add_argument("--title", default=None)
    ap.add_argument("--company", default=None)
    ap.add_argument("--source", default="")
    ap.add_argument("--desc", default="")
    ap.add_argument("--id", dest="job_id", default=None)
    ap.add_argument("--status", default=None)
    ap.add_argument("--object", default=os.environ.get("TALENT_OBJECT")
                    or str(Path(__file__).parent / "demo" / "talent-object.json"))
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
    elif a.cmd == "schedule":
        r = b.schedule_interview(a.arg or "", a.note, a.token)
    elif a.cmd == "summary":
        r = b.resume_summary()
    elif a.cmd == "add-event":
        r = b.resume_add_event(a.role, a.org, a.start, a.hl, a.end, a.ev)
    elif a.cmd == "add-highlight":
        r = b.resume_add_highlight(a.idx if a.idx is not None else -1, a.text or "")
    elif a.cmd == "add-skills":
        r = b.resume_add_skills(a.silicon or None, a.carbon or None)
    elif a.cmd == "regen":
        r = b.resume_regen_page()
    elif a.cmd == "jobs-add":
        r = b.jobs_add(a.title, a.company, a.source, a.note, a.desc)
    elif a.cmd == "jobs":
        r = b.jobs_list()
    elif a.cmd == "jobs-status":
        r = b.jobs_set_status(a.job_id, a.status)
    elif a.cmd == "match":
        r = b.jobs_match(a.job_id)
    else:
        r = {"error": "unreachable"}
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
