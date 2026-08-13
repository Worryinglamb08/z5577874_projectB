# Prompt log — Phase 0 project governance

**Date:** 12 August 2026  
**Scope:** Project B brief review, identity, timing design, agent rules, and phase plan

## What I wanted

Start Project B with a complete reading of the supplied brief and supporting
documentation, preserve continuity with the student's completed Project A, and
turn the main product and experiment decisions into working instructions and a
manageable phase roadmap.

## Prompt(s)

> We are now on Project B of the fins project we did A of. Have a read of the
> docs and brief

After the assistant identified the main requirements and conflicts:

> Yes change to stockist, we will do monthly but lets show experiments with
> daily,weekly, bi weekly as well. Use FINS5545. Next we need the ai prompting
> log as well in this project. But first lets create/update the agents.md with
> what we are doing/need. Create a project phase as well, breakdown the whole
> process into managable phases.

## What the assistant produced

- Read the Project B brief, context, data guide, report outline, deployment
  guide, submission checklist, starter code, brainstorming notes, and relevant
  final Project A documentation.
- Replaced the Project B `AGENTS.md` placeholder with project-specific rules for
  data, calendars, walk-forward testing, optimisation, sentiment, fusion,
  deployment, reporting, reproducibility, and AI transparency.
- Created `ai/PROJECT_PHASES.md`, breaking the complete project into Phases 0–10
  with work items, planned outputs, and completion gates.
- Standardised the working identity on Stockist Funds and FINS5545 in
  student-created planning files.
- Preserved monthly rebalancing as the primary assignment-compliant fund design
  and classified daily, weekly, and bi-weekly runs as sensitivity experiments.
- Established coverage-aware finance sentiment as the preferred continuation of
  the student's Project A coverage-confidence innovation.
- Updated the pre-existing brainstorming notes to use Stockist Funds and to
  distinguish the primary monthly fund from higher-frequency diagnostics.

## What was wrong or risky

- The supplied `PROJECT_BRIEF.md` identifies FINS3645, while the student's final
  Project A record confirms FINS5545. Editing the supplied brief would obscure
  its provenance, so the assistant preserved it and used FINS5545 only in
  student-created files.
- The brainstorming notes changed the established product name from Stockist
  Funds to Harbour Signal without a stated reason. This would weaken continuity
  between Parts A and B, so the student chose Stockist Funds.
- The brief specifies monthly or less frequent rebalancing for the backtested
  funds. Daily, weekly, and bi-weekly schedules could appear non-compliant if
  presented as the main product. They were therefore retained only as clearly
  labelled robustness experiments; monthly remains the default and anchors the
  required results, fact sheets, app, and conclusions.
- Frequent rebalancing can appear better before costs while creating excessive
  turnover. The roadmap requires matched comparisons, turnover measurement, and
  gross versus cost-adjusted results.
- A finance lexicon and coverage-confidence formula can be overfit after seeing
  returns. The instructions require a disclosed, reviewable lexicon and a
  pre-specified or prior-only fusion design.
- This phase defines a target direction, not an empirical conclusion. No claim
  is made yet that finance-adjusted or coverage-aware sentiment improves fund
  performance.

## Checks performed

- Read repository, `fins2026/`, and project-local instructions in scope.
- Read the full Part B requirements, marking rubric, mandatory requirements,
  data dictionary, and deployment appendix.
- Confirmed the four exact marker-facing output filenames.
- Reviewed the Project B starter modules and confirmed that portfolio,
  sentiment, fusion, pipeline, app, and substantive tests are still placeholders.
- Reviewed the final Project A instructions, audit, product identity,
  coverage-confidence design, and visual system for continuity.
- Kept `PROJECT_BRIEF.md`, all files under `context/`, `src/data_access.py`, and
  `ai/prompt_log_template.md` unchanged.
- Checked the new instructions against the brief's no-look-ahead, calendar,
  annualisation, app-artifact, Word-report, public-repository, and AI-log rules.
- Searched the working Project B files for unintended Harbour Signal branding
  after the update; the only retained mention is this audit trail explaining the
  corrected naming conflict.

## What I changed and why

The student explicitly chose Stockist Funds, FINS5545, a monthly primary
specification, and additional high-frequency experiments. The assistant turned
those choices into operational safeguards so later code and reporting do not
silently drift. The assistant also connected the new sentiment work to the
student's existing coverage-confidence framework, providing a coherent
innovation story rather than adding an unrelated feature.

## Student review still required

- Approve the final fund menu and which methods are user-facing rather than
  benchmarks or diagnostics.
- Approve the estimation-window length, weight caps, risk-free-rate assumption,
  and transaction-cost scenarios before Phase 2.
- Approve the exact coverage-confidence equation and finance-lexicon entries
  before they are used in the reported fusion test.
- Review and rewrite any later report interpretations and recommendations in the
  student's own voice.
