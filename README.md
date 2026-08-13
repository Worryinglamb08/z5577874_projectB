# FinTech Project - Part B

## Current build status

Phases 1 through 8 are implemented and verified. The Phase 7 Streamlit app is
built and locally verified; its fresh-user comprehension review remains open.
Phase 4's lexicon and selected
headline cases still require the student's report-level review. `scripts/run_part_b.py` rebuilds and verifies the
local data foundation and the 15 primary monthly walk-forward funds, then exports
their app-readable returns and weights, fact-sheet metrics, diagnostics, and core
report figures. The build also downloads adjusted SPY and ONEQ histories and
exports them as optional S&P 500 and Nasdaq Composite market-reference artifacts. It
The previously completed daily/every-5-day/every-10-day/monthly frequency and
5/10/25 basis-point cost comparisons remain as frozen research evidence; the
routine build validates and preserves those values instead of rerunning their
slow diagnostic optimisations. It then scores plain and finance-
adjusted VADER sentiment, and exports the leakage-safe ticker-equal-weight sector
index and its report exhibit. It then applies the one-day-lagged, coverage-aware
finance signal to the otherwise-identical Equity Minimum Variance fund, exports
the before-versus-after evidence, and retains the observed underperformance.
Finally, it exports the coverage-confidence diagnostic, reconciles all 15 fund
fact sheets, catalogs nine report exhibits, and traces nine candidate findings
to machine-readable source artifacts. Phase 8 validates 75 canonical artifacts,
writes a timestamp-free SHA-256 manifest, and can compare two monthly-only builds
byte for byte.
The app reads only committed precomputed artifacts and never loads raw data,
scores VADER, or reruns the portfolio models at interaction time.

An isolated **Effective Number of Bets** prototype is also available. It uses
PCA-orthogonal risk contributions to compare an experimental Factor
Diversification rule with Risk Parity under the same monthly walk-forward
design. It does not add Factor Diversification to the approved menu or app. Run
`python scripts/run_effective_bets_prototype.py`; its six prototype artifacts
are written under `results/data/` and `results/tables/`.

An isolated **Risk-Parity Black-Litterman sentiment** prototype is available as
well. It reverse-optimises the existing monthly Equity Risk-Parity weights,
uses lagged finance sentiment for sector-basket views, and uses lagged coverage
only to scale view uncertainty. The 1%, 2%, and 4% annual view-scale paths are
exploratory and remain outside the app. Run
`python scripts/run_black_litterman_prototype.py`; its six prototype artifacts
are also written under `results/data/` and `results/tables/`.

**Hierarchical Risk Parity (HRP)** is now the fifth primary monthly method,
expanding the product to 15 funds. It uses single-linkage correlation clustering
and recursive variance bisection, recording any projection needed to satisfy
the approved asset and crypto-sleeve caps. The original controlled comparison
can still be reproduced with `python scripts/run_hrp_prototype.py`; its six
diagnostic artifacts are written under `results/data/` and `results/tables/`.

An isolated **95% minimum-CVaR** prototype compares historical Expected
Shortfall minimisation with Minimum Variance and HRP across all three asset
families. It uses the same monthly walk-forward dates, constraints and 10 bp
cost assumption, but it does not change the 15-fund menu or app. Run
`python scripts/run_cvar_prototype.py`; the prototype CSVs are written under
`results/data/` and `results/tables/`, with a validated comparison figure under
`results/figures/`.

> FIRST: rename this folder to <yourZID>_projectB (for example z1234567_projectB)
> and move it into fins-agent/fins2026/. The folder name carrying your zID is your
> submission.

Part B: funds, sentiment, and the app (DFF Stations 3-4). This folder is also your
public GitHub repository; the app entrypoint is streamlit_app.py at the root.

## How to run

    pip install -r requirements.txt -r requirements-dev.txt   # dev adds VADER + benchmark fetch
    python -m nltk.downloader vader_lexicon  # one-time local build resource
    python scripts/run_part_b.py            # rebuilds monthly funds and core evidence
    python scripts/check_reproducibility.py # optional: builds twice and compares hashes
    python -m pytest -q                     # runs all 138 tests
    python -m ruff check .                  # checks the full project
    streamlit run streamlit_app.py          # runs the app locally

`run_part_b.py` intentionally does not recompute the faster-schedule experiment.
Its committed comparison tables and figure are preserved and validated as frozen
diagnostic evidence; monthly remains the only routine walk-forward product build.

## Investor journey

The sidebar provides five investor-focused destinations:

1. **Overview** — product purpose, systematic process, families, and evidence status.
2. **Compare funds** — up to four selected monthly funds, a switchable
   equal-weight, S&P 500 or Nasdaq Composite benchmark, and secondary filters
   that remove non-matching selections and update the comparison evidence.
3. **Fund details** — one complete fact sheet with a switchable benchmark and
   aligned growth comparison, drawdown, dated holdings, turnover, concentration,
   costs, allocation-through-time bands, and latest weight changes.
4. **Allocation lab** — a hypothetical monthly mix with portfolio risk,
   a switchable equal-fund, SPY or ONEQ benchmark, look-through exposure,
   crypto share, correlation, overlap, and a fixed-fee illustration using the
   code-configured 0.12% annual product fee.
5. **News signal** — finance sentiment, coverage confidence, positive-but-thin
   evidence, plain-VADER comparison, and the measured fusion result.

Detailed model configuration, frequency diagnostics, equations, artifact
validation and reproducibility evidence are retained in the project outputs and
report rather than exposed as a customer-facing app destination.

Important selections are URL-shareable with `?view=`, `?fund=`, `?benchmark=`,
`?allocation_benchmark=`, and `?sector=`.

Load raw data through src/data_access.py (see context/DATA_GUIDE.md); never commit
raw data. The deployed app, by contrast, reads your precomputed artifacts from
results/ - those ARE committed.

## What is here

- streamlit_app.py    the app entrypoint (repo root)
- .streamlit/         app config
- PROJECT_BRIEF.md    the full assignment brief for your course (read this first)
- src/                your code (data_access is provided; portfolios/sentiment/fusion are yours)
- scripts/            runnable scripts that reproduce your results
- results/            your outputs: figures in results/figures/, tables in results/tables/, app data artifacts in results/data/
- context/            provided data guide and project context (do not edit)
- report/             your report - see report/OUTLINE.md (author in Word, submit report.pdf)
- ai/                 your prompt logs and AI notes
- requirements-dev.txt build/repro-only deps (nltk and yfinance); keep them out of the deployed app
- AGENTS.md / CLAUDE.md   replace the stub for your tool (you need just one) with your own

## Deploy + hand in

This folder is its own GitHub repo, independent of fins-agent. Your AI agent can run
the check and push the repo; the browser deploy is yours (it needs your login). See
PROJECT_BRIEF.md Appendix D and docs/STUDENT_DEPLOY.md (in this folder). In short:

    python scripts/check_handin.py        # your agent can run this
    # commit your precomputed app artifacts under results/ (the app reads them)
    # git init in this folder, then push the contents to a NEW private GitHub repo

Then YOU connect the repo on share.streamlit.io (entrypoint streamlit_app.py). At
hand-in, make the repo PUBLIC, submit the live URL + repo link, and also zip this
whole folder and upload the zip to Moodle.
