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
import sys
import tempfile
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
        self._audit_degraded = False
        self.access = dict(DEFAULT_ACCESS)
        self.access.update((self.obj.get("agent_config") or {}).get("access", {}))

    # ---------- plumbing ----------
    def _audit(self, action: str, detail: dict) -> None:
        """Append to the audit trail. Never fatal: if the preferred path is
        unwritable (e.g. a sandboxed harness), degrade transparently to a
        fallback location and flag every response — silent degradation would
        be worse than degraded audit."""
        rec = {"ts": int(time.time()), "action": action,
               "audit_degraded": self._audit_degraded, **detail}
        try:
            with self.audit_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            fallback = os.environ.get("BUTLER_AUDIT") or str(
                Path(tempfile.gettempdir()) / f"butler-audit-{self.obj.get('identity', {}).get('anon_id', 'anon')}.jsonl")
            if not self._audit_degraded:
                self._audit_degraded = True
                print(f"[butler] audit path unwritable ({self.audit_path}); "
                      f"degrading to {fallback} — responses will carry audit_degraded=true",
                      file=sys.stderr)
            rec["audit_degraded"] = True
            try:
                with open(fallback, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except OSError:
                print("[butler] WARNING: audit completely unavailable", file=sys.stderr)

    def _flag(self, payload: dict) -> dict:
        """Attach the degraded-audit flag so callers always see it."""
        if self._audit_degraded:
            payload = dict(payload)
            payload["audit_degraded"] = True
        return payload

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
            return self._flag({"error": f"unknown section: {section}"})
        if not self._allowed(section, token):
            self._audit("get_profile.denied", {"section": section})
            return self._flag({"exists": True, "access": "requires-higher-grant",
                               "note": "该分节存在，但需要更高授权（当前匿名/低权级）"})
        data = self._section_data(section)
        self._audit("get_profile", {"section": section})
        return self._flag({"section": section, "data": data})

    def ask(self, question: str, token: str | None = None) -> dict:
        hits, blocked = self._search(question, token)
        self._audit("ask", {"q_len": len(question), "hits": len(hits), "blocked": blocked})
        if not hits and not blocked:
            return self._flag({"answer": "档案中没有与该问题相关的内容。", "evidence": []})
        if not hits and blocked:
            return self._flag({"answer": "存在相关信息，但需要更高授权（NDA 层）才能回答。",
                                "evidence": [], "requires": "nda"})
        lines = [f"{h['text']}（{h.get('org','')}·{h.get('when','')}）" for h in hits[:6]]
        return self._flag({"answer": f"档案中有 {len(hits)} 条相关记录：\n- " + "\n- ".join(lines),
                           "evidence": hits[:6],
                           "note_for_relay": "中转agent请先给一两句自然结论，再引用以上原文；不要贴JSON/表格"})

    def get_preferences(self, token: str | None = None) -> dict:
        if not self._allowed("preferences", token):
            self._audit("get_preferences.denied", {})
            return self._flag({"error": "求职偏好为主人私有（NDA 层），未授权不可见"})
        self._audit("get_preferences", {})
        return self._flag({"preferences": (self.obj.get("agent_config") or {}).get("preferences", {})})

    def reveal_identity(self, token: str | None = None) -> dict:
        g = self._grants()
        if not token or token not in g:
            return self._flag({"error": "无效的揭示令牌"})
        if g[token].get("used"):
            return self._flag({"error": "该令牌已被使用（一次性授权）"})
        g[token]["used"] = True
        g[token]["used_at"] = int(time.time())
        (self.obj.setdefault("agent_config", {})["grants"]) = g
        self._save()
        ident = self.obj.get("identity", {})
        self._audit("reveal_identity", {})
        return self._flag({"revealed": True,
                    "display_name": ident.get("real_name") or ident.get("display_name")})

    def verify(self, claim_id: str) -> dict:
        """Present the registry-anchored badge for a claim (PRD law #3)."""
        for c in (self.obj.get("verification") or {}).get("claims", []):
            if c.get("id") == claim_id:
                self._audit("verify", {"claim": claim_id})
                return self._flag(c)
        self._audit("verify.miss", {"claim": claim_id})
        return self._flag({"error": f"claim {claim_id} 不存在；无签名的主张一律视为 ○ 自述"})

    def schedule_interview(self, when: str, note: str = "", token: str | None = None) -> dict:
        """Stub per PRD P2: real scheduling service is not wired yet."""
        self._audit("schedule_interview", {"when": when, "note_len": len(note)})
        return self._flag({"status": "queued-stub", "when": when,
                           "note": "面试调度服务尚未接线（P2 试点项），已记录请求并通知主人线"})

    # ================== 个人版：简历管理 + 职位管理 ==================

    # ---------- resume management (mutations, backup-first) ----------
    def _mutate(self, reason: str) -> bool:
        """Backup once per process, then caller edits self.obj and saves."""
        if not getattr(self, "_backed_up", False):
            bak = self.path.with_name(self.path.name + f".bak-{int(time.time())}.json")
            bak.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
            self._backed_up = True
            self._audit("backup", {"file": bak.name})
        self._audit("mutate", {"reason": reason})
        return True

    def _validate_self(self) -> None:
        for k in ("identity", "career_events", "skills"):
            if k not in self.obj:
                raise ValueError(f"mutation would break schema: missing {k}")

    def resume_summary(self) -> dict:
        evs = self.obj.get("career_events", [])
        return self._flag({
            "name": self.obj.get("identity", {}).get("display_name"),
            "tagline": self.obj.get("meta", {}).get("tagline"),
            "events": [{"idx": i, "role": e.get("role"), "org": e.get("org"),
                        "start": e.get("start"), "end": e.get("end"),
                        "highlights": len(e.get("highlights", []))}
                       for i, e in enumerate(evs)],
            "skills_silicon": len((self.obj.get("skills") or {}).get("silicon", [])),
            "skills_carbon": len((self.obj.get("skills") or {}).get("carbon", [])),
            "evidence_total": sum(len(e.get("evidence_numbers", [])) for e in evs)})

    def resume_add_event(self, role: str, org: str, start: str, highlights: list[str],
                         end: str | None = None, evidence_numbers: list[str] | None = None) -> dict:
        if not role or not org or not start or not highlights:
            return self._flag({"error": "role/org/start/highlights 必填"})
        self._mutate("resume.add_event")
        ev = {"start": start, "end": end, "role": role, "org": org,
              "highlights": [str(h) for h in highlights]}
        if evidence_numbers:
            ev["evidence_numbers"] = [str(n) for n in evidence_numbers]
        self.obj.setdefault("career_events", []).insert(0, ev)
        self._validate_self()
        self._save()
        return self._flag({"ok": True, "added": role, "events_now": len(self.obj["career_events"]),
                           "note": "已写入主副本（改前已自动备份）"})

    def resume_add_highlight(self, event_index: int, text: str) -> dict:
        evs = self.obj.get("career_events", [])
        if not (0 <= event_index < len(evs)) or not text:
            return self._flag({"error": "event_index 越界或 text 为空"})
        self._mutate("resume.add_highlight")
        evs[event_index].setdefault("highlights", []).append(str(text))
        self._validate_self()
        self._save()
        return self._flag({"ok": True, "event": event_index,
                           "highlights_now": len(evs[event_index]["highlights"])})

    def resume_add_skills(self, silicon: list[str] | None = None, carbon: list[str] | None = None) -> dict:
        self._mutate("resume.add_skills")
        sk = self.obj.setdefault("skills", {})
        for s in silicon or []:
            if s not in sk.setdefault("silicon", []):
                sk["silicon"].append(s)
        for c in carbon or []:
            if c not in sk.setdefault("carbon", []):
                sk["carbon"].append(c)
        self._validate_self()
        self._save()
        return self._flag({"ok": True, "silicon": len(sk["silicon"]), "carbon": len(sk["carbon"])})

    def resume_regen_page(self) -> dict:
        """Regenerate projection A (terminal paradigm page) from the current object."""
        sys.path.insert(0, str(Path(__file__).parent.parent / "p0"))
        try:
            from render import render  # p0 renderer
        except ImportError as e:
            return self._flag({"error": f"p0 renderer unavailable: {e}"})
        html = render(self.obj)
        out = self.path.parent / "page.html"
        out.write_text(html, encoding="utf-8")
        self._audit("regen_page", {"bytes": len(html)})
        return self._flag({"ok": True, "page": str(out), "bytes": len(html),
                           "note": "浏览器直接打开即可；发布到 GitHub Pages 另行走 docs/ 流程"})

    # ---------- position management ----------
    def _jobs_path(self) -> Path:
        return self.path.parent / "jobs.json"

    def _jobs(self) -> dict:
        p = self._jobs_path()
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {"jobs": []}

    def jobs_add(self, title: str, company: str, source: str = "", notes: str = "",
                 description: str = "") -> dict:
        if not title or not company:
            return self._flag({"error": "title/company 必填"})
        j = self._jobs()
        item = {"id": f"job-{int(time.time())}", "title": title, "company": company,
                "source": source, "notes": notes, "status": "看机会",
                "description": description, "created": int(time.time())}
        j["jobs"].append(item)
        self._jobs_path().write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        self._audit("jobs.add", {"title": title, "company": company})
        return self._flag({"ok": True, "job": item})

    def jobs_list(self) -> dict:
        return self._flag(self._jobs())

    def jobs_set_status(self, job_id: str, status: str) -> dict:
        if status not in ("看机会", "已投递", "沟通中", "面试中", "offer", "放弃"):
            return self._flag({"error": "status 须为：看机会/已投递/沟通中/面试中/offer/放弃"})
        j = self._jobs()
        for it in j["jobs"]:
            if it["id"] == job_id:
                it["status"] = status
                self._jobs_path().write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
                self._audit("jobs.status", {"job": job_id, "status": status})
                return self._flag({"ok": True, "job": it})
        return self._flag({"error": f"job {job_id} 不存在"})

    def jobs_match(self, job_id: str) -> dict:
        """Honest keyword match between one job's description and my profile.
        Not a model judgment — terms in/out are listed so the human decides."""
        j = self._jobs()
        job = next((it for it in j["jobs"] if it["id"] == job_id), None)
        if not job:
            return self._flag({"error": f"job {job_id} 不存在，先 jobs_add"})
        jd = (job.get("description") or "") + " " + job.get("title", "")
        if len(jd.strip()) < 10:
            return self._flag({"error": "该职位没有描述文本，无法匹配（jobs_add 时带 description）"})
        terms = sorted({t for t in _terms(jd) if len(t) >= 2})
        mine = set()
        for s in (self.obj.get("skills") or {}).values():
            mine.update(str(x) for x in s)
        profile_text = json.dumps({k: self.obj.get(k) for k in ("career_events", "skills")}, ensure_ascii=False)
        hit_terms = [t for t in terms if t in profile_text]
        missing = [t for t in terms if t not in profile_text and t not in mine][:12]
        score = round(len(hit_terms) / max(1, len(terms)) * 100)
        self._audit("jobs.match", {"job": job_id, "score": score})
        return self._flag({"ok": True, "job": f'{job["company"]}·{job["title"]}',
                           "match_score": score,
                           "matched_terms": hit_terms[:15],
                           "missing_terms": missing,
                           "note": "关键词匹配（非模型判断），matched/missing 全列出，由主人自己判断"})

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
