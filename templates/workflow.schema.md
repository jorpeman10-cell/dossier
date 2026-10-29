# Workflow Asset Schema (PAWAS v0.1 subset)

Create one file per workflow: `workflows/<slug>.md`. YAML frontmatter carries
the registry metadata; the body documents the workflow itself.

```yaml
---
# --- identity ---
asset_id: wfa_xxxxxxxx        # system-issued UUID prefix; author may self-issue for v0.1
title: 工作流标题（中英皆可）
slug: url-safe-slug            # lowercase, hyphens; same as filename
version: 1.0.0                 # semver

# --- classification ---
domain: MEDICAL                # RD|CLINICAL|REG|MEDICAL|COMMERCIAL|MARKET_ACCESS|COMPLIANCE|OPS
therapeutic_area: [ONCOLOGY]   # align with community tag taxonomy; [] for TA-agnostic
workflow_type: monitoring_alert  # data_pipeline|document_generation|monitoring_alert|analysis_reporting|agent_orchestration|integration|manual_sop
runtime: lobehub_skill         # claude_code|lobehub_skill|dify|coze|script|manual_sop

# --- safety & ownership ---
data_sensitivity_class: S0     # S0 public | S1 community-visible | S2 NDA-only (S2 never listed)
authorship_basis: personal_time  # personal_time|commissioned|employer  -> "employer" is REFUSED

# --- provenance ---
status: draft                  # draft|registered|verified|retired (listed reserved)
provenance:
  verification_level: V1       # V1 self-reported | V2 works-checkable | V3 expert-verified
  claim_high_watermark: V1     # highest level ever achieved; never decreases
  attestations: []             # e.g. {by: run_reproduction, member: <gh-user>, result: passed, date: YYYY-MM-DD}
  lineage: {source: "", period: ""}   # e.g. source: training_cohort_2026Q4

# --- commerce (reserved, do not activate) ---
license:
  type: community_fork         # personal_use|community_fork|commercial_license|subscription_bundle|royalty_per_run
  price: null                  # {model: one_time|subscription|per_run, amount, currency}
  revenue_share: null

# --- author linkage ---
author:
  name: ""
  github: ""
  dossier_entry: null          # entry number in the community dossier index
---

## What it does
One paragraph: the problem, the trigger, the output.

## Inputs / Outputs (sanitized samples only — red lines apply)
- input example: ...
- output example: ...

## Steps
1. ...

## Eval cases (required for `registered` status)
| input | expected |
|-------|----------|
| ...   | ...      |

## Limitations (be honest — this field is review-critical)
- ...

## Requirements
models: [] / tools: [] / data_access: []
```

Registration rules enforced by maintainers:
1. No `eval_cases` → status stays `draft`.
2. `draft` with no update for 30 days → archived (anti-squatting).
3. `authorship_basis: employer` → refused.
4. Forks: new file, set `parent_asset_id` in a comment line, reset status to `draft`.
