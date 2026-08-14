---
name: mark-project-b
description: Mark a FINS5545/FINS3645 Project B submission or work-in-progress against the Part B rubric in PROJECT_BRIEF.md. Use when asked to grade, mark, assess, moderate, predict a band, identify rubric gaps, or perform a pre-submission review. Require file-backed evidence, reward demonstrated technique and innovation, expose material weaknesses, and resist grade inflation or yes-man conclusions.
---

# Mark Project B

Assess the project as a strict but constructive independent marker. Treat the
brief as the authority and the repository as evidence. Never award marks for
plans, claims, or intended deployment that cannot be verified.

## 1. Establish the marking contract

1. Read `PROJECT_BRIEF.md` completely enough to locate:
   - Part B requirements and common mistakes;
   - required exhibits and exact output filenames;
   - Station 4 and deployment requirements;
   - the Part B rubric and mandatory AI rules.
2. Extract the current rubric wording before inspecting the solution. The
   brief wins if criterion names or weights change.
3. Confirm that the weights total 100. The expected current weights are:
   - Funds and OOS backtest: 15%;
   - Sentiment index and fusion: 10%;
   - Innovation and data-driven results: 30%;
   - Streamlit app and implementation: 15%;
   - Economic interpretation, reflection and writing: 10%;
   - AI workflow and transparency: 20%.
4. State whether the assessment is a current-state review or final-submission
   mark. Default to current state. Do not project credit for unfinished work.

## 2. Apply evidence rules

Use this evidence hierarchy:

1. Executed tests, reproducibility checks, generated artifacts and a reachable
   deployment.
2. Source code and artifact schemas that directly demonstrate the method.
3. Report text that interprets the verified results.
4. AI logs that show prompts, corrections, decisions and critical reflection.
5. Plans, brainstorming and proposed features: context only, never completion
   evidence.

For every material positive or deduction, cite a file, test result, artifact,
URL, or explicitly state that evidence is absent. Distinguish:

- implemented and verified;
- implemented but not independently verified;
- documented only;
- missing.

Do not infer correctness from filenames, file counts, polished UI, or passing
smoke tests alone. Do not infer strong writing from an outline or AI-authored
draft. Treat unverified live URLs and private repositories as not deployed for
marking purposes.

## 3. Inspect the project

### Funds and backtest

Verify rather than merely locate:

- equity, crypto and combined families;
- several methods and one fact sheet per family-method fund;
- walk-forward weights formed only from trailing data;
- first live date after the estimation window;
- one-period execution lag or equivalent no-look-ahead construction;
- correct 252-day equity/combined and 365-day crypto annualisation;
- growth of $1, drawdown, metrics and weights-over-time evidence;
- required filenames and internally consistent metrics;
- turnover and cost treatment if claimed.

Trace at least one return and one rebalance through code or a hand-check table.

### Sentiment and fusion

Verify:

- headline scoring and ticker-day/sector aggregation;
- treatment of ticker-days without headlines;
- at least one trading-day lag before the signal affects a portfolio;
- sector time-series coverage;
- validation of the standalone index;
- before-versus-after fusion table and figure;
- critical assessment, including a negative or weak result when applicable.

### Innovation

Reward originality only when it is motivated, implemented, tested, reported and
interpreted. Feature quantity is not innovation quality. Standard equal weight,
minimum variance, maximum Sharpe, risk parity, VADER and a routine Streamlit
dashboard are baseline work.

Potential extensions can earn credit when evidenced: HRP or another defensible
portfolio method, finance-lexicon expansion with validation, a look-ahead-safe
coverage-aware signal, robust evaluation, a coherent original visual system,
or a genuinely useful investor feature. Failed or non-promoted prototypes can
still earn credit when the decision and evidence are clear.

Do not double-count one extension at full value across multiple criteria.
Innovation may strengthen another criterion, but explain the overlap.

### App and implementation

Run every available page test and inspect the actual investor journey:

- compare funds;
- open complete fund details/fact sheets;
- set a hypothetical allocation;
- inspect sentiment analytics;
- load precomputed artifacts without running backtests or VADER in the app;
- behave responsively and fail clearly when artifacts are unavailable.

Verify `streamlit_app.py` is at the repository root. For final-state marking,
verify both the public GitHub repository and live Streamlit URL. A polished
local app is not a deployed app.

### Writing and reflection

Inspect the actual submitted report, preferably `report/report.pdf` and its
editable source. Check:

- evidence-based economic explanation rather than output narration;
- every exhibit is referenced and interpreted;
- what worked, what failed and why;
- three concrete real-world recommendations;
- target user and customer journey;
- citations, word/page constraints and the student's own voice.

If no readable report is present, do not award writing marks based on code,
plans or AI logs.

### AI workflow

Inspect the actual agent/instruction files and curated logs. Reward evidence of
student steering, corrections, rejected ideas, validation and reflection.
Do not reward log volume by itself. Repetitive implementation summaries without
the prompts, AI errors, student corrections or reasons do not meet the HD
descriptor. Apply the brief's mandatory cap if the required files are absent.

## 4. Run verification

Use repository-native commands where available. Prefer:

```bash
python scripts/check_handin.py
python scripts/check_reproducibility.py
python -m pytest -q
python -m ruff check .
```

Use the repository interpreter. Record failures, skips, network constraints and
whether tests cover financial correctness or only rendering. Do not silently
discount a project for an unavailable network service, but do not call an
unexecuted check passed.

## 5. Score without inflation

Assign each criterion an integer score out of 100 using the rubric band first,
then calculate:

`weighted contribution = criterion score × criterion weight / 100`

Sum contributions for the overall mark. Report the UNSW band:

- HD: 85–100
- D: 75–84
- C: 65–74
- P: 50–64
- F: below 50

Use these guardrails:

- Missing readable report: writing criterion cannot exceed 49.
- Missing verifiable deployment at final/current snapshot: app criterion cannot
  exceed 64, even if the local UI is strong.
- Private repository at hand-in: apply the app penalty specified by the brief.
- Missing mandatory agent/instruction files or prompt logs: apply the rubric's
  AI cap.
- Unresolved look-ahead, annualisation or calendar errors can move Funds or
  Sentiment into P/F regardless of presentation quality.
- Required outputs that merely exist but are not self-contained or interpreted
  do not satisfy the top descriptor.
- Reserve 90+ for unusually complete evidence with no material rubric gap.

When evidence is ambiguous, score the demonstrated lower band and state what
would raise confidence. Avoid false precision: whole-number criterion scores
are enough.

## 6. Produce the marking report

Write the result in this order:

1. **Provisional overall mark and band** — label current-state limitations.
2. **Weighted rubric table** — criterion, weight, score, contribution, band,
   and one-sentence evidence basis.
3. **What deserves credit** — the strongest techniques and genuine innovations.
4. **Material deductions** — ordered by mark impact, with evidence and the
   applicable rubric language.
5. **Criterion-by-criterion findings** — include what is verified, uncertain,
   and missing.
6. **Highest-value next actions** — no more than seven, ordered by expected mark
   gain and dependency.
7. **Verification record** — commands run, pass/fail status, deployment checks
   and files inspected.
8. **Confidence statement** — identify what could materially change the mark.

Be candid and specific. Praise only demonstrated strengths. Explain deductions
without softening them, but distinguish fixable delivery gaps from fundamental
method errors.
