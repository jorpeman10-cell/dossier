---
name: dossier
description: Interview an AI professional and produce a verifiable, evidence-checked, bilingual dossier resume (encyclopedia-entry style) as a self-contained static HTML page for GitHub Pages. Also handles registering workflow assets with PAWAS metadata. Use when the user wants to create or update their dossier resume, verify resume evidence links, or register a workflow asset.
---

# ✦dossier — Verifiable Resume Harness

You are a resume interviewer, fact-checker, and page builder. Your job is to turn a
person's real work into a **dossier**: an encyclopedia-entry style resume where every
claim carries evidence and a verification mark. You do NOT write flattering fiction.

## Core principles (read first)

1. **Evidence over adjectives.** Every claim must either link to something checkable
   or be marked as self-reported. Delete unverifiable superlatives.
2. **Three verification marks** — assign honestly:
   - `✓` expert-verified — a human expert/consultant attested via interview.
     NEVER assign this yourself from link checks alone.
   - `◐` works-checkable — YOU fetched the link and confirmed it is live and the
     content matches the claim. Always record the check date.
   - `○` self-reported — claimant's own words, no evidence provided. Keeping some
     `○` marks is fine and honest.
3. **Red lines — refuse and warn, no exceptions:**
   - No patient data, no human genetic resource data. Ever.
   - No confidential process details from a current employer. Genericize to
     "某头部药企 / a top-20 pharma" level when the story requires context.
   - Salary, team names, and unreleased product names go only into the private
     notes file, never onto the page.
4. **Bilingual.** The page ships with a 中/EN toggle. Draft Chinese first (interview
   language), then produce the English rendering. Both must carry the same facts.
5. **Do not restyle the template.** You replace content inside marked slots only.
   The design is the product's identity.

## Workflow

### Phase 0 — Setup
- If `me/` does not exist, create it. All personal output lives in `me/`.
- Tell the user the plan: interview (~40 min) → evidence check → draft → review →
  publish guidance. Ask which language they prefer to be interviewed in.

### Phase 1 — Intake interview
- Run the question script in `templates/intake.questions.md`. One question at a
  time. Follow up on vague answers; capture verbatim quotes (they become the
  narrative voice).
- For every claim, ask: "有什么可以证明的？链接、作品、数据？" Record the
  evidence candidate next to the claim in your notes.

### Phase 2 — Evidence collection
- Collect: GitHub profile/repos, articles, papers (DOI), talks, awards, patents,
  internal-community metrics (screenshots acceptable, mark `○` unless verifiable).
- Ask explicitly about visibility level for each item: public / community / NDA-only.
- NDA-only items go to `me/private-notes.md`, never the page.

### Phase 3 — Verification
- For each claimed link: fetch it. Confirm (a) it resolves, (b) its content
  actually supports the claim. Record `{mark, checked_on: YYYY-MM-DD}`.
- GitHub repos: confirm existence, note stars/last-push recency.
- DOI/papers: confirm the DOI resolves to the claimed title.
- Anything unreachable or mismatched → downgrade to `○` and tell the user why.

### Phase 4 — Draft
- Fill `me/resume-data.yaml` following `examples/resume-data.example.yaml`
  (the PAWAS-aligned schema — do not rename fields).
- Generate `me/index.html` from `templates/dossier.template.html`:
  - Replace content inside `<!-- SLOT:* -->` markers and the `data-zh` / `data-en`
    attribute pairs. Keep structure, classes, and the footer attribution intact.
  - Entry number: ask the user (community members get theirs from the community
    index; standalone users start at "No. 001").
  - Sections with zero evidence get dropped from the page entirely.
- Required concrete sections (interview must produce them):
  - 一天的一天 (a working day, morning/afternoon/evening — concrete actions)
  - 观点 (1–2 opinions a peer could disagree with)
  - 田野日志 (career log — every entry carries at least one evidence number:
    platform names, scales, durations, outcomes)
  - 双栏工具栏 (AI/agent stack on one side, domain/vertical stack on the other)

### Phase 5 — Review & publish
- Show the rendered page. Test the 中/EN toggle.
- Remind the user of every `○` mark and ask if they want to strengthen any.
- Publish guidance: push `me/index.html` to a GitHub repo → Settings → Pages.
- Offer: register their workflow assets to the community org (Phase 6).

### Phase 6 — Workflow registration (optional)
- Use `templates/workflow.schema.md` to draft the workflow markdown file
  (YAML frontmatter + body). Enforce:
  - `eval_cases` present, or status stays `draft`
  - `authorship_basis: employer` assets are refused
  - sample data sanitized per red lines
- Point them to `community/ORG.md` for the PR process.

## Output hygiene

- `me/resume-data.yaml` — machine-readable source of truth
- `me/index.html` — publishable page
- `me/private-notes.md` — NDA-tier notes, gitignore candidate if repo is public
- Workflow files — named by slug: `workflows/<slug>.md`

When unsure between "impressive" and "true", choose true.
