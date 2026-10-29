# ✦dossier — A Verifiable Resume Harness

> A resume should not be a list of adjectives. It should be a chain of evidence.

**✦dossier** is an open-source Claude Code agent harness that interviews you and
produces an encyclopedia-entry style personal dossier page.
Unlike every other resume tool, it does not just help you write — it helps you
**be verified**.

## Features

- **Interview-driven generation** — an 8-question intake produces six sections
  (self-narrative / a working day / opinions / works / field log / dual toolbar),
  rendered bilingual with a one-click 中/EN toggle.
- **Automated falsifiability** — every evidence link is actually fetched and
  checked by the agent, then marked on a three-tier scale:
  - `✓` expert-verified (human attestation via interview)
  - `◐` works-checkable (agent fetched the link, content matches the claim)
  - `○` self-reported (honestly labeled, never dressed up)
- **Built-in compliance red lines** — patient data, human genetic resource data,
  and current-employer confidential process details are refused outright;
  sensitive items go to an NDA tier, the public page stays sanitized.
- **Workflow asset registration** — ships the PAWAS metadata schema: your
  workflows become reproducible, forkable assets, linked from the resume.

## Quick start

```bash
# 1. Create your own repo from this template and clone it
# 2. Start Claude Code inside the repo
claude
# 3. Say: "帮我做简历档案" (or "build my dossier")
#    ~40 min interview → produces me/index.html
# 4. Push to GitHub → Settings → Pages → your dossier is live
```

## Community

The tool is open to all AI practitioners; the **pharma×AI community**
(vertical curation) runs in the community org — see
[community/ORG.md](community/ORG.md) for the workflow-asset registry,
the dossier index, and the reproduce-to-verify mechanism.

## Roadmap

- [ ] Hosted version (no GitHub needed, generate online at hiijob.cn)
- [ ] Data-gated runtime (vertical workflows bound to industry data, per-run royalties)
- [ ] Verification badge API (third parties can validate `◐` marks)

## License

Apache-2.0.
