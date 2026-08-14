<p align="center">
  <img src="assets/stockist_spartan_logo.png" alt="Stockist Funds Spartan logo" width="110">
</p>

<h1 align="center">Stockist Funds</h1>

<p align="center">
  Inspectable systematic investing across equities and crypto.
</p>

<p align="center">
  <a href="https://z5577874projectb.streamlit.app/?view=Overview"><strong>Launch the app</strong></a>
  ·
  <a href="report/report.pdf"><strong>Read the report</strong></a>
  ·
  <a href="https://github.com/Worryinglamb08/z5577874_projectB"><strong>Public repository</strong></a>
</p>

Stockist Funds is an educational FINS5545 prototype for self-directed investors
who want systematic portfolios with inspectable evidence. It turns the supplied
2020–2023 equity, cryptocurrency, and headline data into 15 monthly funds,
complete fact sheets, a hypothetical allocation lab, and a coverage-aware news
signal experiment.

The deployed app reads committed, precomputed artifacts. It does not download
raw data, optimise portfolios, or run VADER during an app interaction.

## What the project delivers

- **15 monthly funds:** Equity, Crypto, and Combined families, each available
  through five portfolio-construction methods.
- **Walk-forward evidence:** prior-only estimation, explicit first-live dates,
  family-specific calendars, turnover, transaction costs, and leakage tests.
- **Complete fact sheets:** growth of $1, return, volatility, Sharpe ratio,
  drawdown, holdings, sector allocation, concentration, and rebalance changes.
- **Fund comparison:** up to five funds with Same-family Equal Weight, S&P 500
  (SPY), or Nasdaq Composite (ONEQ) benchmark options.
- **Allocation lab:** a hypothetical monthly mix with look-through exposures,
  overlap, correlation, drawdown, and a fixed 0.12% product-fee illustration.
- **News analytics:** plain and finance-adjusted VADER, sector sentiment,
  coverage confidence, a fear-and-greed view, and a measured fusion experiment.
- **Inspectable outputs:** app-readable CSVs, report tables, figures,
  validation summaries, captions, and a reproducibility manifest.

## Evidence at a glance

| Item | Evidence |
|---|---:|
| Primary funds | 15 |
| Asset families | Equity, Crypto, Combined |
| Portfolio methods | 5 |
| Monthly decisions per fund | 36 |
| Out-of-sample evaluation | 2021–2023 |
| Clean headlines scored | 146,836 |
| Equity-sector indices | 10 |
| Canonical reproducible artifacts | 76 |
| Automated tests | 144 |

Three results shape the product rather than a simple performance ranking:

- **Combined Risk Parity** has the strongest combined-fund Sharpe ratio at
  `0.883`, with 13.9% annualised return, 16.2% volatility, and a 19.5% maximum
  drawdown.
- **Combined Equal Weight** returns 15.0% annually but has higher 21.6%
  volatility and a deeper 27.9% maximum drawdown.
- The fixed **coverage-aware finance-sentiment tilt does not improve** Equity
  Minimum Variance. Sharpe falls from `0.504` to `0.453`, return falls from 5.67%
  to 5.01%, and cumulative turnover rises from `5.23` to `5.96`; maximum
  drawdown becomes 0.77 percentage points shallower. The negative result is
  retained rather than tuned away.

The finance lexicon changes 9,481 headline scores and reduces the neutral share
from 49.57% to 46.67%. Lower neutrality is not treated as proof of better
classification or return predictability.

## Fund menu

Every method is applied to Equity, Crypto, and Combined assets, producing one
fact sheet per `(family, method)` fund.

| Method | Role in the menu |
|---|---|
| Equal Weight | Transparent baseline that divides capital evenly across eligible assets. |
| Minimum Variance | Seeks the lowest estimated portfolio volatility from trailing covariance. |
| Risk Parity | Spreads estimated portfolio risk so one asset does not dominate it. |
| Maximum Sharpe | Seeks the highest estimated excess return per unit of volatility; explicitly labelled as estimation-sensitive. |
| Hierarchical Risk Parity | Clusters assets that moved similarly and allocates recursively across risk clusters. |

HRP was promoted after a controlled prototype. Other researched methods remain
documented experiments rather than being added merely because they produced a
different historical path.

## Backtest and signal design

The primary specification is monthly and walk-forward:

- 252-observation trailing windows for Equity and Combined funds;
- a 365-observation native-calendar window for Crypto funds;
- weights formed strictly from observations before the first return earned;
- 252-day Equity/Combined and 365-day Crypto annualisation;
- adjusted-close returns, capped at 31 December 2023;
- long-only, fully invested portfolios;
- 10% equity asset cap, 25% crypto asset cap, and 30% Combined crypto-sleeve cap;
- 0% annual risk-free rate; and
- 10 basis points of one-way trading cost applied to drift-aware turnover.

The sentiment index averages headlines within ticker-day, assigns zero to
no-news ticker-days without carrying stale sentiment, and then equal-weights the
five constituent ticker scores in each sector. Every tradable signal is lagged
by one observed equity trading day. Coverage confidence combines constituent
breadth and headline concentration; it describes evidence support, not model
accuracy.

Daily, every-5-day, and every-10-day rebalance schedules and 5/10/25 basis-point
cost cases are retained as frozen sensitivity evidence. Monthly remains the
only primary product specification regenerated by the routine build.

## Investor journey

The sidebar provides five destinations:

1. **Overview** explains the product, systematic process, asset families,
   methods, allocation workflow, and inspectable evidence.
2. **Compare funds** aligns selected funds and benchmarks across common dates,
   with family and method controls presented as filters.
3. **Fund details** provides one complete fact sheet, current holdings, sector
   allocation, allocation history, and latest target-weight changes.
4. **Allocation lab** combines selected fund return histories into a
   hypothetical monthly allocation without presenting it as advice.
5. **News signal** separates sentiment level, standardized movement, coverage
   support, finance-lexicon effects, and the fusion result.

Important selections are URL-shareable through `view`, `fund`, `benchmark`,
`allocation_benchmark`, and `sector` query parameters.

## Run the app locally

The project targets Python 3.13. From a clean clone:

```bash
git clone https://github.com/Worryinglamb08/z5577874_projectB.git
cd z5577874_projectB
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.
The app starts from the repository root and uses only committed files under
`results/`.

## Rebuild and validate the analysis

Install the build and test dependencies, then download VADER's one-time lexical
resource:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m nltk.downloader vader_lexicon
```

Run the deterministic monthly build and validation suite:

```bash
python scripts/run_part_b.py
python scripts/check_reproducibility.py
python -m pytest -q
python -m ruff check .
python scripts/check_handin.py
```

`scripts/run_part_b.py` loads the hosted course data through
`src/data_access.py`, rebuilds the 15 primary funds and core sentiment/fusion
evidence, validates the frozen frequency experiment, and writes a timestamp-free
SHA-256 artifact manifest. `scripts/check_reproducibility.py` performs two builds
and compares their canonical artifact hashes.

## Experimental research

These controlled prototypes are retained as evidence but are not silently added
to the investor-facing menu:

| Experiment | Product decision |
|---|---|
| Effective Number of Bets | Kept as an isolated factor-diversification experiment. |
| Risk-Parity Black–Litterman | Kept outside the menu after the tested sentiment views did not justify promotion. |
| Ledoit–Wolf covariance shrinkage | Conditioning improved, but economic effects were mixed and did not support asset-family-specific adoption. |
| Minimum CVaR | Distinct from Minimum Variance but did not provide a stronger defensive role in this sample. |
| Faster rebalance schedules | Retained as turnover and cost sensitivities, not primary investable funds. |

Prototype entrypoints are under `scripts/run_*_prototype.py`; their outputs are
stored separately from the primary app artifacts.

## Repository structure

```text
streamlit_app.py       Root Streamlit entrypoint
.streamlit/            Theme and deployment configuration
assets/                Stockist visual assets
src/                   Portfolio, sentiment, fusion, app, and validation logic
scripts/               Build, prototype, reproducibility, and hand-in commands
tests/                 Synthetic, real-data, leakage, app, and smoke tests
results/data/          App-readable derived datasets
results/tables/        Metrics, diagnostics, validations, and evidence tables
results/figures/       Self-contained report figures and caption sidecars
report/report.pdf      Final Project B report
ai/                    Agent instructions, prompt logs, review records, and AI Notes
context/               Supplied project context and data guide
```

## Data boundaries and limitations

- The supplied sample ends in 2023; the 2021–2023 out-of-sample period is short
  and includes only a limited set of market regimes.
- SPY and ONEQ adjusted-close histories are investable ETF proxies, not the
  official S&P 500 or Nasdaq Composite index series.
- Crypto trades seven days per week. Combined funds act on the observed equity
  calendar, while Crypto-only funds retain the native calendar.
- The 10-basis-point cost is a transparent modelling assumption, not an
  execution quote or proprietary trading-cost estimate.
- The news data contain headlines, not article bodies. VADER and a token-level
  finance lexicon can misread context, repetition, and mixed-language headlines.
- Coverage confidence measures breadth and concentration of news support; it
  does not establish sentiment accuracy.
- Historical optimisation and backtested performance are not forecasts or
  personal financial advice.

## AI workflow and reproducibility evidence

AI assisted planning, research, modelling, testing, app development, figures,
and early report drafting. Its outputs were treated as starting points and were
checked through tests, artifact reconciliation, visual review, and student
decisions. The process is documented in [`AGENTS.md`](AGENTS.md),
[`ai/AI_Notes.md`](ai/AI_Notes.md), and the numbered prompt logs under `ai/`.

The final mechanical hand-in check passes without failures. The full test suite
contains 144 tests, and the latest reproducibility check confirms 76 canonical
artifacts are byte-identical across builds.
