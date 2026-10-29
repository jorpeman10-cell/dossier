# -*- coding: utf-8 -*-
"""butler.py — career-butler core (P2, PRD v0.2 §7/§8).

The butler serves ONE talent object (master copy stays local, per law #2)
and enforces the trust model:

  - sections carry visibility: public | community | nda  (nda NEVER leaves)
  - ask() answers only from allowed sections, with evidence quotes
  - reveal_identity() is a one-time grant, logged
  - every call appends to butler-audit.jsonl (who/what/when, never NDA content)

No third-party deps. The MCP server and the CLI are thin fronts over this.
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

VISIBILITY_ORDER = {"public": 0, "community": 1, "nda": 2}
DEFAULT_ACCESS = {
    "identity": "public", "meta": "public", "career_events": "public",
    "skills": "public", "certs": "public", "education": "public",
    "evidence": "public", "workflows": "community",
    "preferences": "nda", "contact": "nda",
}


class Butler:
    def __init__(self, object_path: str | Path, audit_path: str | Path | None = None):
        self.path = Path(object_path)
        self.obj = json.loads(self.path.read_text(encoding="utf-8"))
        base = self.path.parent
        self.audit_path = Path(audit_path) if audit_path else base / "butler-audit.jsonl"
        self.access = dict(DEFAULT_ACCESS)
        self.access.update((self.obj.get("agent_config") or {}).get("access", {}))

    # ---------- plumbing ----------
    def _audit(self, action: str, detail: dict) -> None:
        rec = {"ts": int(time.time()), "action": action, **detail}
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def _grants(self) -> dict:
        return (self.obj.get("agent_config") or {}).get("grants", {})

    def _token_level(self, token: str | None) -> str:
        """Resolve a caller token to its access level."""
        if not token:
            return "public"
        g = self._grants().get(token)
        return g.get("level") if g and not g.get("used") else "public"

    def _allowed(self, section: str, token: str | None) -> bool:
        need = VISIBILITY_ORDER.get(self.access.get(section, "nda"), 2)
        have = VISIBILITY_ORDER[self._token_level(token)]
        return have >= need

    # ---------- tool surface (PRD §7) ----------
    def get_profile(self, section: str, token: str | None = None) -> dict:
        if section not in DEFAULT_ACCESS:
            return {"error": f"unknown section: {section}"}
        if not self._allowed(section, token):
            self._audit("get_profile.denied", {"section": section})
            return {"exists": True, "access": "requires-higher-grant",
                    "note": "该分节存在，但需要更高授权（当前匿名/低权级）"}
        data = self._section_data(section)
        self._audit("get_profile", {"section": section})
        return {"section": section, "data": data}

    def ask(self, question: str, token: str | None = None) -> dict:
        hits, blocked = self._search(question, token)
        self._audit("ask", {"q_len": len(question), "hits": len(hits), "blocked": blocked})
        if not hits and not blocked:
            return {"answer": "档案中没有与该问题相关的内容。", "evidence": []}
        if not hits and blocked:
            return {"answer": "存在相关信息，但需要更高授权（NDA 层）才能回答。",
                    "evidence": [], "requires": "nda"}
        lines = [h["text"] for h in hits[:6]]
        return {"answer": "根据档案中的以下内容作答（引用原文）：\n- " + "\n- ".join(lines),
                "evidence": hits[:6]}

    def get_preferences(self, token: str | None = None) -> dict:
        if not self._allowed("preferences", token):
            self._audit("get_preferences.denied", {})
            return {"error": "求职偏好为主人私有（NDA 层），未授权不可见"}
        self._audit("get_preferences", {})
        return {"preferences": (self.obj.get("agent_config") or {}).get("preferences", {})}

    def reveal_identity(self, token: str | None = None) -> dict:
        g = self._grants()
        if not token or token not in g:
            return {"error": "无效的揭示令牌"}
        if g[token].get("used"):
            return {"error": "该令牌已被使用（一次性授权）"}
        g[token]["used"] = True
        g[token]["used_at"] = int(time.time())
        (self.obj.setdefault("agent_config", {})["grants"]) = g
        self._save()
        ident = self.obj.get("identity", {})
        self._audit("reveal_identity", {})
        return {"revealed": True,
                "display_name": ident.get("real_name") or ident.get("display_name")}

    def verify(self, claim_id: str) -> dict:
        """Present the registry-anchored badge for a claim (PRD law #3)."""
        for c in (self.obj.get("verification") or {}).get("claims", []):
            if c.get("id") == claim_id:
                self._audit("verify", {"claim": claim_id})
                return c
        self._audit("verify.miss", {"claim": claim_id})
        return {"error": f"claim {claim_id} 不存在；无签名的主张一律视为 ○ 自述"}

    def schedule_interview(self, when: str, note: str = "", token: str | None = None) -> dict:
        """Stub per PRD P2: real scheduling service is not wired yet."""
        self._audit("schedule_interview", {"when": when, "note_len": len(note)})
        return {"status": "queued-stub", "when": when,
                "note": "面试调度服务尚未接线（P2 试点项），已记录请求并通知主人线"}

    # ---------- internals ----------
    def _section_data(self, section: str):
        mapping = {
            "identity": self.obj.get("identity"), "meta": self.obj.get("meta"),
            "career_events": self.obj.get("career_events"), "skills": self.obj.get("skills"),
            "certs": self.obj.get("certs"), "education": self.obj.get("education"),
            "evidence": [n for e in self.obj.get("career_events", []) for n in e.get("evidence_numbers", [])],
            "workflows": self.obj.get("workflows"),
            "preferences": (self.obj.get("agent_config") or {}).get("preferences"),
            "contact": (self.obj.get("agent_config") or {}).get("contact"),
        }
        if section == "identity":
            d = dict(mapping["identity"] or {})
            if not (self._grants()):
                d.pop("real_name", None)   # real name only via reveal
            return d
        return mapping.get(section)

    def _search(self, question: str, token: str | None):
        terms = [t for t in _terms(question) if len(t) >= 2][:8]
        hits, blocked = [], False
        # public layer: career highlights
        for ev in self.obj.get("career_events", []):
            for h in ev.get("highlights", []) or []:
                if any(t in str(h) for t in terms):
                    hits.append({"section": "career_events", "text": str(h),
                                 "org": ev.get("org"), "when": ev.get("start")})
        # restricted layers: if terms hit a section the caller can't read,
        # flag blocked — never deny the information EXISTS (leak-by-omission)
        restricted_texts = {
            "workflows": ["工作流 workflow 流程 节点"] + [
                f"{n.get('verb','')}{n.get('object','')}{n.get('output','')}"
                for e in (self.obj.get("workflows") or []) for n in e.get("nodes", [])],
            "preferences": ["求职偏好 preferences 期望 薪资 到岗",
                            json.dumps((self.obj.get("agent_config") or {}).get("preferences", {}), ensure_ascii=False)],
            "contact": ["联系方式 contact 电话 邮箱 email phone 微信",
                        json.dumps((self.obj.get("agent_config") or {}).get("contact", {}), ensure_ascii=False)],
        }
        for section, texts in restricted_texts.items():
            if self._allowed(section, token):
                continue
            if any(any(t in txt for t in terms) for txt in texts):
                blocked = True
        return hits, blocked

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _terms(q: str) -> list[str]:
    """Cheap CJK-friendly term split: bigrams + ascii words."""
    out, buf = [], ""
    for ch in q:
        if "一" <= ch <= "鿿":
            if buf:
                out.append(buf); buf = ""
            out.append(ch)
        elif ch.isalnum():
            buf += ch
        else:
            if buf:
                out.append(buf); buf = ""
    if buf:
        out.append(buf)
    bigrams = [a + b for a, b in zip(out, out[1:]) if "一" <= a <= "鿿" and "一" <= b <= "鿿"]
    return out + bigrams
