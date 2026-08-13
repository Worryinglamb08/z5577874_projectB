# Stockist Funds — Project B Instructions

These instructions apply to all work inside
`fins2026/z5577874_projectB/`. Repository-level and `fins2026/`
instructions also apply. `PROJECT_BRIEF.md` is the authoritative assignment
specification; read it and the supplied files under `context/` before making
substantive changes.

## Project identity and purpose

- Course: **FINS5545 Financial Market Data Design & Analysis**.
- Product: **Stockist Funds**, continuing the student's own Project A product.
- Audience: self-directed investors seeking transparent, systematic,
  multi-asset funds and inspectable evidence about risk and news-signal quality.
- Scope: Project B completes Data Factory Floor Stations 3 and 4 by building
  out-of-sample funds, sentiment analytics, a structured/unstructured-data
  fusion, and a deployed Streamlit investment app.
- Do not edit the supplied brief to resolve its FINS3645/FINS5545 label
  conflict. Use FINS5545 in student-created reports, app copy, metadata, and
  project documentation, while preserving the source brief unchanged.

The central product question is:

> Can Stockist Funds turn the student's Project A data foundation into
> transparent systematic funds, and does a coverage-aware finance-news signal
> add useful out-of-sample information after risk, turnover, and implementation
> costs are considered?

## Continuity with Project A

- Reuse only the student's own work in `../z5577874_projectA/`; do not inspect
  or copy another student's project.
- Preserve Project A's validated data rules, Stockist Funds identity, visual
  language, and coverage-confidence definitions where they remain appropriate.
- Part B must be independently runnable from its own folder. Do not import code
  at runtime from the Project A folder. Port or adapt required student-owned
  logic into Project B and test it here.
- Preserve the Part A findings as context, not as Part B performance evidence.
  Fund, sentiment, and fusion claims must trace to Part B outputs.
- The preferred original extension is a **coverage-aware finance-sentiment
  signal**. It should use the Project A coverage evidence to qualify sentiment
  when coverage is thin or concentrated, rather than treating every sector-day
  score as equally reliable.

## Analytical scope and fund menu

Build a user-facing menu in which each `(asset family, method)` pair is one
investable fund with its own fact sheet.

Target asset families:

- equity-only;
- crypto-only on the native seven-day calendar; and
- combined equity-plus-crypto on the observed equity trading calendar.

Target methods should include transparent equal-weight benchmarks and several
genuine portfolio rules, such as minimum variance, risk parity, and a carefully
validated maximum-Sharpe method. Do not present two methods as different unless
their objective, constraints, and resulting weights are demonstrably different.

The approved default menu contains 15 monthly funds: equity-only, crypto-only,
and combined families, each implemented with Equal Weight, Minimum Variance,
Risk Parity, Maximum Sharpe, and Hierarchical Risk Parity. Equal Weight is the
transparent benchmark. HRP is positioned as a cluster-diversified, lower-risk
alternative and must not be described as outperforming Risk Parity.
Coverage-aware sentiment is evaluated as an extension and is not silently mixed
into the base fund menu.

Every fact sheet must include growth of $1, annualised return, annualised
volatility, Sharpe ratio, maximum drawdown, and current target holdings. Add
turnover, concentration, benchmark-relative performance, and estimated trading
costs where the implementation supports them.

## Backtest and timing rules

- Use a walk-forward out-of-sample historical simulation. At every decision
  date, estimates and weights may use only observations strictly before the
  first return earned under those weights.
- State the estimation-window length, first live date, rebalance rule, holding
  period, risk-free-rate assumption, transaction-cost assumption, constraints,
  missing-value treatment, and annualisation convention.
- The **primary investable specification is monthly rebalancing**, satisfying
  the brief's monthly-or-less-frequent rule. The monthly schedule must anchor
  the required performance table, fact sheets, app, and headline conclusions.
- Also run daily, weekly, and bi-weekly retraining/rebalancing as explicitly
  labelled **sensitivity experiments**. They test noise sensitivity, turnover,
  and cost drag; they do not replace the assignment-compliant monthly backtest
  or become the default app funds.
- Compare schedules on the same eligible assets, estimation window, live
  sample, method, constraints, and cost assumptions so frequency is the intended
  difference.
- Report gross and transaction-cost-adjusted experimental results when feasible.
  Never call a higher-frequency result investable without discussing turnover,
  costs, and the brief's required baseline.
- Use `252` observations per year for equity-only and combined funds on the
  equity calendar. Use `365` for crypto-only funds on their native calendar.
- Compute asset returns on native calendars before alignment. Never merge price
  levels and difference them afterward. Never forward-fill missing returns.
- For combined funds, already-computed crypto returns are left-aligned to the
  equity trading calendar. Explain exactly what the retained crypto return
  interval represents.
- Use adjusted close for returns, cap raw observations at 2023-12-31, and do not
  claim evidence beyond the supplied 2020–2023 sample.
- Use long-only, fully invested weights unless a different constraint is
  explicitly motivated and tested. Validate the sum, bounds, finite values, and
  concentration of every weight vector.
- Optimisation success flags are not sufficient evidence. Check objective
  scaling, constraint residuals, weight variation through time, and whether
  ostensibly different methods collapse to the same solution.
- Do not tune a rule on the full out-of-sample period and then report that same
  period as untouched evidence. Any hyperparameter selection needs a prior-only
  rule, nested validation, or an honest in-sample/sensitivity label.

### Approved default model configuration

Keep these settings in one typed configuration object and pass them explicitly
to modelling functions. Do not scatter numeric constants through the code.

- Equity and combined estimation window: 252 observed equity trading days.
- Crypto-only estimation window: 365 native crypto calendar days.
- Primary rebalance schedule: monthly.
- Diagnostic schedules: daily, every 5 trading days, and every 10 trading days.
- Risk-free rate: 0% per year.
- Equity individual-asset cap: 10%.
- Crypto individual-asset cap: 25%.
- Combined total crypto-sleeve cap: 30%.
- HRP rule: single-linkage clustering on correlation distance followed by
  recursive variance bisection; retain raw weights when feasible and record any
  projection required by the approved caps.
- Base one-way trading-cost assumption: 10 basis points applied to portfolio
  turnover at each rebalance.
- Trading-cost sensitivities: 5 and 25 basis points.

Alternative values may be tested through configuration-driven sensitivity runs,
but the defaults above anchor the primary tables, figures, fact sheets, app, and
report unless the student approves and documents a change.

## Sentiment and coverage-confidence rules

- Use headlines only; never imply that the dataset contains article bodies.
- Preserve casing, punctuation, negation, and other text features required by
  VADER. Document all transformations and lexicon changes.
- Build and retain a plain-VADER baseline before applying a disclosed
  finance-specific lexicon. Every added term and score must be reviewable.
- Deduplicate news on `ticker`, original date, and title. Align each headline to
  the same or next observed equity trading day, retaining both dates.
- Aggregate headline scores to ticker-day first, then construct each sector-day
  index by equal-weighting its constituent ticker scores as required by the
  brief. Define and justify the treatment of ticker-days with no headlines.
- Lag every tradable sentiment signal by at least one observed trading day. A
  headline aligned to day `t` may first affect a decision on day `t+1`.
- The coverage-aware extension must be constructed from contemporaneously
  available or prior information. Define its equation and the treatment of
  zero-news days, thin breadth, concentrated coverage, and missing values.
- Keep raw sentiment, coverage confidence, and the final confidence-adjusted
  signal separately available so the effect of each layer can be audited.
- Validate the sentiment model with reproducible diagnostics such as neutral
  share, sign changes under the finance lexicon, hand-reviewed headline cases,
  sector coverage, and sensitivity to missing-news treatment.
- Treat headline sentiment as a noisy proxy. A fusion that fails to improve
  returns is a valid result and must not be hidden or retrospectively tuned away.

The approved starting confidence measure is:

```text
confidence = breadth * (1 - HHI) / (1 - 0.20)
```

where `breadth` is covered sector constituents divided by five and `HHI` is the
headline-share concentration across the five sector constituents. Clip the
result to `[0, 1]`; set it to zero on no-news days. Keep breadth, HHI, confidence,
raw finance sentiment, confidence-adjusted sentiment, and the lagged tradable
signal as separate fields. Any later threshold or nonlinear transformation must
be justified without selecting it on the final reported out-of-sample result.

## Fusion and evaluation rules

- Compare, at minimum, an equity base fund with the otherwise-identical
  sentiment-augmented version.
- Apply the lagged signal only to eligible equity weights. Crypto has no supplied
  news and must not receive an invented sentiment score.
- Keep the base method, estimation window, rebalance dates, constraints, cost
  model, and live sample identical in before-versus-after comparisons.
- Define the tilt strength and normalisation rule explicitly. Test that weights
  remain finite, long-only if intended, fully invested, and within caps.
- Evaluate economic magnitude as well as direction: return, volatility, Sharpe,
  maximum drawdown, turnover, concentration, and cost-adjusted performance.
- Separate confirmatory results from exploratory sensitivity analysis. Report
  negative and null findings candidly.

## Data and source protection

- Load raw data only through `src/data_access.py`; do not edit that supplied
  helper without an unavoidable, documented reason.
- Never commit or submit the raw ZIP, Parquet files, secrets, credentials, local
  caches, or absolute laptop paths.
- Do not edit supplied files in `context/` or `ai/prompt_log_template.md`.
- Copy cached input frames before transformation so source objects are not
  mutated.
- Record the source, transformation, calendar, sample, schema, and purpose of
  every derived dataset.
- Every reported number must trace to a reproducible Part B calculation or a
  verified source. Never invent citations, events, statistics, data definitions,
  or findings.

## Code, tests, and reproducibility

- Keep reusable logic in `src/`. Keep `scripts/run_part_b.py` a thin,
  deterministic, end-to-end orchestrator.
- Keep the routine build monthly-only. Preserve and validate the completed
  daily/every-5-day/every-10-day comparison artifacts as frozen diagnostic
  evidence; do not recompute those slow paths in `scripts/run_part_b.py`.
- Resolve paths from the Project B directory rather than the caller's current
  working directory.
- Prefer small functions with type hints, clear docstrings, explicit inputs and
  outputs, and no hidden global state.
- Use deterministic seeds for any stochastic operation and stable ordering for
  tickers, funds, sectors, dates, and artifacts.
- Do not add dependencies casually. Update `requirements.txt` for deployed app
  packages or `requirements-dev.txt` for build-only packages before installing.
- Test financial calculations with synthetic examples and hand calculations.
  Tests must cover calendar alignment, rebalance timing, absence of look-ahead,
  optimiser constraints, metric annualisation, drawdown, turnover, sentiment
  lagging, no-news handling, coverage confidence, fusion normalisation, output
  schemas, and important edge cases.
- Add an explicit temporal leakage test proving that changing future returns or
  future headlines cannot change an earlier decision weight or signal.
- Do not mark a phase complete just because the code runs. Inspect whether
  outputs are financially sensible and reconcile key values independently.

Run from the main repository root with its interpreter:

```bash
./.venv/bin/python fins2026/z5577874_projectB/scripts/run_part_b.py
./.venv/bin/python -m pytest -q fins2026/z5577874_projectB/tests
./.venv/bin/python -m ruff check fins2026/z5577874_projectB
./.venv/bin/python fins2026/z5577874_projectB/scripts/check_handin.py
```

## Output contract

Save generated artifacts only beneath `results/data/`, `results/tables/`, and
`results/figures/`. The following marker- and app-facing filenames are fixed:

- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/data/sector_sentiment_index.csv`
- `results/tables/performance_metrics.csv`

Additional machine-readable artifacts should use lowercase `snake_case` names.
Keep final report figures as self-contained, Word/A4-ready PNGs, with caption or
evidence sidecars where useful. The pipeline must validate required schemas and
must not silently leave stale outputs from an earlier run.

Required Part B evidence includes:

- performance metrics across funds and methods;
- growth of $1 across methods;
- drawdown for at least one fund;
- weights through time across methods for at least one family;
- Sharpe or return-versus-risk comparison;
- sector sentiment through time; and
- fusion before-versus-after as both a table and figure.

## App rules

- `streamlit_app.py` is the root entrypoint and represents Stockist Funds.
- The app must support the complete investor journey: compare funds, inspect a
  fund fact sheet and current holdings, set an allocation across funds, and
  inspect sentiment and coverage confidence.
- The deployed app reads committed precomputed artifacts from `results/`. It
  must not rerun backtests, score VADER, import NLTK, or require raw data to
  render the main investor experience.
- Keep app dependencies in `requirements.txt` and build-only dependencies such
  as NLTK in `requirements-dev.txt`.
- Cache file loading where useful, keep interactions responsive on Streamlit's
  basic tier, and provide clear empty/error states.
- Preserve the accessible, modern-minimal Stockist Funds visual system from
  Project A: calm neutral surfaces, dark ink, restrained teal accent, readable
  comparisons, and warnings that do not rely on colour alone.
- Label all performance as historical out-of-sample simulation, show the sample
  period, and avoid promises, personalised advice, or future-return claims.

## Report and academic ownership

- The editable source is `report/report.docx`; submit `report/report.pdf`.
- Maximum written narrative is about 5,000 words and 10 pages, excluding the
  appendix and references, as specified in the brief.
- Write for a financially literate, non-technical investor. Define methods
  precisely, then interpret their economic meaning in plain language.
- Every figure and table must be referenced and interpreted, with a caption,
  labels, units, sample period, and source/transformation note.
- Include the funds and backtest design, fund results and fact sheets, sentiment
  index, fusion and innovation, app journey, limitations, critical reflection,
  and three concrete real-world recommendations.
- The student owns the final wording, economic interpretation, product choices,
  and recommendations. AI may help build, organise, calculate, test, critique,
  and edit, but AI-generated prose must be reviewed and rewritten in the
  student's own voice.
- Verify every citation by opening the source. If a claim or citation cannot be
  verified, remove it or label the uncertainty.

## AI workflow and prompt logs

- AI workflow evidence is graded. Maintain curated Markdown records under
  `ai/` for every material AI-assisted phase or decision.
- Treat `ai/prompt_log_template.md` as protected: do not edit, rename, move, or
  overwrite it. Create numbered records such as
  `ai/001_phase_0_project_governance.md`.
- Each record must include the goal, the user's actual prompt(s), what the
  assistant produced, errors or risks, checks performed, student decisions and
  corrections, and review still required.
- Record rejected advice, look-ahead risks, solver failures, negative results,
  and course-rule conflicts as well as successful outputs.
- Keep the account candid about what AI produced and what the student chose,
  checked, corrected, interpreted, or wrote independently.

## Definition of done

Project B is complete only when:

- the pipeline runs end to end from the hosted source and regenerates all
  declared artifacts;
- tests, lint, temporal-leakage checks, schema checks, and reproducibility checks
  pass;
- the monthly primary funds, fact sheets, sector sentiment index, coverage-aware
  fusion, and all required exhibits exist and have been reviewed;
- daily, weekly, and bi-weekly experiments are clearly labelled and do not
  displace the monthly primary specification;
- the Streamlit app runs locally from precomputed artifacts and completes the
  investor journey;
- report DOCX and PDF reconcile to generated outputs and remain within the brief;
- the AI workflow pack accurately documents the collaboration;
- `scripts/check_handin.py` reports no failures;
- no raw data, secrets, caches, temporary files, or unverified claims remain;
- the Project B folder is its own GitHub repository, is public at hand-in, and
  the live Streamlit URL works while logged out.
