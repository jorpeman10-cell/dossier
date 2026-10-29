# -*- coding: utf-8 -*-
"""extract.py — resume text -> Talent Object (P0 subset) via LLM.

Backends:
  anthropic : stdlib REST call using ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN
              (or ANTHROPIC_API_KEY) from the environment. Zero deps.
  mock      : deterministic stub for offline pipeline testing. NOT for
              real validation — it extracts nothing.

Honesty rules baked into the prompt (PRD v0.2 §1/§6):
  - extract verbatim; never invent numbers, dates or employers
  - anything synthesized must be listed in inference_notes
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.request

PROMPT = """你是一个医药×AI猎头团队的简历结构化引擎。把下面的简历文本转成严格的 JSON（不要 markdown 代码块，直接输出 JSON 对象），schema 如下：

{
  "identity": {"display_name": "姓名（中文优先，有英文名附上）"},
  "meta": {"tagline": "一句话人设（≤30字，只基于简历事实综合）", "city": "城市（简历未写则空字符串）"},
  "career_events": [
    {"start": "YYYY（原文无年份则null，禁止占位符）", "end": "YYYY或null(在职)", "role": "职位", "org": "公司名（照抄原文，原文没有则空字符串）",
     "highlights": ["职责/成果要点，尽量保留原文数字", "最多5条"],
     "evidence_numbers": ["这段经历里的关键数字，如'11万患者池'、'3个瘤种'，没有就空数组"]}
  ],
  "skills": {"silicon": ["AI/数据/技术类技能"], "carbon": ["医药领域类技能与治疗领域"]},
  "certs": ["认证/证书"],
  "education": [{"years": "", "school": "", "major": ""}],
  "inference_notes": ["任何你推断/合并/翻译得到的内容，逐条列出；纯照抄则空数组"]
}

铁律：
1. 只从文本提取，禁止编造任何数字、日期、公司、头衔
2. 原文没有的时间/公司一律填 null 或空字符串，禁止使用"20XX"之类的占位符
3. tagline 是唯一允许综合表述的字段，且必须写入 inference_notes
4. career_events 按时间倒序（最新在前）
5. 输出必须是可被 json.loads 直接解析的纯 JSON

简历文本：
"""


def extract(text: str, backend: str = "auto") -> dict:
    backend = _resolve(backend)
    if backend == "mock":
        return _mock(text)
    return _anthropic(text)


def _resolve(backend: str) -> str:
    if backend == "mock":
        return "mock"
    has_token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if backend == "anthropic" and not has_token:
        raise RuntimeError("anthropic backend requested but no ANTHROPIC_AUTH_TOKEN/ANTHROPIC_API_KEY in env")
    if backend == "auto":
        return "anthropic" if has_token else "mock"
    return backend


def _anthropic(text: str) -> dict:
    base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    model = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-5-5")
    body = json.dumps({
        "model": model,
        "max_tokens": 4000,
        "temperature": 0,
        "messages": [{"role": "user", "content": PROMPT + text[:15000]}],
    }).encode("utf-8")
    req = urllib.request.Request(
        base + "/v1/messages", data=body, method="POST",
        headers={
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
            # AUTH_TOKEN -> bearer; API_KEY -> x-api-key. Send both styles to be safe.
            "authorization": "Bearer " + token,
            "x-api-key": token,
        })
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    raw = "".join(b.get("text", "") for b in data.get("content", []))
    obj = _loads_lenient(raw)
    obj["_backend"] = f"anthropic:{model}"
    obj["_elapsed_s"] = round(time.time() - t0, 1)
    return obj


def _loads_lenient(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # salvage the outermost {...}
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def _mock(text: str) -> dict:
    """Offline stub: shape-valid, content-empty. Pipeline testing only."""
    return {
        "identity": {"display_name": ""},
        "meta": {"tagline": "", "city": ""},
        "career_events": [],
        "skills": {"silicon": [], "carbon": []},
        "certs": [],
        "education": [],
        "inference_notes": ["MOCK BACKEND: no real extraction performed"],
        "_backend": "mock",
    }


def validate(obj: dict) -> list[str]:
    """Fail-closed sanity checks; returns list of problems (empty = ok)."""
    problems = []
    for key in ("identity", "meta", "career_events", "skills"):
        if key not in obj:
            problems.append(f"missing key: {key}")
    if "skills" in obj:
        for side in ("silicon", "carbon"):
            if side not in obj["skills"]:
                problems.append(f"missing skills.{side}")
    ev = obj.get("career_events", [])
    if not isinstance(ev, list):
        problems.append("career_events not a list")
    else:
        for i, e in enumerate(ev):
            for f in ("start", "role", "org"):
                if f not in e:
                    problems.append(f"career_events[{i}] missing {f}")
    return problems


if __name__ == "__main__":
    import sys
    from ingest import ingest
    print(json.dumps(extract(ingest(sys.argv[1])), ensure_ascii=False, indent=2))
