# Stockist Funds — Project B Phases

This is the working roadmap for FINS5545 Project B. It breaks the build into
small, auditable phases with an explicit completion gate for each one.
`PROJECT_BRIEF.md` remains the authoritative assignment specification.

## Product direction

**Stockist Funds** continues the student's Project A product for self-directed
investors seeking transparent systematic multi-asset funds. Project B converts
the validated 2020–2023 price and headline foundation into out-of-sample fund
evidence, coverage-aware news analytics, and a lightweight investor app.

The distinctive extension is a coverage-aware finance-sentiment signal:

```text
clean headlines
    -> finance-adjusted headline sentiment
    -> ticker-day and equal-weight sector-day indices
    -> coverage-confidence qualification
    -> one-trading-day lag
    -> equity-weight tilt
    -> before-versus-after out-of-sample evaluation
```

Monthly rebalancing is the primary assignment-compliant product specification.
Daily, weekly, and bi-weekly schedules are diagnostic sensitivity experiments,
not substitutes for the monthly results or the default app funds.

## Phase 0 — Governance, continuity, and experiment design

### Work

- [x] Confirm the continuing product name: Stockist Funds.
- [x] Confirm FINS5545 for student-created outputs while preserving the supplied
      brief unchanged.
- [x] Replace the Project B `AGENTS.md` placeholder with actual working rules.
- [x] Define monthly rebalancing as the primary fund specification.
- [x] Retain daily, weekly, and bi-weekly schedules as clearly labelled
      robustness experiments.
- [x] Select coverage-aware finance sentiment as the main innovation direction.
- [x] Create this phase roadmap and the first curated Project B prompt log.
- [x] Research investor-protection, fund-disclosure, automated-investing, and
      accessibility practices and translate them into an app product brief.
- [x] Research current investment-platform UI patterns and define the proposed
      navigation, visual language, responsive rules, wireframes, and chart system.
- [x] Review and approve the final fund menu, optimiser constraints, cost
      assumptions, and coverage-confidence equation before modelling.
- [x] Adapt the Stockist Funds visual system for the app and Part B exhibits.

### Outputs

- `AGENTS.md`
- `ai/PROJECT_PHASES.md`
- `ai/001_phase_0_project_governance.md`
- `ai/002_phase_0_investment_app_research.md`
- `ai/003_phase_0_ui_design_research.md`
- `ai/APP_PRODUCT_RESEARCH.md`
- `ai/UI_DESIGN_RESEARCH.md`
- updated `ai/PART_B_BRAINSTORMING.md`
- `ai/VISUAL_SYSTEM.md`

### Decisions confirmed 13 August 2026

- Fund menu: 15 monthly funds formed from three families (equity-only,
  crypto-only, and combined) and five methods (Equal Weight, Minimum Variance,
  Risk Parity, Maximum Sharpe, and Hierarchical Risk Parity). HRP was promoted
  after its separately logged exploratory prototype showed a distinct,
  lower-volatility and shallower-drawdown role.
- Equal Weight is the transparent benchmark; coverage-aware sentiment remains a
  separately evaluated extension.
- Default estimation windows: 252 observed equity dates for equity/combined and
  365 native calendar days for crypto-only.
- Default constraints: long-only, fully invested, 10% equity asset cap, 25%
  crypto asset cap, and 30% combined total crypto-sleeve cap.
- Default risk-free rate: zero.
- Default one-way trading cost: 10 basis points applied to rebalance turnover,
  with 5 and 25 basis-point sensitivities.
- Primary timing: monthly. Daily, 5-trading-day, and 10-trading-day schedules are
  diagnostic frequency experiments.
- Starting confidence equation:
  `breadth * (1 - HHI) / (1 - 0.20)`, clipped to `[0, 1]` and set to zero on
  no-news days.
- All values above are central configuration variables. Alternative values may
  be precomputed for sensitivity analysis without rewriting portfolio logic.
- Visual direction: the Project A modern-minimal Stockist Funds system extended
  into the five-destination, light-first app defined in `ai/VISUAL_SYSTEM.md`.

### Completion gate — completed 13 August 2026

The student approved the fund menu, configurable default model settings, primary
and experimental timing rules, innovation definition, transaction-cost
assumptions, confidence equation, and Part A-continuous visual direction.

## Phase 1 — Rebuild and verify the Project A foundation locally

### Work

- [x] Port only the required student-owned ETL, returns, calendar-alignment, and
      headline-alignment logic into Project B.
- [x] Load all raw inputs only through Project B's supplied
      `src/data_access.py`.
- [x] Reproduce the Project A clean row counts and key integrity resolutions.
- [x] Cap crypto at 2023-12-31 and preserve native equity and crypto calendars.
- [x] Compute adjusted-close returns within ticker before cross-asset alignment.
- [x] Rebuild the combined equity-calendar return panel without filling missing
      returns.
- [x] Rebuild the headline trading-day alignment with original and aligned dates.
- [x] Recreate the ticker-day and sector-day coverage features needed by the
      confidence extension.
- [x] Add regression tests against selected Project A artifacts and hand checks.

### Implementation targets

- `src/etl.py`
- `src/features.py`
- a focused coverage-feature module if needed
- Phase 1 tests under `tests/`

### Planned evidence

- local validation tables for row counts, date spans, key uniqueness, alignment,
  and return hand checks;
- a compact schema/provenance table for every model input.

### Completion gate

Project B independently reproduces the required Project A foundation, selected
values reconcile to the student's final Project A outputs, and calendar and
headline-alignment tests pass without importing from the Project A folder.

### Completion gate — completed 13 August 2026

- Project B now owns its ETL, return, alignment, coverage, and Phase 1
  orchestration code; a source scan test prevents a runtime Project A import.
- All 17 frozen reconciliation targets pass, including clean rows, exclusions,
  return counts, panel sizes, alignment statuses, and the NVDA/BTC hand checks.
- The return foundation contains 50,250 valid equity returns and 14,600 valid
  native-calendar crypto returns. The combined panel has 1,006 observed equity
  dates and never fills absent crypto returns.
- Headline alignment produces 134,279 same-day rows, 12,551 next-trading-day
  rows, and 6 explicitly unaligned post-calendar rows. Its complete grids contain
  50,300 ticker-days and 10,060 sector-days.
- The approved breadth/HHI confidence equation is implemented as a distinct
  coverage field, bounded to `[0, 1]` and exactly zero on no-news days; sentiment
  scoring and tradable lagging remain Phase 4 work.
- `20` Project B tests pass, including synthetic financial calculations,
  same/next-date alignment, missing-return behavior, no-news handling, prior-only
  attention, a future-headline leakage test, and real-data regression.

### Evidence generated

- `results/tables/foundation_reconciliation.csv`
- `results/tables/foundation_input_catalog.csv`
- `results/tables/dataset_inventory.csv`
- `results/tables/data_integrity_summary.csv`
- `results/tables/data_schema.csv`
- `results/tables/missing_dates_by_ticker.csv`
- `results/tables/extreme_returns_screen.csv`
- `results/tables/return_hand_checks.csv`
- `results/tables/headline_alignment_summary.csv`
- `results/tables/coverage_panel_summary.csv`
- compact derived samples under `results/data/`

## Phase 2 — Portfolio engine and monthly out-of-sample funds

### Work

- [x] Finalise the fund menu across equity-only, crypto-only, and combined
      families.
- [x] Implement an equal-weight benchmark and several genuine optimisation
      methods, initially minimum variance, risk parity, and maximum Sharpe subject
      to validation.
- [x] Define long-only, fully invested constraints and any asset caps.
- [x] Implement a fixed trailing estimation window and monthly walk-forward
      rebalancing using only information available before each live period.
- [x] Keep crypto-only funds on the native calendar with 365-day annualisation;
      use the equity calendar and 252-day annualisation for equity and combined
      funds.
- [x] Calculate daily fund returns, growth of $1, drawdowns, annualised return,
      annualised volatility, zero-rate or approved risk-free Sharpe, maximum
      drawdown, turnover, concentration, and current target weights.
- [x] Validate solver status, constraint residuals, objective scaling, and
      economically distinct weights.
- [x] Add temporal-leakage tests by perturbing future returns and confirming
      earlier weights do not change.
- [x] Compare optimised funds with their transparent benchmarks.

### Implementation targets

- `src/portfolios.py`
- focused optimiser, backtest, and metric tests under `tests/`

### Required and supporting outputs

- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/tables/performance_metrics.csv`
- planned turnover, concentration, rebalance, and benchmark-comparison tables

### Completion gate

All primary funds run monthly out of sample; weights use prior data only;
metrics and drawdowns reconcile to hand calculations; annualisation matches each
calendar; and methods generate valid, meaningfully different portfolios.

### Completion gate — completed 13 August 2026

- A single immutable `ModelConfig` holds the approved windows, caps, cost,
  schedule, risk-free rate, diagnostics, numerical tolerances, methods, and
  families. `results/tables/model_configuration.csv` records the exact run.
- All 12 `(family, method)` funds run from January 2021 through the final 2023
  observation, after a full 252-observation equity/combined or 365-observation
  crypto history. Every estimation end precedes the return first earned.
- Each fund has 36 first-of-month target rebalances. The 540 total decisions
  passed solver, long-only, full-investment, individual-cap, combined crypto-cap,
  and finite-value checks.
- Holdings drift between monthly decisions. Turnover is measured against the
  drifted pre-trade allocation, initial deployment is one-way turnover of one,
  and the approved 10 basis-point cost is deducted on each rebalance date.
- Net CAGR, annualised volatility, zero-rate Sharpe, maximum drawdown, growth,
  turnover, concentration, current simulated target weights, and equal-weight
  benchmark comparisons are available for every fund.
- All 18 within-family method pairs are economically distinct. Average L1 target-
  weight distances are approximately 1.17 for equity, 0.84 for crypto, and 1.23
  for combined funds; risk-parity contribution dispersion is near zero.
- The primary combined result is not selected retrospectively: risk parity has
  the highest combined net Sharpe (about 0.88), while equal weight has the highest
  combined net CAGR (about 15.0%). Maximum Sharpe has higher turnover and does not
  beat equal weight on net CAGR.
- Combined minimum variance uses very little crypto on average (about 0.7%) and
  sometimes none. This is retained as a genuine optimiser result under the
  approved cap-only design, not hidden or relabelled as a fixed-sleeve fund.
- Synthetic tests reconcile adjusted objectives, annualisation, drift turnover,
  deployment cost, CAGR, and drawdown. A future-return perturbation cannot change
  the earlier target vector. The real-data regression checks all 15 funds.
- Five Word/A4-ready exhibits and caption sidecars pass the selected rendered
  validation checks and were visually inspected after export.
- The Combined allocation-history exhibit compares all five portfolio methods
  using the supplied equity sectors and one aggregated Crypto band; every
  monthly stack sums to 100%.
- An isolated Ledoit-Wolf robustness prototype compares the existing
  sample-plus-ridge covariance with standard linear shrinkage for Minimum
  Variance, Risk Parity, Maximum Sharpe, and HRP across Equity and Combined,
  plus a pre-declared Crypto HRP extension. Its 18 paths and 648 decisions are
  validated. The student rejected production adoption because the family-level
  results were mixed and an asset-family-specific covariance model would reduce
  product consistency. The approved production funds remain unchanged.
- An isolated 95% minimum-CVaR prototype compares tail-loss minimisation with
  Minimum Variance and HRP across all three families. Its nine paths and 324
  decisions pass the weight, timing, solver and artifact checks. CVaR is
  economically distinct, but Minimum Variance has lower realised 95% daily
  CVaR, shallower drawdown and higher Sharpe in every family, so the prototype
  remains outside the primary fund menu.

### Evidence generated

- `results/data/fund_returns.csv`
- `results/data/fund_weights.csv`
- `results/tables/performance_metrics.csv`
- `results/tables/fund_fact_sheets.csv`
- `results/tables/rebalance_diagnostics.csv`
- `results/tables/method_distinctness.csv`
- `results/tables/model_configuration.csv`
- `results/tables/portfolio_validation_summary.csv`
- `results/tables/portfolio_figure_validation.csv`
- `results/figures/fund_growth.png`
- `results/figures/combined_fund_drawdowns.png`
- `results/figures/fund_risk_return.png`
- `results/figures/fund_sharpe_by_family.png`
- `results/figures/combined_weight_history.png`
- matching `.caption.md` sidecars for all five figures

## Phase 3 — Rebalancing-frequency and implementation-cost experiment

### Research question

> Does more frequent retraining improve out-of-sample risk-adjusted performance,
> or mainly amplify estimation noise, turnover, and trading-cost drag?

### Work

- [x] Hold the eligible universe, estimation window, optimiser, constraints,
      live sample, and cost assumptions fixed.
- [x] Rerun the selected fund under daily, weekly, bi-weekly, and monthly
      schedules.
- [x] Label daily, weekly, and bi-weekly results as diagnostic experiments because
      the assignment's primary fund rule is monthly or less frequent.
- [x] Calculate average and cumulative turnover using pre-trade drift where
      implemented, plus gross and cost-adjusted performance.
- [x] Test more than one transparent transaction-cost assumption if useful,
      without selecting the most flattering one after observing results.
- [x] Compare annualised return, volatility, Sharpe, maximum drawdown, cumulative
      return, turnover, concentration, and cost drag.
- [x] Decide whether the evidence supports monthly as the product default.

### Planned outputs

- `results/tables/rebalance_frequency_metrics.csv`
- `results/figures/rebalance_frequency_tradeoff.png`
- supporting turnover/cost artifacts as needed

### Completion gate

The schedule comparison changes only rebalance frequency, distinguishes gross
from net results, and supports an honest product decision without presenting the
high-frequency diagnostics as the required baseline.

### Completion gate — completed 13 August 2026

- The experiment covers the two predeclared combined methods in
  `ModelConfig`: Risk Parity as the covariance-focused rule and Maximum Sharpe as
  the mean-sensitive rule. No method was chosen after viewing frequency results.
- Each method uses the same 60 assets, 252-observation trailing window, first live
  date (4 January 2021), final date (29 December 2023), constraints, annualisation,
  covariance treatment, and 10 basis-point primary cost. Daily, every-5-day,
  every-10-day, and first-observed-date monthly schedules are the only intended
  difference.
- Daily, every-5-day, and every-10-day paths are explicitly labelled diagnostic;
  monthly remains the primary app, fact-sheet, and assignment specification.
- All 2,032 experiment rebalance decisions pass solver, prior-only timing,
  long-only, full-investment, individual-cap, and 30% combined crypto-cap checks.
  The monthly paths reconcile exactly to Phase 2 returns and target weights.
- Gross and net performance, drift-aware turnover, concentration, crypto sleeve,
  maximum drawdown, and cost drag are available for all eight paths. Cost
  sensitivity is reported at the predeclared 5, 10, and 25 basis points.
- Risk Parity supports monthly: its monthly net Sharpe is about 0.883, compared
  with 0.872 daily, 0.865 every 5 days, and 0.876 every 10 days. Daily annualised
  turnover is about 216%, versus 78% monthly.
- Maximum Sharpe is the counterexample: daily achieves the highest 10 bp net
  Sharpe (about 0.897 versus 0.776 monthly) and net CAGR (about 17.1% versus
  14.8%), but annualised turnover rises to about 1,412% from 333%. Its daily
  ending-wealth cost drag is about 0.069 at 10 bp, versus 0.015 monthly, and its
  net CAGR falls to about 14.6% at 25 bp.
- The product decision remains monthly. The higher-frequency Maximum Sharpe
  result is informative diagnostic evidence but violates the assignment's
  primary monthly-or-less-frequent requirement and increases estimation churn,
  implementation burden, and cost sensitivity. The result is preserved rather
  than used to retune the product retrospectively.
- A Word/A4-ready turnover-versus-Sharpe figure passes rendered checks and was
  visually inspected after replacing unreadable logarithmic scientific ticks
  with explicit percentage ticks.
- The complete Project B suite passes `37` tests, including schedule spacing,
  cost isolation, future-return leakage, exact monthly reconciliation, and the
  full real-data frequency regression.

### Evidence generated

- `results/data/rebalance_frequency_returns.csv`
- `results/tables/rebalance_frequency_metrics.csv`
- `results/tables/rebalance_frequency_cost_sensitivity.csv`
- `results/tables/rebalance_frequency_rebalances.csv`
- `results/tables/rebalance_frequency_decision_support.csv`
- `results/tables/rebalance_frequency_validation.csv`
- `results/tables/rebalance_frequency_figure_validation.csv`
- `results/figures/rebalance_frequency_tradeoff.png`
- `results/figures/rebalance_frequency_tradeoff.caption.md`

## Phase 4 — Finance sentiment and standalone sector index

### Work

- [x] Establish a plain-VADER baseline while preserving headline casing,
      punctuation, negation, and raw text.
- [x] Create a small, disclosed finance lexicon whose scores are the unweighted
      arithmetic mean of ten score-blind sub-agent reviews, with every raw score,
      observed-use count, rationale, and dispersion statistic retained.
- [x] Complete the student's review of the proposed lexicon terms/scores and the
      balanced real-headline validation sheet before using them in the report.
- [x] Compare plain and finance-adjusted scores, neutral shares, score changes,
      and polarity-label changes.
- [x] Aggregate scores to ticker-day, explicitly choosing the treatment of
      ticker-days with no headlines.
- [x] Construct the required sector-day index by equal-weighting ticker-day
      scores within each sector.
- [x] Preserve raw and lagged sentiment columns; lag tradable information by at
      least one observed equity trading day.
- [x] Add tests for deduplication, alignment, no-news treatment, sector equal
      weighting, finance-lexicon behaviour, and future-headline leakage.

### Implementation targets

- `src/sentiment.py`
- sentiment tests under `tests/`

### Required and supporting outputs

- `results/data/sector_sentiment_index.csv`
- planned finance-lexicon audit, validation-case, neutral-share, and coverage
  tables
- sector sentiment time-series figure

### Completion gate

Headline and score counts reconcile; sector indices follow the required
ticker-equal-weight rule; the no-news policy is justified; finance lexicon
changes are auditable; and no day uses same-day or future sentiment to trade.

### Analytical build status — rebuilt 14 August 2026; student review complete

- All 146,836 clean headlines retain their original text and receive both plain
  and finance-adjusted VADER scores. The six post-sample unaligned headlines are
  scored for audit but excluded from trading-day aggregation.
- Plain VADER classifies 72,790 headlines (49.57%) as neutral. After both blind
  review rounds and the student's exclusion of the context-dependent `layoff`
  family, the final 75-token, 33-family finance lexicon lowers this to 68,525
  (46.67%), changes 9,481 compound scores, and changes 5,721 polarity labels.
- Ten sub-agents independently scored 15 canonical finance concepts without
  seeing the former scores or one another's responses. All 150 raw votes are
  retained; explicit variants share the canonical family mean so morphology does
  not receive extra voting weight. No reviewer voted zero/exclusion. Across
  families, sample score dispersion ranges from about 0.07 to 0.20 on the
  `[-4, 4]` scale. These are independent AI reviews, not human or model-diverse
  validation, so the student headline review remains required.
- The 50,300-row ticker-day panel treats no-news observations as neutral zero
  without carrying stale information forward. `has_news` and headline counts
  remain separate, so an observed neutral headline is distinguishable from no
  information.
- The required 10,060-row sector index exactly equals the mean of its five
  ticker-day scores. It retains raw plain/finance values, covered-only
  diagnostics, coverage fields, and one-observed-trading-day lags.
- Eight machine-readable validations pass: unique keys, full aligned-headline
  reconciliation, no-news zeros, exact ticker-equal weighting, bounded scores,
  and previous-observed-day lag identity.
- Four new synthetic tests cover finance-VADER behaviour, duplicate rejection,
  explicit no-news treatment, five-ticker equal weighting, one-day lagging, and
  future-headline leakage; earlier alignment and deduplication tests remain part
  of the full suite. The complete Project B suite passes 43 tests after adding
  exact arithmetic-mean regressions for both ten-reviewer rounds.
- The Word/A4 sector time-series exhibit uses faint daily values plus a 21-day
  rolling mean for readability. Manual inspection corrected a legend collision
  and repetitive axis labels missed by the automated checks.
- The student reviewed all 34 candidate families and 58 real score-change cases.
  Thirty-three family scores were approved unchanged and `layoff` was excluded;
  52 headline directions were accepted, five were marked ambiguous and one was
  reversed. The review is stored under `ai/` and is not treated as random labelled
  ground truth or an out-of-sample accuracy estimate.
- External expansion research compared FinVADER, Henry, SentiBigNomics, and the
  official Loughran-McDonald dictionary against the supplied headline corpus. It
  shortlisted 19 families, separated five subject-dependent movement families
  and one uncertainty family, and rejected unsafe generic dictionary words. A
  second ten-agent blind round supplied 190 raw scores; all 19 nonzero arithmetic
  means now enter the production lexicon. `rout`, `antitrust`, and `recall`
  received one, one, and two zero/exclusion votes respectively; those zeros are
  retained in the means and flagged for student case review.

### Evidence generated

- `results/data/sector_sentiment_index.csv`
- `results/data/ticker_sentiment_sample.csv`
- `results/tables/finance_lexicon_audit.csv`
- `results/tables/finance_lexicon_panel_scores.csv`
- `results/tables/finance_lexicon_panel_summary.csv`
- `results/tables/sentiment_model_summary.csv`
- `results/tables/sector_sentiment_summary.csv`
- `results/tables/sentiment_validation_cases.csv`
- `results/tables/finance_lexicon_expansion_validation_cases.csv`
- `results/tables/sentiment_validation_summary.csv`
- `results/tables/sentiment_figure_validation.csv`
- `results/tables/finance_lexicon_candidate_research.csv`
- `results/figures/sector_sentiment_index.png`
- `results/figures/sector_sentiment_index.caption.md`
- `ai/FINANCE_LEXICON_EXPANSION_RESEARCH.md`
- `ai/FINANCE_LEXICON_EXPANSION_BLIND_REVIEW.md`
- `ai/010_phase_4_expansion_blind_panel.md`
- `ai/SENTIMENT_EVENT_AUDIT.md`

## Phase 5 — Coverage-aware sentiment and fund fusion

### Work

- [x] Define a coverage-confidence score using interpretable Project A measures,
      such as constituent breadth and headline concentration, with explicit
      zero-news handling.
- [x] Keep raw finance sentiment, confidence, confidence-adjusted sentiment, and
      lagged tradable signal as separate auditable fields.
- [x] Define a bounded equity-only tilt and normalisation rule.
- [x] Apply the signal to an otherwise-identical monthly base equity fund without
      assigning news scores to crypto.
- [x] Pre-specify or prior-only select the tilt strength; do not tune on the full
      reported out-of-sample period.
- [x] Compare base sentiment, finance sentiment, and coverage-aware variants if
      the design remains interpretable.
- [x] Measure return, volatility, Sharpe, drawdown, turnover, concentration, and
      cost-adjusted effects.
- [x] Run negative controls or robustness checks where useful, and retain null or
      adverse results.
- [x] Add leakage, weight-bound, normalisation, and before-versus-after identity
      tests.

### Implementation targets

- `src/fusion.py`
- fusion and coverage-confidence tests under `tests/`

### Planned outputs

- `results/data/coverage_adjusted_sentiment.csv`
- `results/tables/fusion_performance_comparison.csv`
- `results/figures/fusion_growth_comparison.png`
- validation and sensitivity artifacts as justified

### Completion gate

The fusion is one-day lagged, equity-only, bounded, reproducible, and evaluated
against an identical base specification. Its contribution is reported honestly
whether positive, negative, or negligible.

### Completion gate — completed 13 August 2026

- The primary rule uses the prior observed trading day's
  `finance sentiment × coverage confidence`, cross-sectionally standardised
  across the ten sectors and clipped at two standard deviations.
- Equity Minimum Variance is the unchanged base. A fixed `0.20` exponential
  tilt is applied only to equities, then capped proportional normalisation
  restores long-only full investment under the original 10% individual cap.
- Base, plain-VADER, finance-VADER, and coverage-aware finance paths share the
  same 753 live dates, 36 monthly targets, eligible assets, constraints, and
  10 basis-point transaction-cost assumption.
- The primary coverage-aware rule lowers net annualised return from about 5.67%
  to 5.00% and net Sharpe from 0.504 to 0.453. It makes maximum drawdown about
  0.77 percentage points shallower but raises cumulative turnover from 5.23 to
  5.96. This adverse performance result is retained.
- Fixed `0.10` and `0.40` tilt sensitivities also fail to improve the base
  Sharpe, and deterioration increases with strength. No ex-post strength is
  substituted for the primary rule.
- Ten machine-readable checks pass, including exact confidence multiplication,
  previous-sector-day lagging, signal-source timing, long-only/full-investment/
  cap identities, equity-only application, and exact reconstruction of the base
  daily path.
- The before-versus-after Word/A4 exhibit passed automated validation and manual
  inspection. Manual review corrected scientific-notation dollar ticks missed
  by the first automated pass.
- The final Project B test suite passes 49 tests. The six Phase 5 tests cover
  exact confidence/lag identities, future-headline leakage, bounded tilt
  direction, constant-signal identity, zero base weights under a binding cap,
  and the generated real-data evidence contract.

### Evidence generated

- `results/data/coverage_adjusted_sentiment.csv`
- `results/data/fusion_returns.csv`
- `results/data/fusion_weights.csv`
- `results/tables/fusion_performance_comparison.csv`
- `results/tables/fusion_tilt_sensitivity.csv`
- `results/tables/fusion_validation_summary.csv`
- `results/tables/fusion_figure_validation.csv`
- `results/figures/fusion_growth_comparison.png`
- `results/figures/fusion_growth_comparison.caption.md`
- `ai/011_phase_5_coverage_aware_fusion.md`

## Phase 6 — Exhibits, fact sheets, and evidence reconciliation

### Required exhibits

- [x] Performance-metrics table across funds and methods.
- [x] Growth-of-$1 comparison across methods.
- [x] Drawdown figure for at least one fund.
- [x] Weights-over-time figure across methods for at least one family.
- [x] Sharpe or return-versus-risk comparison across funds and methods.
- [x] Equity-sector sentiment-index time series.
- [x] Fusion before-versus-after table and figure.

### Additional Stockist Funds evidence

- [x] One fact sheet per user-facing `(family, method)` fund.
- [x] Rebalancing-frequency turnover/cost trade-off.
- [x] Plain VADER versus finance-VADER validation.
- [x] Coverage-confidence diagnostic showing when sentiment is well or poorly
      supported.
- [x] Benchmark-relative and concentration evidence where it helps decisions.

### Presentation and validation

- [x] Apply one accessible Stockist Funds design across report and app.
- [x] Include titles/captions, labels, units, sample periods, source notes, and
      interpretation limits.
- [x] Create a claim-to-artifact findings sheet.
- [x] Reconcile every displayed number to machine-readable output.
- [x] Inspect every final figure at Word/A4 report size.

### Completion gate

Every required exhibit exists and is self-contained; each user-facing fund has a
complete fact sheet; extension results are shown rather than merely proposed;
and all displayed values reconcile to generated outputs.

### Completion gate — completed 13 August 2026

- A compact 15-fund performance table now exposes net growth, CAGR, volatility,
  Sharpe, maximum drawdown, turnover, current effective asset count, and
  benchmark-relative return from the primary monthly histories.
- All 15 fact-sheet rows reconcile exactly to `performance_metrics.csv` and the
  latest dated target weights. They now retain the complete non-zero holdings,
  not only a top-ten preview, alongside concentration, cost, turnover, benchmark,
  and evidence-limit fields.
- Eight Word/A4-ready exhibits cover fund growth, combined drawdowns, risk and
  return, combined target weights, sector sentiment, coverage confidence,
  frequency trade-offs, and fusion. Each has a caption sidecar and a backing-data
  and validation entry in the exhibit catalog.
- The new coverage diagnostic separates daily confidence from its 21-day rolling
  mean. Mean confidence ranges from 0.39 for Materials to 0.82 for Consumer; this
  measures evidence support rather than sentiment accuracy.
- Plain-versus-finance validation records 9,481 changed compound scores, 5,721
  changed polarity labels, and a neutral-share reduction from 49.57% to 46.67%.
  The table explicitly avoids treating lower neutrality as automatic accuracy.
- Nine candidate report findings are stored with their displayed values, units,
  source files, filters, and fields. All source artifacts exist and every
  upstream Phase 2–5 validation remains green.
- Manual review at report size covered all nine figures. The risk/return label
  placement was corrected after the first pass and re-inspected; the review log
  records the accepted result and the genuine end-of-sample coverage decline.
- All nine Phase 6 evidence-contract checks pass, and the complete Project B
  suite passes 51 tests.

### Evidence generated

- `results/tables/report_performance_table.csv`
- `results/tables/fact_sheet_validation.csv`
- `results/tables/plain_vs_finance_validation.csv`
- `results/tables/coverage_confidence_summary.csv`
- `results/tables/exhibit_catalog.csv`
- `results/tables/claim_to_artifact_findings.csv`
- `results/tables/phase6_validation_summary.csv`
- `results/tables/coverage_figure_validation.csv`
- `results/figures/coverage_confidence_index.png`
- `results/figures/coverage_confidence_index.caption.md`
- `ai/PHASE_6_FIGURE_REVIEW.md`
- `ai/012_phase_6_evidence_reconciliation.md`

## Phase 7 — Streamlit investor app

### Investor journey

1. Understand Stockist Funds and the historical-simulation disclaimer.
2. Compare the monthly systematic funds.
3. Open a fact sheet and inspect risk, drawdown, and current holdings.
4. Set and review an allocation across funds.
5. Explore finance sentiment and its coverage confidence.
6. Understand the extension result, limitations, and fee illustration.

### Work

- [x] Build a low-fidelity shell with fixture data for comparison, fund details,
      allocation, and news-signal pages before wiring final artifacts.
- [x] Replace the starter app with the Stockist Funds interface.
- [x] Use the investor-facing sidebar information architecture and responsive
      rules in `ai/UI_DESIGN_RESEARCH.md`, subject to prototype testing. The
      final app has five customer destinations after removing the internal
      Methods & data page.
- [x] Load only committed, precomputed `results/` artifacts for the main app.
- [x] Build fund comparison, fact-sheet, holdings, allocation, sentiment, and
      coverage-confidence views.
- [x] Show portfolio-level correlation, overlap, aggregate exposure, drawdown,
      and illustrative fee effects in the allocation builder.
- [x] Place contextual risk and evidence-quality information beside the decision
      it qualifies rather than relying on generic disclaimer blocks.
- [x] Keep the monthly funds as defaults and separate high-frequency diagnostics
      from the investable menu.
- [x] Add clear historical, sample, risk, and no-advice disclosures.
- [x] Add robust artifact validation and helpful empty/error states.
- [x] Confirm that `streamlit_app.py` does not import NLTK or run model builds.
- [x] Test the complete journey locally on the repository environment and verify
      a real Streamlit server health response.
- [ ] Run the five-task comprehension protocol in `ai/APP_PRODUCT_RESEARCH.md`
      with a fresh user and record errors, questions, and design corrections.

### Completion gate

The app starts quickly, loads committed artifacts, supports the full investor
journey without heavy recomputation, remains usable at common screen sizes, and
communicates risk and signal confidence clearly.

### Implementation status — built and locally verified 13 August 2026

- The root entrypoint is now a thin launcher for five sidebar destinations:
  Overview, Compare funds, Fund details, Allocation lab, and News signal. The
  selected view, fund, and sector can be shared through URL query parameters.
- A deployment-safe artifact contract loads and validates 17 committed CSVs,
  including adjusted SPY and ONEQ benchmark histories built outside the app.
  Missing files, empty files, schema changes, a non-15-fund menu, or a failed
  Phase 6 validation stop the app with a specific recovery instruction.
- Comparison supports family/method filters and up to five selected funds, a
  dropdown for same-family Equal Weight, S&P 500 (SPY proxy), or Nasdaq
  Composite (ONEQ proxy), an aligned metric table, risk-return evidence, growth paths,
  definitions, and a filtered download. Higher-frequency experiments are
  excluded from this menu.
- Every primary fund has a complete fact-sheet view with objective, contextual
  risk, balanced return/risk metrics, switchable aligned benchmark growth,
  drawdown, dated complete
  weights, allocation-through-time bands, largest rebalance changes,
  concentration, turnover, costs, evidence limit, and downloads.
- The allocation lab combines two to four already cost-adjusted fund paths with
  a disclosed monthly fund-level rebalance. It shows growth, drawdown, return,
  volatility, Sharpe, an equal-fund reference, look-through assets and asset
  classes, crypto exposure, correlations, pairwise holdings overlap, and a
  separately labelled illustrative product fee. A benchmark dropdown keeps the
  equal-selected-fund reference as default and adds SPY and ONEQ on exact common
  dates with aligned return differences and tracking error. It makes no
  recommendation.
- The news page begins with a precomputed, all-50-stock Stockist News Fear and
  Greed view: a selected-window 0–100 headline-tone level and a full-sample
  standardized daily panel. It then aligns finance/plain sector sentiment with
  headline concentration, literal confidence, no-news states,
  positive-but-thin examples, lexicon validation, and the retained negative
  fusion result. The market and sector rolling windows are display-only; the
  lagged daily signal rule remains visible and unchanged.
- Detailed method definitions, central configuration,
  frequency-versus-turnover diagnostics, equations, data inventory, artifact
  health and reproducibility evidence remain in the project outputs and report,
  rather than a customer-facing app page.
- Streamlit runtime tests exercise every page and a source scan proves the app
  path imports neither raw-data/build modules nor NLTK. A real server started on
  a local port and returned `ok` from its health endpoint before being stopped.
- The final automated test and lint counts are recorded in
  `ai/013_phase_7_streamlit_app.md` after full verification.

### Completion gate still open

The fresh-person five-task comprehension protocol remains deliberately open.
The student should observe a new participant using the rendered browser app at
desktop and mobile widths, then record task completion, errors, questions, and
any resulting corrections. Automated tests cannot establish comprehension or
responsive visual quality.

### Implementation evidence

- `streamlit_app.py`
- `src/app_data.py`
- `src/app_logic.py`
- `src/app_charts.py`
- `src/app_views.py`
- `tests/test_app.py`
- `tests/test_app_logic.py`
- `ai/013_phase_7_streamlit_app.md`
- `ai/PHASE_7_USER_TEST.md`

## Phase 8 — End-to-end pipeline, testing, and reproducibility

### Work

- [x] Make `scripts/run_part_b.py` the thin entrypoint for a fixed monthly build.
- [x] Define required output schemas and validate them after generation.
- [x] Remove or deliberately replace stale generated artifacts on each build.
- [x] Generate a timestamp-free artifact manifest.
- [x] Run the pipeline twice and compare deterministic analytical artifacts.
- [x] Run the full Project B test suite and Ruff.
- [x] Run from a different working directory to verify path independence.
- [x] Scan for raw data, ZIP files, secrets, absolute paths, and deployment-only
      failures.
- [x] Run `scripts/check_handin.py` and resolve every failure.

The routine build was deliberately narrowed to the assignment-primary monthly
walk-forward funds. The completed daily/every-5-day/every-10-day comparison
values remain committed, are validated and included in the manifest, but are
not recomputed during the routine build.

### Completion gate

One documented command regenerates the monthly product and core analytical
output while preserving the completed frequency comparison, tests and lint
pass, all 75 deterministic artifacts match across runs in the fixed environment,
and the hand-in checker has no failures.

### Implementation evidence

- `src/pipeline.py`
- `scripts/run_part_b.py`
- `scripts/check_reproducibility.py`
- `tests/test_pipeline.py`
- `pytest.ini`
- `results/tables/artifact_manifest.csv`
- `ai/030_phase_8_reproducibility.md`

## Phase 9 — Word report and student interpretation

### Planned structure

1. Product, funds, and walk-forward design.
2. Out-of-sample performance and fact sheets.
3. Rebalancing robustness and implementation costs.
4. Finance sentiment and coverage confidence.
5. Fusion evidence and innovation.
6. Streamlit investor journey and product economics.
7. Critical reflection, limitations, and three concrete recommendations.

### Work

- [x] Build Versions 2, 3, 4, 5, 6 and 7 as separate editable Word files under
      `report/`; keep later revisions in their own files.
- [ ] Export `report/report.pdf` only after the student approves the Word draft;
      PDF creation remains deferred for Version 7.
- [ ] Keep narrative within the brief's approximately 5,000-word and 10-page
      limits, excluding appendices and references.
- [x] Define equations, timing conventions, assumptions, constraints, and sample
      before interpreting results.
- [x] Reference and interpret every required exhibit in the Version 7 draft.
- [x] Remove repeated in-image exhibit headings and retain one numbered Word
      caption below each appendix figure.
- [x] Separate observed results, possible explanations, limitations, and
      recommendations.
- [x] Include three specific real-world recommendations grounded in evidence.
- [x] Verify every external source and citation used in Version 7.
- [x] Reconcile all Version 7 report numbers and fund names to final artifacts.
- [x] Revise Version 5 into Version 7 using the author's academic voice while
      preserving all analytical content, tables, figures and conclusions.
- [ ] Inspect every DOCX/PDF page for layout, caption, table, and figure issues.

### Completion gate

The final Word and PDF reports are readable, within the brief, numerically
reconciled, properly sourced, and contain student-reviewed economic
interpretation and recommendations.

## Phase 10 — AI audit, deployment, and hand-in

### Work

- [ ] Maintain numbered prompt logs throughout Phases 1–9.
- [ ] Create a final candid AI-use summary covering assistance, errors, rejected
      advice, student corrections, and negative results.
- [ ] Confirm `AGENTS.md` and every log reflect the workflow actually used.
- [ ] Run final tests, reproducibility checks, app smoke tests, and
      `scripts/check_handin.py`.
- [ ] Remove caches, temporary files, editor clutter, secrets, and raw data.
- [ ] Initialise Project B as its own Git repository and push to a new private
      GitHub repository when authorised by the student.
- [ ] Student deploys `streamlit_app.py` through Streamlit Community Cloud.
- [ ] At hand-in, make the repository public and test both links while logged out.
- [ ] Submit the zipped folder, public repository URL, and live Streamlit URL.

### Completion gate

The Moodle zip, public repository, and live app contain the same reviewed
version; all mandatory artifacts and AI evidence are present; there are no
secrets or raw data; and the app works for an unauthenticated marker.
