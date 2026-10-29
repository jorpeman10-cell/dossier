# -*- coding: utf-8 -*-
"""extract_steps.py — duty sentences -> five-tuple workflow nodes (PRD P1, §6).

Honesty contract (fail-closed, mirrors the PRD's 诚实性铁律):
  - Nodes (steps) may ONLY come from source sentences — each node carries the
    sentence index it was extracted from. No sentence, no node.
  - Edges (sequence/dataflow) MAY be inferred, but every inferred edge is
    flagged inferred:true and rendered dashed by the projector.
  - Verbs are normalized against the pharma verb dictionary when possible.

Backend: same zero-dependency anthropic REST path as p0/extract.py.
"""
from __future__ import annotations
import json
import os
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent

PROMPT_HEADER = """你是医药×AI猎头团队的工作流提取引擎。任务：把一段职业经历的职责句列表拆解成五元组流程节点和连接，输出严格 JSON（无 markdown 包裹）。

动词词典（用于把同义动词归一到规范动词；无法归一就用原词）：
__VERBS__

输入是一个经历对象的 highlights 句列表。输出 schema：
{
  "nodes": [
    {"id": "s1", "verb": "规范动词", "object": "对象", "tool": "工具或系统，没有则null",
     "collaborator": "协作方，没有则null", "output": "产出",
     "sentence_idx": 0, "stated": true}
  ],
  "edges": [
    {"from": "s1", "to": "s2", "kind": "sequence|dataflow|collaboration", "inferred": true}
  ],
  "notes": ["每条推断连接的理由，逐条列出"]
}

铁律：
1. 每个 node 必须锚定一个原句（sentence_idx 指向输入的下标），禁止发明原文没有的步骤
2. 只有原句有明确先后/数据流向线索时才允许 inferred:false 的边；其余连接一律 inferred:true 并写入 notes
3. verb 归一**仅在语义真正吻合**时使用词典动词；没有合适的词典动词时**必须保留原句动词**，禁止为了归一而硬套（"负责销售"是"销售"不是"销售洞察"；"参与试验"是"参与"不是"方案设计"）
4. 一句可拆多个节点（句内含多步骤时），一个节点不得跨句拼接
5. nodes 按 s1..sN 编号，edges 的 from/to 必须引用存在的节点 id
6. 拆不动的句子（太笼统，如"负责数据相关工作"）直接跳过，不要硬造节点
7. 同一事件内不得产生重复节点（同句+同动词+同对象视为重复）
8. output 必须直接来自原句文字或其明显改写，禁止外推未提及的结果

经历对象：
"""


def _load_verbs() -> str:
    import yaml
    d = yaml.safe_load((HERE / "pharma-verbs.yaml").read_text(encoding="utf-8"))
    return "\n".join(f"- {k}（{v.get('domain','')}）: 同义 {'/'.join(v.get('aliases', [])[:3])}" for k, v in d.items())


def extract_steps(event: dict, event_index: int) -> dict:
    """One career event -> {nodes, edges, notes} or empty structure."""
    sentences = [h for h in (event.get("highlights") or []) if h and str(h).strip()]
    if not sentences:
        return {"event_index": event_index, "nodes": [], "edges": [], "notes": ["no duty sentences"]}
    if not _has_token():
        return {"event_index": event_index, "nodes": [], "edges": [],
                "notes": ["MOCK BACKEND: no real extraction — set ANTHROPIC_AUTH_TOKEN to enable"]}
    payload = {"role": str(event.get("role", "")), "org": str(event.get("org", "")), "highlights": sentences}
    prompt = PROMPT_HEADER.replace("__VERBS__", _load_verbs()) + json.dumps(payload, ensure_ascii=False)
    obj = None
    for attempt in range(2):   # one full retry on malformed/truncated JSON
        try:
            obj = _loads_lenient(_anthropic(prompt))
            break
        except json.JSONDecodeError:
            if attempt == 1:
                raise
    wf = {"event_index": event_index,
          "nodes": _dedup_nodes(obj.get("nodes", [])),
          "edges": obj.get("edges", []),
          "notes": obj.get("notes", [])}
    _drop_dangling_edges(wf)
    problems = validate_workflow(wf, len(sentences))
    if problems:
        wf["nodes"], wf["edges"] = [], []
        wf["notes"] = ["EXTRACTION REJECTED (fail-closed): " + "; ".join(problems)]
    return wf


def _dedup_nodes(nodes: list) -> list:
    """Drop duplicate nodes (same sentence + verb + object prefix) keeping the first."""
    seen, out = set(), []
    for n in nodes:
        key = (n.get("sentence_idx"), n.get("verb"), str(n.get("object", ""))[:12])
        if key in seen:
            continue
        seen.add(key)
        out.append(n)
    return out


def _drop_dangling_edges(wf: dict) -> None:
    ids = {n["id"] for n in wf["nodes"]}
    wf["edges"] = [e for e in wf.get("edges", []) if e.get("from") in ids and e.get("to") in ids]


def validate_workflow(wf: dict, n_sentences: int) -> list[str]:
    """Fail-closed checks; empty list = ok."""
    problems = []
    nodes, edges = wf.get("nodes", []), wf.get("edges", [])
    ids = set()
    for n in nodes:
        for f in ("id", "verb", "output"):
            if not n.get(f):
                problems.append(f"node missing {f}")
        idx = n.get("sentence_idx")
        if not isinstance(idx, int) or not (0 <= idx < n_sentences):
            problems.append(f"node {n.get('id')} sentence_idx out of range")
        if n.get("stated") is not True:
            problems.append(f"node {n.get('id')} not stated (invented step)")
        if n.get("id"):
            ids.add(n["id"])
    for e in edges:
        if e.get("from") not in ids or e.get("to") not in ids:
            problems.append(f"edge {e.get('from')}->{e.get('to')} dangles")
        if e.get("inferred") is not True and e.get("kind") not in ("sequence", "dataflow", "collaboration"):
            problems.append("edge kind invalid")
        if e.get("inferred") is True and not wf.get("notes"):
            problems.append("inferred edges present but no notes")
    if nodes and not all(isinstance(x, str) for x in wf.get("notes", []) or [""]):
        problems.append("notes malformed")
    return problems


def _has_token() -> bool:
    return bool(os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY"))


def _anthropic(prompt: str) -> str:
    base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    model = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-5-5")
    body = json.dumps({"model": model, "max_tokens": 4000, "temperature": 0,
                       "messages": [{"role": "user", "content": prompt[:20000]}]}).encode("utf-8")
    req = urllib.request.Request(base + "/v1/messages", data=body, method="POST", headers={
        "content-type": "application/json", "anthropic-version": "2023-06-01",
        "authorization": "Bearer " + token, "x-api-key": token})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return "".join(b.get("text", "") for b in data.get("content", []))


def _loads_lenient(raw: str) -> dict:
    """strip fences -> salvage object -> repair truncation; raises on failure."""
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*", raw, flags=re.DOTALL)
    candidate = m.group(0) if m else raw
    return json.loads(_repair_truncated(candidate))


def _repair_truncated(s: str) -> str:
    """Close unbalanced strings/brackets of a truncated JSON object."""
    s = s.rstrip().rstrip(",")
    in_str, esc = False, False
    stack = []
    for ch in s:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
    if in_str:
        s += '"'
    s += "".join("}" if c == "{" else "]" for c in reversed(stack))
    return s


def extract_all(obj: dict) -> list[dict]:
    """Talent Object -> workflows list aligned to career_events order."""
    return [extract_steps(e, i) for i, e in enumerate(obj.get("career_events", []))]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE.parent / "p0"))
    target = Path(sys.argv[1])
    data = json.loads(target.read_text(encoding="utf-8"))
    print(json.dumps(extract_all(data), ensure_ascii=False, indent=2))
