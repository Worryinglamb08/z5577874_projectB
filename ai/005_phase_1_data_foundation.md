# Prompt log — Phase 1 data foundation

**Date:** 13 August 2026  
**Scope:** Independent Project B ETL, returns, calendar alignment, news coverage,
and Project A regression

## What I wanted

Move from the approved Phase 0 design into Phase 1 and rebuild only the Project A
data foundation required for Project B's funds, sentiment, and fusion analysis.
The result needed to be independently runnable, auditable, and protected against
calendar mistakes and look-ahead.

## Prompt(s)

The student instructed:

> Move to Phase 1

This followed the approved defaults, fund menu, phase roadmap, and visual system
recorded during Phase 0.

## What the assistant produced

- Replaced the Project B ETL and return placeholders with validated local modules.
- Added `src/news_features.py` for same/next-trading-day headline alignment,
  complete ticker-day and sector-day grids, breadth, HHI, prior-only attention,
  and the approved coverage-confidence equation.
- Added `src/foundation.py` as the deterministic Phase 1 orchestrator and kept
  `scripts/run_part_b.py` thin.
- Generated a compact input catalog, data-integrity evidence, return hand checks,
  headline alignment counts, and a 17-check Project A reconciliation table.
- Added synthetic and real-data tests covering source copying, sample caps,
  deduplication, adjusted-close returns, native crypto timing, no-fill alignment,
  no-news coverage, confidence bounds, future-headline leakage, and independence
  from the Project A runtime.

## What was wrong or risky

- Direct Project A imports would make Project B non-independent and fragile. The
  required student-owned logic was adapted locally and a source-scan regression
  test rejects a Project A runtime reference.
- Computing a Monday crypto return after merging price levels to the equity
  calendar would incorrectly accumulate weekend performance. Returns are first
  computed on the seven-day crypto calendar; Monday therefore retains the native
  Sunday-to-Monday interval.
- Forward-filling a missing crypto return would invent a realised return. The
  combined panel is a left join of already-computed returns and leaves missing
  values missing.
- Mapping headlines after the final equity date backward would introduce future
  information. Six such headlines remain explicitly unaligned and excluded from
  the coverage panels.
- HHI is undefined on no-news days. The raw HHI remains missing while the
  approved confidence field is explicitly zero, preserving both mathematical
  meaning and the product rule.
- A tail sample can look unusually sparse and should not be treated as a full
  coverage diagnostic. The full panel summary separately records 10,060 rows,
  228 no-news sector-days, 9,353 positive-confidence rows, and mean confidence
  of about 0.624.
- The first data run failed in the restricted environment because the supplied
  helper needed network access. It was rerun with approved access; no source ZIP
  or raw frame was saved to the project.
- Repository-wide lint still reports formatting in supplied protected helpers.
  The student-owned Phase 1 files and tests pass the lint rules without changing
  `src/data_access.py`.

## Checks performed

- Exact clean rows: 50,300 equities, 14,610 crypto, and 146,836 headlines.
- Exact documented resolutions: 10 post-2023 crypto rows removed, 2,847 exact
  headline duplicates removed, and 137,447 missing publishers retained.
- Native return counts: 50,250 equity and 14,600 crypto observations.
- Hand checks: NVDA on 3 January 2020 equals `-0.01600591028787468`; BTC-USD on
  2 January 2020 equals `-0.029819292162590716`.
- Headline alignment: 134,279 same-day, 12,551 next-day, and 6 unaligned rows;
  146,830 headlines enter the complete coverage panels.
- Panel dimensions: 50,300 ticker-days and 10,060 sector-days.
- All 17 Project A reconciliation checks pass with zero difference.
- `20` Project B tests pass.
- Ruff passes for all student-owned Phase 1 modules, the orchestrator, and tests.

## What I changed and why

The assistant constrained Phase 1 to reusable data foundations and did not begin
optimisation or sentiment scoring early. It also added explicit Project B naming,
typed result containers, provenance, and regression evidence instead of copying
Project A's phase labels wholesale. This keeps later work modular and makes any
future departure from the validated Project A foundation visible.

## Student review still required

- Review this contemporaneous log and rewrite any wording that does not reflect
  the student's own evaluation.
- Confirm Phase 2 should now implement the approved configuration object and the
  monthly walk-forward fund engine before the frequency experiments begin.
