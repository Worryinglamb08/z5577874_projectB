# Project B current-state marking report

**Assessment date:** 14 August 2026  
**Assessment type:** Current-state review, not a final submitted-grade guarantee  
**Rubric authority:** `PROJECT_BRIEF.md`, Part B criteria and mandatory requirements  
**Marker approach:** Evidence-led and deliberately conservative where a required deliverable is unfinished

## Provisional result

**91/100 — High Distinction**

The analytical project is already at HD standard in funds, sentiment, and
innovation. The app is deployed, its Sharing setting records it as public and
searchable, and the student has confirmed successful access from an incognito
browser. The earlier command-line redirect was therefore an unreliable access
test, not evidence that the app was private. The GitHub repository is also
public, and the final Version 7 PDF is present with the corrected five-fund and
143-test statements. Remaining deductions concern final commit synchronisation,
minor AI-audit polish, and formal user-testing evidence rather than a discovered
modelling or delivery failure.

The unrounded weighted result is **91.05**.

## Weighted rubric assessment

| Criterion                                     |   Weight | Score | Contribution | Band   | Evidence basis                                                                                                                                                                                                                              |
| --------------------------------------------- | -------: | ----: | -----------: | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Funds: Optimal Portfolios & OOS Backtest      |      15% |    93 |        13.95 | HD     | Fifteen funds across three families and five methods, prior-only walk-forward weights, correct 252/365 conventions, complete fact-sheet artifacts, temporal tests, and reconciled outputs.                                                  |
| Sentiment Index & Fusion Extension            |      10% |    92 |         9.20 | HD     | Validated ticker-day and sector-day construction, explicit neutral-zero handling, one-observed-day lag, coverage-aware fusion, controlled sensitivities, and a candid negative result.                                                      |
| Innovation & Data-Driven Results              |      30% |    91 |        27.30 | HD     | HRP, the reviewed finance lexicon, coverage-aware fusion, frequency/cost analysis, controlled rejected prototypes, custom design system, and investor-facing inspection features are implemented and evidenced rather than merely proposed. |
| Streamlit App & Implementation                |      15% |    92 |        13.80 | HD     | The complete precomputed-data journey is publicly deployed from a verified public GitHub repository and provides polished, original, tested UX across every required investor task.                                                         |
| Economic Interpretation, Reflection & Writing |      10% |    88 |         8.80 | HD     | The final 21-page Version 7 PDF contains strong interpretation, honest negative findings, and specific recommendations; the narrative is followed by excluded references and evidence appendices.                                           |
| AI Workflow & Transparency                    |      20% |    90 |        18.00 | HD     | The custom `AGENTS.md`, extensive logs, and student-written `AI_Notes.md` show prompts, mistakes, corrections, rejected ideas, student steering, and candid reflection on AI's limits.                                                      |
| **Total**                                     | **100%** |       |    **91.05** | **HD** | Current-state mark.                                                                                                                                                                                                                         |

## What deserves credit

### Methodological technique

- The portfolio work is genuinely walk-forward. In
  [`src/portfolios.py`](../src/portfolios.py), each rebalance estimates from a
  trailing window ending before the first held return. The saved
  [`fund_weights.csv`](../results/data/fund_weights.csv) contains 540 dated
  target vectors with `estimation_end < first_held_return_date`; all vector sums
  are within approximately `5.4e-11` of one.
- The project correctly separates the 252-day equity/combined calendar from the
  365-day native crypto calendar. The first live dates follow the required
  252- or 365-observation estimation windows.
- Turnover is based on drifted pre-trade weights rather than repeatedly
  comparing targets with an artificial zero portfolio. Trading costs are
  explicitly applied and reported.
- The full test suite includes future-data perturbation tests for portfolio
  weights, sentiment signals, and fusion. This is much stronger evidence than a
  narrative claim of “no look-ahead”.

### Sentiment and fusion

- [`src/sentiment.py`](../src/sentiment.py) preserves VADER-relevant text,
  distinguishes no news from observed neutral language, equal-weights five
  ticker-day values per sector, and creates the tradable lag within each sector.
- The coverage confidence calculation preserves breadth, HHI, raw finance
  sentiment, adjusted sentiment, and the lagged value as separate auditable
  fields. It is not mislabeled as forecast accuracy.
- [`src/fusion.py`](../src/fusion.py) reuses the same base method, sample,
  rebalance dates, constraints, and cost model. The main result is not tuned
  away: Sharpe falls from 0.504 to 0.453 while maximum drawdown becomes 0.77
  percentage points shallower.
- The Utilities and Technology event reviews in
  [`SENTIMENT_EVENT_AUDIT.md`](SENTIMENT_EVENT_AUDIT.md) test conspicuous chart
  movements and acknowledge cross-ticker repetition and mixed-language errors.

### Genuine innovation

The innovation score is not based on feature count. The strongest coherent
contribution is the combination of:

1. an auditable finance-specific lexicon with blinded scoring evidence and a
   later student-review layer;
2. a coverage-aware, look-ahead-safe news signal with its equation and failure
   mode exposed;
3. controlled portfolio-method research in which HRP is promoted after testing,
   while Effective Bets, Black–Litterman, Ledoit–Wolf, and Minimum CVaR remain
   documented prototypes when their evidence does not justify inclusion; and
4. an original visual and interaction system that helps a user inspect holdings,
   sectors, allocation changes, benchmarks, overlap, and signal evidence.

The negative prototype decisions are valuable because the project does not
selectively add whichever method happens to produce the highest historical
return.

### App implementation

- The root [`streamlit_app.py`](../streamlit_app.py) is a thin entrypoint.
- The deployed code path reads precomputed CSV artifacts; it does not import the
  optimiser, the raw-data loader, NLTK, or VADER.
- All four required investor tasks are implemented: compare funds, inspect a
  fact sheet and holdings, set an allocation, and inspect news analytics.
- The app has substantially more than a template dashboard: exact-date benchmark
  alignment, shareable state, complete downloads, sector allocation, allocation
  history, a keyboard-accessible segmented allocation control, clear evidence
  limitations, and a coherent Stockist visual system.
- Thirty focused app and chart tests pass. Public GitHub access, Streamlit's
  public-and-searchable setting, and a successful incognito session establish
  deployment. Automated checks still do not establish customer comprehension.

### AI transparency

[`AGENTS.md`](../AGENTS.md) is a detailed, project-specific instruction file,
not the supplied placeholder. The logs are unusually candid about implementation
errors, visual failures, rejected approaches, and negative results. Examples
include the Streamlit session-state bug, dark-theme failure, incorrect fusion
normalisation guard, mis-anchored sensitivity deltas, and the decision not to
promote CVaR or Ledoit–Wolf. The logs also preserve direct student decisions,
including requests to audit anomalous sentiment periods and to reject
asset-specific covariance models.

## Material deductions

### 1. The latest local state is not yet frozen in the public repository

The app has been deployed at
[`z5577874projectb.streamlit.app`](https://z5577874projectb.streamlit.app/?view=Overview),
and the supplied Streamlit Sharing screenshot records “This app is public and
searchable.” The student also confirmed successful access in an incognito
browser. A command-line request returned an authentication redirect, but that
method produced a false negative and is not used as evidence of app privacy.

The repository at
[`github.com/Worryinglamb08/z5577874_projectB`](https://github.com/Worryinglamb08/z5577874_projectB)
returns HTTP 200 to a logged-out request and is explicitly labelled `Public` by
GitHub. This satisfies the visibility requirement.

The local working tree nevertheless contains an untracked `report/report.pdf`,
the moved lexicon-review tables, the new marking report, and other recent source
changes. These are not yet proven to be the exact state served by Streamlit or
available in the public repository. This is a final synchronisation risk, not a
deployment failure.

### 2. The PDF is present; source and visual close-out remain

- [`report/report.pdf`](../report/report.pdf) is a valid 21-page PDF titled
  `Stockist Funds: Project B Version 7`.
- Extracted PDF text confirms that the earlier stale statements were corrected:
  it now says five selectable monthly funds and 143 tests.
- The narrative is followed by references and evidence appendices, which are
  excluded from the brief's approximate ten-page narrative limit.
- The local `report/` folder no longer contains the editable Word source named
  `report/report.docx`, even though the brief describes it as the editable
  source. The PDF is the actual submission deliverable, but retaining the final
  Word source in the Moodle ZIP would improve traceability.
- A page-by-page visual inspection is not independently recorded in this audit.

The content itself is strong: it interprets risk-return trade-offs, reports the
failed fusion honestly, states limitations, and gives three specific
recommendations. Version 7 is treated as the materially revised final report,
not as the untouched initial AI draft.

### 3. Only hand-in cleanup remains

The review CSVs have been moved to `results/tables/`. A fresh
`scripts/check_handin.py` run reports **22 checks passed, no failures**, and one
non-blocking reminder to remove generated `__pycache__` and `.pyc` files before
zipping.

### 4. The AI synthesis is present; two audit details need attention

[`AI_Notes.md`](AI_Notes.md) is a concise student-written synthesis of where AI
accelerated the work, where outputs required correction, and why tests, visual
checks, and investor-centred judgement remained necessary. This completes the
main missing AI-workflow requirement.

Two smaller issues remain. The note says early AI suggestions “introduced timing
and look-ahead issues,” while the curated logs clearly evidence look-ahead
safeguards but do not identify a concrete AI-introduced leakage bug. Unless a
specific incident can be cited, “created timing and look-ahead risks” would be
more precisely supported.

### 5. Human usability evidence remains limited

The app has extensive automated tests and many student-driven visual
corrections, but [`PHASE_7_USER_TEST.md`](PHASE_7_USER_TEST.md) and the phase
roadmap do not establish a completed fresh-user comprehension test. This matters
because automated tests cannot prove that a new investor understands turnover,
coverage confidence, historical status, or the allocation lab.

## Criterion-by-criterion findings

### Funds — 93/100, HD

**Verified:** 15 funds; equity, crypto, and combined families; Equal Weight,
Minimum Variance, Risk Parity, Maximum Sharpe, and HRP; 13,005 return rows; 21,600
weight rows; 36 monthly rebalances per fund; correct calendar annualisation;
required metrics; holdings; growth, drawdown, method comparison, and
weights-through-time evidence; trading-cost and turnover treatment; no temporal
violations in the saved diagnostics.

**Why not higher:** The live evidence is only 2021–2023, Maximum Sharpe remains
estimation-sensitive, and the final report/package has not yet been reconciled
to the last app changes. These limitations are mostly acknowledged rather than
method errors.

### Sentiment and fusion — 92/100, HD

**Verified:** 146,836 scored clean headlines; a 50,300-row ticker-day panel; a
10,060-row, ten-sector index; explicit no-news policy; exact five-ticker sector
aggregation; one-day observed-calendar lag; bounded scores; standalone and
fusion validation; before/after table and figure; sensitivity at fixed tilt
strengths; preserved negative conclusion.

**Why not higher:** The lexicon panel is AI-heavy and not equivalent to an
independent human-labelled validation sample. Token rules remain vulnerable to
context and repeated headlines. The report appropriately acknowledges this,
but it limits claims about classification accuracy.

### Innovation — 91/100, HD

**Verified:** Multiple extensions are motivated, implemented, tested, and
interpreted. The strongest work is the coverage-aware signal, reviewed finance
lexicon, disciplined method-prototype process, HRP promotion, frequency/cost
analysis, and the inspectable investor interface.

**Why not higher:** Some breadth comes from AI-assisted prototyping, and several
experiments are adjacent robustness studies rather than one externally validated
new economic result. The news extension fails to improve risk-adjusted return,
which still earns credit, but its external validity remains untested.

### Streamlit app — 92/100, HD

**Verified:** Complete local journey, precomputed data path, caching, responsive
layout work, error handling, 30 focused app/chart tests, a deployed URL, a public
and searchable Streamlit Sharing setting, and successful student incognito
access. The GitHub repository independently returns HTTP 200 and is labelled
Public.

**Why not higher:** A formal fresh-user comprehension record remains limited,
and the current uncommitted local changes are not yet proven to match the public
repository and deployed app. The command-line Streamlit redirect is not treated
as a browser-access failure.

### Writing and reflection — 88/100, HD

**Verified in Version 7:** About 4,923 words; clear structure; required exhibits
referenced and interpreted; critical reflection; honest null/negative findings;
three concrete recommendations; zero findings from the repository proofreader.

**Verified in the final PDF:** Valid 21-page Version 7 export, corrected five-fund
and 143-test statements, clear Part B interpretation of fund results,
sentiment/fusion, the app, limitations, and recommendations.

**Remaining uncertainty:** The editable `report/report.docx` source is no longer
present locally, and a page-image visual inspection was not possible in this
environment.

### AI workflow — 90/100, HD

**Verified:** Custom instructions; curated prompts; implementation summaries;
specific AI errors; student corrections and rejected recommendations; transparent
AI-assisted report drafting; honest negative results; preserved research
decisions; and a student-written synthesis in [`AI_Notes.md`](AI_Notes.md).

**Why not higher:** One look-ahead statement should be tied to a specific logged
incident or softened to a documented risk; the deleted log 042 should be restored
unless its removal is intentional and transparently explained; and duplicate log
numbers could be indexed more cleanly.

## Highest-value next actions

1. **Freeze and push the exact final state.** Commit the PDF, moved review
   tables, latest app/tests, and intended AI files, then confirm the public
   GitHub commit matches the deployment and Moodle ZIP.
2. **Retain the editable Word source if available.** Keep the final
   `report/report.docx` in the Moodle ZIP, update fields, and retain the already
   exported PDF.
3. **Record the final logged-out app test.** Check the deployed commit on desktop
   and a narrow screen and record the result.
4. **Remove generated caches.** The hand-in checker now passes all 22 checks and
   leaves only the `__pycache__`/`.pyc` reminder.
5. **Polish the AI audit.** Tighten the unsupported look-ahead wording, restore
   log 042 unless deletion is intentional, and optionally add a short log index.
6. **Run and record one fresh-user session.** Test fund comparison, fact-sheet
   interpretation, allocation, turnover, and coverage confidence without
   coaching; fix material comprehension problems.
7. **Freeze one submission commit.** Rerun the build/hash comparison, full tests,
   Ruff, app smoke test, hand-in checker, and checklist on exactly the commit
   deployed and zipped.

## Verification record

| Check                                                                   | Result                                                                                                                                                                        |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `python -m pytest -q` with the hosted data and VADER resource available | **143 passed** in 805.83 seconds                                                                                                                                              |
| `python -m pytest -q tests/test_app.py tests/test_app_charts.py`        | **30 passed** in 9.92 seconds                                                                                                                                                 |
| `python -m ruff check .`                                                | **All checks passed**                                                                                                                                                         |
| One new full build compared with the saved baseline manifest            | **76 canonical artifacts byte-identical**                                                                                                                                     |
| `python scripts/check_handin.py`                                        | **22 passed, no failures, 1 cleanup reminder**                                                                                                                                |
| Word outline check on `report_v7.docx`                                  | 24 structured headings found                                                                                                                                                  |
| Word proofread check on `report_v7.docx`                                | 0 doubled-word, spacing, reference, or placeholder findings                                                                                                                   |
| Required output filenames                                               | Present and non-empty                                                                                                                                                         |
| Artifact inspection                                                     | 15 funds, 3 families, 5 methods, 540 target vectors, 10 sentiment sectors                                                                                                     |
| Deployed Streamlit URL                                                  | Sharing screenshot says **public and searchable**; student confirms successful incognito access. The command-line redirect was rejected as an unreliable browser-access test. |
| Public GitHub check                                                     | **HTTP 200 and GitHub `Public` label verified**                                                                                                                               |
| Final PDF                                                               | **Valid PDF 1.7, 21 pages, Version 7 title; extracted text says five funds and 143 tests**                                                                                    |
| PDF page-image inspection                                               | **Not independently performed because no local PDF renderer is present**                                                                                                      |

## Confidence statement

Confidence is **high** in the funds, sentiment, code-quality, and reproducibility
scores because they are supported by executed real-data tests, source inspection,
saved diagnostics, and a fresh artifact-hash comparison. Confidence is
**high** in the app and writing scores because public app access, the public
repository, and the final PDF are now evidenced. Visual page inspection and
exact commit synchronisation remain the main uncertainties.

Completing the remaining commit, AI-audit polish, cache cleanup, and hand-in checks
without introducing new defects would consolidate the current provisional HD
position. The final mark must still be based on the exact deployment, PDF, AI
pack, and submission commit that the marker receives.
