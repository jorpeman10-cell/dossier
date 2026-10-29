# Community Org Repo — Structure & Curation Rules

The community lives in a GitHub organization (suggested name: `pharma-ai-field`).
The tool is open to everyone; **the curated index is pharma×AI only.**

## Repo layout

```
pharma-ai-field/
├── workflows/            # workflow assets, one .md per asset (see workflow.schema.md)
│   └── <slug>.md
├── dossiers/
│   └── INDEX.md          # curated member dossier index
├── attestations/         # reproduction logs — the "复现即确权" records
│   └── <slug>-<gh-user>.md
└── ORG.md
```

## dossiers/INDEX.md format

| Entry | Name | Domain | TA | Link | Works ✓/◐ | Registered assets |
|-------|------|--------|----|------|-----------|-------------------|
| No. 001 | 陈之遥 (example) | MEDICAL | ONCOLOGY | https://… | 1✓ 1◐ | 2 |

Entry numbers are issued by maintainers, in order of acceptance. They never change.

## Acceptance criteria (both must hold)

1. The dossier page passes evidence checks (≥1 `✓` or ≥2 `◐` marks), and
2. The member has ≥1 workflow asset at `registered` or above in `workflows/`.

## 复现即确权 (Reproduce-to-verify)

Any community member may verify another member's workflow: run it with the
sanitized sample data, and open a PR with an attestation file in
`attestations/` (what ran, output, pass/fail, date). A passing reproduction PR
raises the asset's verification to V2 and appends to `attestations` in its
frontmatter. Maintainers merge; no central bottleneck.

## Anti-squatting

- No `eval_cases` → stays `draft`.
- `draft` untouched for 30 days → maintainer archives it.
- Registration order grants no ranking advantage — ordering anywhere is by
  verification watermark × usage signals, never by registration date.

## Red lines (maintainer-enforced)

- No patient data, no human genetic resource data — instant takedown.
- No current-employer confidential process details; genericize.
- `authorship_basis: employer` assets are refused.

## Curation boundary

Generic AI practitioners are welcome to use the ✦dossier tool and even
contribute code. The curated index and workflow registry accept **pharma×AI**
assets only: `domain` must be one of RD/CLINICAL/REG/MEDICAL/COMMERCIAL/
MARKET_ACCESS/COMPLIANCE/OPS (or workflow explicitly serves a pharma workflow).
