---
# Example workflow asset (FICTIONAL). File name = slug.
asset_id: wfa_9d2e11aa
title: 医保目录信号周监测（肿瘤）
slug: claims-signal-weekly-oncology
version: 1.1.0

domain: MARKET_ACCESS
therapeutic_area: [ONCOLOGY]
workflow_type: monitoring_alert
runtime: lobehub_skill

data_sensitivity_class: S0
authorship_basis: personal_time

status: verified
provenance:
  verification_level: V2
  claim_high_watermark: V2
  attestations:
    - {by: run_reproduction, member: some-gh-user, result: passed, date: "2026-09-02"}
    - {by: expert_interview, consultant: advisor-03, result: passed, date: "2026-09-15"}
  lineage: {source: self-built, period: "2024-2026"}

license:
  type: community_fork
  price: null
  revenue_share: null

author:
  name: 陈之遥
  github: zhiyao-example
  dossier_entry: "001"
---

## What it does
Weekly scan of claims/policy sources for signals that affect oncology products
(directory adjustments, negotiation lists, volume-based procurement scope).
Output: one decision brief per product, ranked by urgency.

## Inputs / Outputs (sanitized)
- input: monitored product list + therapeutic-area keywords (public sources)
- output: markdown brief — signal, affected products, suggested owner action

## Steps
1. Pull the week's policy/claims feeds (public endpoints only).
2. Filter by TA keyword dictionary; deduplicate against last week's brief.
3. Draft per-product impact lines; attach source links.
4. Human (author) reviews sign-off suggestions before send.

## Eval cases
| input | expected |
|-------|----------|
| feed week with 1 known directory adjustment | brief flags exactly that product, cites source |
| quiet week | brief states "no material signals" and still ships |

## Limitations
- Public sources only — no internal pricing data.
- Keyword dictionary maintained by hand; misses are possible.
- Suggested actions are drafts, never compliance conclusions.

## Requirements
models: [claude-sonnet-5-5]
tools: [web_fetch, keyword_dictionary]
data_access: []
