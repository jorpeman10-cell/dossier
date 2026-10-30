# -*- coding: utf-8 -*-
"""butler_test.py — core access-model tests + live MCP stdio handshake test.

Run:  python butler_test.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from butler import Butler  # noqa: E402

PASS, FAIL = 0, 0


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else ""))
    PASS, FAIL = PASS + (1 if cond else 0), FAIL + (0 if cond else 1)


def test_core():
    print("== core access model ==")
    tmp = Path(tempfile.mkdtemp())
    obj_path = tmp / "to.json"
    obj_path.write_text((HERE / "demo" / "talent-object.json").read_text(encoding="utf-8"), encoding="utf-8")
    b = Butler(obj_path, audit_path=tmp / "audit.jsonl")

    # anonymous: public ok, nda denied-but-exists, workflows (community) blocked
    r = b.get_profile("career_events")
    check("anon public section", "data" in r)
    r = b.get_profile("preferences")
    check("anon nda denied gracefully", r.get("requires") == "higher" or "error" in r or "note" in r, str(r)[:80])
    r = b.ask("做过医保信号监测吗")
    check("ask hits public evidence", "医保信号监测" in r.get("answer", ""), str(r)[:80])
    r = b.ask("求职偏好是什么")
    check("ask refuses nda topic", "授权" in r.get("answer", "") or r.get("requires") == "nda", str(r)[:80])

    # grant token unlocks nda
    r = b.get_preferences(token="grant-employer-001")
    check("token unlocks preferences", "preferences" in r, str(r)[:80])

    # verify: signed claim vs missing claim
    r = b.verify("claim-rwe-x")
    check("verify signed claim", r.get("signature") == "registry-sig-demo-7f3a")
    r = b.verify("claim-nope")
    check("verify missing claim degrades to ○", "error" in r)

    # reveal is one-time and mutates the object
    r = b.reveal_identity(token="grant-reveal-001")
    check("reveal works once", r.get("revealed") is True and r.get("display_name") == "陈之遥")
    r2 = b.reveal_identity(token="grant-reveal-001")
    check("reveal rejected second time", "error" in r2)
    obj2 = json.loads(obj_path.read_text(encoding="utf-8"))
    check("reveal persisted to disk", obj2["agent_config"]["grants"]["grant-reveal-001"]["used"] is True)

    # audit trail written, and never contains NDA content
    audit = (tmp / "audit.jsonl").read_text(encoding="utf-8")
    check("audit has entries", "reveal_identity" in audit and "ask" in audit)
    check("audit never leaks nda content", "open_to" not in audit and "demo@example.com" not in audit)

    # schedule stub
    r = b.schedule_interview("2026-11-05 15:00")
    check("schedule stub queues", r.get("status") == "queued-stub")

    # degraded audit: unwritable audit path (parent is a file) must not crash,
    # must flag responses and fall back — sandboxed-harness scenario
    tmp2 = Path(tempfile.mkdtemp())
    blocker = tmp2 / "blocker"
    blocker.write_text("not a dir", encoding="utf-8")
    b2 = Butler(obj_path, audit_path=blocker / "sub" / "audit.jsonl")
    r = b2.ask("做过医保信号监测吗")
    check("degraded audit does not crash", "answer" in r)
    check("degraded audit flagged in response", r.get("audit_degraded") is True)
    r = b2.get_profile("career_events")
    check("degraded flag on every response", r.get("audit_degraded") is True)

    # ---- personal edition: resume & jobs management ----
    print("== personal edition ==")
    b3 = Butler(obj_path, audit_path=tmp / "audit.jsonl")
    r = b3.resume_summary()
    check("resume summary", r.get("events") is not None and len(r["events"]) >= 1)
    n_before = len(json.loads(obj_path.read_text(encoding="utf-8"))["career_events"])
    r = b3.resume_add_event(role="医药AI顾问", org="某AI公司", start="2027",
                            highlights=["设计AI面试评估流程", "交付3个药企AI项目"], evidence_numbers=["3个药企项目"])
    check("add event ok", r.get("ok") is True)
    obj_now = json.loads(obj_path.read_text(encoding="utf-8"))
    check("event persisted", len(obj_now["career_events"]) == n_before + 1)
    baks = list(tmp.glob("to.json.bak-*.json"))
    check("backup created before mutation", len(baks) == 1)
    r = b3.resume_add_highlight(0, "新增：负责大模型评测体系建设")
    check("add highlight ok", r.get("ok") is True)
    r = b3.resume_add_skills(silicon=["模型评测"])
    check("add skill ok", r.get("ok") is True and "模型评测" in json.loads(obj_path.read_text(encoding="utf-8"))["skills"]["silicon"])
    r = b3.resume_regen_page()
    check("regen page", r.get("ok") is True and (tmp / "page.html").exists() and (tmp / "page.html").stat().st_size > 1000)

    r = b3.jobs_add(title="AI解决方案架构师", company="某创新药企", source="顾问推荐",
                    description="负责医药AI平台建设，需要LobeHub部署经验、MCP工具开发、RAG与agent系统设计经验")
    check("job added", r.get("ok") is True and "id" in r.get("job", {}))
    jid = r["job"]["id"]
    r = b3.jobs_match(jid)
    check("job match runs", r.get("ok") is True and isinstance(r.get("match_score"), int), str(r)[:100])
    check("match lists terms", isinstance(r.get("matched_terms"), list) or "error" in r)
    r = b3.jobs_set_status(jid, "沟通中")
    check("job status set", r.get("ok") is True and r["job"]["status"] == "沟通中")
    r = b3.jobs_list()
    check("jobs listed", len(r.get("jobs", [])) == 1)


def test_mcp_stdio():
    print("== MCP stdio handshake ==")
    env = dict(os.environ)
    env["TALENT_OBJECT"] = str(HERE / "demo" / "talent-object.json")
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.Popen([sys.executable, str(HERE / "butler_server.py")],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env, text=True, encoding="utf-8")

    def send(obj):
        p.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        p.stdin.flush()
        return json.loads(p.stdout.readline())

    r = send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}})
    check("initialize", r["result"]["serverInfo"]["name"] == "career-butler")
    p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    p.stdin.flush()
    r = send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    check("tools/list has 15 tools", len(r["result"]["tools"]) == 15)
    r = send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
              "params": {"name": "ask", "arguments": {"question": "做过真实世界证据平台吗"}}})
    body = json.loads(r["result"]["content"][0]["text"])
    check("tools/call ask returns evidence", "RWE-X" in body.get("answer", ""), str(body)[:100])
    r = send({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
              "params": {"name": "get_profile", "arguments": {"section": "preferences"}}})
    body = json.loads(r["result"]["content"][0]["text"])
    check("nda section denied over MCP too", "error" in body or "授权" in json.dumps(body, ensure_ascii=False))
    p.terminate()


if __name__ == "__main__":
    test_core()
    test_mcp_stdio()
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
