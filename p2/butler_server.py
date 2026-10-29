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
