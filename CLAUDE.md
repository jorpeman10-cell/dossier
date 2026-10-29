# ✦dossier — Verifiable Resume Harness

This repo is a resume-generating agent harness that runs inside Claude Code.

When the user asks to create or update a dossier resume, verify resume evidence,
or register a workflow asset — load `SKILL.md` and follow its workflow exactly.

Key files:
- `SKILL.md` — the harness instructions (interview → verify → render)
- `templates/` — dossier HTML template, intake questions, workflow schema
- `examples/` — filled example data (fictional person)
- `community/ORG.md` — community org repo structure and curation rules

House rules for code/doc changes in this repo: code comments in English,
README bilingual (中文 primary, English mirror in README.en.md).
