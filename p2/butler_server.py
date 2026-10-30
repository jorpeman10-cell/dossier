# -*- coding: utf-8 -*-
"""butler_server.py — stdio MCP front for the career butler (zero-dep).

Speaks the Model Context Protocol over stdio using newline-delimited
JSON-RPC 2.0. Mount from Claude Code:

  "mcpServers": { "career-butler": {
      "command": "python",
      "args": ["C:/path/to/dossier/p2/butler_server.py"],
      "env": { "TALENT_OBJECT": "C:/path/to/me/talent-object.json" } } }
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from butler import Butler  # noqa: E402

TOOLS = [
    {"name": "get_profile", "description": "按访问等级获取档案分节（identity/meta/career_events/skills/certs/education/evidence/workflows）。越权返回'存在但需授权'",
     "inputSchema": {"type": "object", "properties": {
         "section": {"type": "string"}, "token": {"type": "string", "description": "访问令牌（匿名可空）"}},
         "required": ["section"]}},
    {"name": "ask", "description": "向职场管家提问。答案带档案原文引用；无证据则明说；越权信息拒答",
     "inputSchema": {"type": "object", "properties": {
         "question": {"type": "string"}, "token": {"type": "string"}}, "required": ["question"]}},
    {"name": "get_preferences", "description": "获取求职偏好（NDA 层，需授权令牌）",
     "inputSchema": {"type": "object", "properties": {"token": {"type": "string"}}}},
    {"name": "reveal_identity", "description": "匿名→实名揭示（一次性授权令牌，使用后作废并留痕）",
     "inputSchema": {"type": "object", "properties": {"token": {"type": "string"}}, "required": ["token"]}},
    {"name": "verify", "description": "出示某条主张的登记处签名徽章；无签名主张一律视为自述 ○",
     "inputSchema": {"type": "object", "properties": {"claim_id": {"type": "string"}}, "required": ["claim_id"]}},
    {"name": "schedule_interview", "description": "预约面试（P2 为存根：记录请求并通知主人）",
     "inputSchema": {"type": "object", "properties": {
         "when": {"type": "string"}, "note": {"type": "string"}, "token": {"type": "string"}},
         "required": ["when"]}},
    # ---- personal edition: resume & position management ----
    {"name": "resume_summary", "description": "简历概况：经历列表/技能计数/证据总数",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "resume_add_event", "description": "新增一段经历（改前自动备份主副本）",
     "inputSchema": {"type": "object", "properties": {
         "role": {"type": "string"}, "org": {"type": "string"}, "start": {"type": "string"},
         "end": {"type": "string"}, "highlights": {"type": "array", "items": {"type": "string"}},
         "evidence_numbers": {"type": "array", "items": {"type": "string"}}},
         "required": ["role", "org", "start", "highlights"]}},
    {"name": "resume_add_highlight", "description": "给第 N 段经历追加一条职责/成果",
     "inputSchema": {"type": "object", "properties": {
         "event_index": {"type": "integer"}, "text": {"type": "string"}},
         "required": ["event_index", "text"]}},
    {"name": "resume_add_skills", "description": "追加技能（silicon=AI/数据侧, carbon=领域侧）",
     "inputSchema": {"type": "object", "properties": {
         "silicon": {"type": "array", "items": {"type": "string"}},
         "carbon": {"type": "array", "items": {"type": "string"}}}}},
    {"name": "resume_regen_page", "description": "从当前主副本重新生成简历页 page.html（终端范式）",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "jobs_add", "description": "记录一个在看的机会（title/company/source/notes/description=JD文本，用于匹配）",
     "inputSchema": {"type": "object", "properties": {
         "title": {"type": "string"}, "company": {"type": "string"}, "source": {"type": "string"},
         "notes": {"type": "string"}, "description": {"type": "string"}},
         "required": ["title", "company"]}},
    {"name": "jobs_list", "description": "列出我在看的全部机会及状态",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "jobs_set_status", "description": "更新机会状态（看机会/已投递/沟通中/面试中/offer/放弃）",
     "inputSchema": {"type": "object", "properties": {
         "job_id": {"type": "string"}, "status": {"type": "string"}},
         "required": ["job_id", "status"]}},
    {"name": "jobs_match", "description": "关键词匹配：该职位 JD vs 我的档案（matched/missing 全列出，人做判断）",
     "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"}},
         "required": ["job_id"]}},
]

PROTOCOL_VERSION = "2025-03-26"


def dispatch(butler: Butler, name: str, args: dict) -> dict:
    token = args.get("token")
    if name == "get_profile":
        return butler.get_profile(args["section"], token)
    if name == "ask":
        return butler.ask(args["question"], token)
    if name == "get_preferences":
        return butler.get_preferences(token)
    if name == "reveal_identity":
        return butler.reveal_identity(token)
    if name == "verify":
        return butler.verify(args["claim_id"])
    if name == "schedule_interview":
        return butler.schedule_interview(args["when"], args.get("note", ""), token)
    if name == "resume_summary":
        return butler.resume_summary()
    if name == "resume_add_event":
        return butler.resume_add_event(args["role"], args["org"], args["start"],
                                       args.get("end"), args["highlights"], args.get("evidence_numbers"))
    if name == "resume_add_highlight":
        return butler.resume_add_highlight(args["event_index"], args["text"])
    if name == "resume_add_skills":
        return butler.resume_add_skills(args.get("silicon"), args.get("carbon"))
    if name == "resume_regen_page":
        return butler.resume_regen_page()
    if name == "jobs_add":
        return butler.jobs_add(args["title"], args["company"], args.get("source", ""),
                               args.get("notes", ""), args.get("description", ""))
    if name == "jobs_list":
        return butler.jobs_list()
    if name == "jobs_set_status":
        return butler.jobs_set_status(args["job_id"], args["status"])
    if name == "jobs_match":
        return butler.jobs_match(args["job_id"])
    return {"error": f"unknown tool {name}"}


def serve() -> None:
    obj_path = os.environ.get("TALENT_OBJECT") or str(Path(__file__).parent / "demo" / "talent-object.json")
    butler = Butler(obj_path)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        rid, method = req.get("id"), req.get("method", "")

        if method == "initialize":
            resp = {"jsonrpc": "2.0", "id": rid, "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "career-butler", "version": "0.1.0"}}}
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            try:
                result = dispatch(butler, req["params"]["name"], req["params"].get("arguments", {}))
                resp = {"jsonrpc": "2.0", "id": rid, "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                    "isError": False}}
            except Exception as e:  # noqa: BLE001 — surface to the model, never crash the server
                resp = {"jsonrpc": "2.0", "id": rid, "result": {
                    "content": [{"type": "text", "text": f"butler error: {e}"}], "isError": True}}
        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": rid, "result": {}}
        else:
            if rid is None:
                continue
            resp = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    serve()
