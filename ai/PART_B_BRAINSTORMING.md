# Part B Brainstorming Notes

These notes collect the strongest ideas for improving the Part B report and app story. The aim is to show innovation, risk awareness, and data-driven results beyond a simple AI-generated baseline.

## Core Positioning

Stockist Funds should be framed as a risk-aware systematic fund platform, not only a portfolio dashboard. The investor journey is:

1. Compare systematic funds.
2. Understand each fund's risk and performance.
3. Review sentiment analytics.
4. Set an allocation.
5. Understand how the platform earns fees.

The report should repeatedly connect results to investor usefulness: risk control, benchmark value added, drawdown transparency, and whether the fund rules are robust out of sample.

## Innovation Ideas To Emphasise

Strong extensions to mention or build:

- Rebalancing-frequency experiment: monthly is the primary assignment-compliant fund specification; daily, weekly, and bi-weekly schedules are clearly labelled sensitivity experiments for noise, turnover, and cost drag.
- Benchmarking: compare optimised funds against transparent simple alternatives.
- Finance-specific VADER lexicon: extend general VADER with finance terms and test how scores change.
- Risk integration: volatility, drawdown, Sharpe ratio, concentration, turnover, and benchmark-relative results.
- Fee structure: management fee plus performance fee only when the fund beats its benchmark.

Covariance shrinkage is now implemented and tested as an isolated Ledoit-Wolf
robustness prototype. The student decided to retain it as experimental evidence
only because results differed by asset family and they did not want
family-specific model definitions. The app funds continue to use the original
sample-plus-ridge covariance.

## Risk Integration

Risk is already integrated through:

- Minimum-variance optimisation.
- Risk-parity optimisation.
- Annualised volatility.
- Sharpe ratio.
- Maximum drawdown.
- Long-only asset caps.
- Current holdings and allocation weights.

The report can make this stronger by presenting risk as part of the product design:

> Stockist Funds is designed around investable risk-adjusted performance, not just high historical returns. Each fund is assessed using return, volatility, Sharpe ratio, drawdown, and benchmark-relative performance so that users can compare both upside and downside risk.

Possible app/report enhancement:

- Add a "Risk Engine" or "Risk Summary" section.
- Show whether a fund's drawdown is large relative to its own history.
- Show whether concentration risk is high in the latest holdings.
- Report turnover in the retraining frequency experiment.

## Retraining Frequency Experiment

This is a strong innovation and robustness test. Monthly rebalancing remains the primary specification used for the assignment's required funds, fact sheets, app, and conclusions. Daily, weekly, and bi-weekly schedules are diagnostic sensitivity experiments rather than substitutes for the brief's monthly-or-less-frequent fund rule.

Research question:

> Does more frequent retraining improve out-of-sample fund performance, or does it mainly increase noise sensitivity and turnover?

Experiment design:

| Experiment | In-sample window | Retrain/rebalance frequency | Out-of-sample holding period |
|---|---:|---:|---:|
| Diagnostic: daily | 252 trading days | Every trading day | 1 trading day |
| Diagnostic: weekly | 252 trading days | Every 5 trading days | About 5 trading days |
| Diagnostic: bi-weekly | 252 trading days | Every 10 trading days | About 10 trading days |
| Primary: monthly | 252 trading days | First eligible trading day of each month | About 21 trading days |

Important interpretation:

> The optimiser is trained only on historical data available before the rebalance date. The next holding period is out of sample. This makes the experiment a look-ahead-safe walk-forward historical simulation.

Recommended table columns:

- Annualised return.
- Annualised volatility.
- Sharpe ratio.
- Maximum drawdown.
- Cumulative return.
- Average turnover.
- Transaction-cost-adjusted return, if implemented.

Expected interpretation:

> Daily retraining may look sophisticated, but if it creates higher turnover without a clear improvement in Sharpe ratio or drawdown, monthly rebalancing remains the more defensible product design. The higher-frequency schedules are sensitivity evidence, not the assignment-compliant default fund.

## Look-Ahead Bias

Look-ahead bias happens when a model uses information that would not have been available at the time of the decision.

Report wording:

> To avoid look-ahead bias, portfolio weights are formed using only returns from the prior estimation window. If the fund rebalances on date t, the optimiser uses information available before date t. Returns after date t are used only to evaluate out-of-sample performance.

For sentiment:

> Sentiment is lagged by at least one trading day. A headline aligned to trading day t can first affect a trading decision on t+1, so the fund does not trade on same-day information that may not have been available before execution.

## Walk-Forward Backtest

Walk-forward design:

1. Select a historical estimation window.
2. Estimate expected returns, covariance, sentiment signal, and portfolio weights.
3. Hold those weights during the next live out-of-sample period.
4. Move forward and repeat.

Report wording:

> The backtest is walk-forward because the model is repeatedly retrained through time and then tested on the next unseen period. This mirrors how a real systematic fund would operate.

## Historical Simulation

Report wording:

> The backtest is a historical simulation: it asks how Stockist Funds' rules-based funds would have performed during the realised 2021-2023 market path, using only information available at each rebalance date. It does not claim to predict future returns, but it tests whether the investment rules were robust under realistic historical conditions.

## Benchmarking

Benchmarking should answer:

> Did Stockist Funds add value relative to simple investable alternatives?

Useful benchmarks:

- Equal-weight equity fund.
- Equal-weight crypto fund.
- Equal-weight combined fund.
- Naive combined allocation such as 80% equity / 20% crypto or 90% equity / 10% crypto.
- Zero-return cash baseline, if the Sharpe ratio assumes zero risk-free rate.

Report wording:

> Each optimised fund is compared against transparent benchmark rules. This prevents the analysis from treating optimisation as valuable by default and tests whether the additional complexity improves investor outcomes.

Best benchmark link:

- Combined adaptive or optimised fund versus equal-weight combined fund.
- Equity sentiment tilt versus equity minimum-variance fund.
- Fee performance test versus the relevant benchmark.

## Fee Structure And Business Model

Stockist Funds can earn revenue through:

1. Management fee on assets under management.
2. Performance fee only if a fund beats its benchmark.

Example:

> Stockist Funds charges a 0.50% annual management fee plus a 10% performance fee on returns above the relevant benchmark. For the Combined fund, the benchmark is the Equal-Weight Combined fund. If the fund returns 12% and the benchmark returns 8%, the excess return is 4%, so the performance fee is 10% x 4% = 0.40% of assets. The total fee for that year is 0.90% of assets.

Professional detail:

> A high-water mark should apply so investors are not charged performance fees for simply recovering previous losses.

Why this matters:

> The performance fee aligns Stockist Funds' incentives with investors because the platform earns additional fees only when it creates value relative to a transparent passive benchmark.

## Finance-Specific VADER Lexicon

Standard VADER is built for general English, not finance headlines. A finance-specific lexicon can reduce false neutral or misclassified headlines.

Current finance terms to build around:

| Positive terms | Negative terms |
|---|---|
| beat | miss |
| upgrade | downgrade |
| outperform | underperform |
| buyback | warning |
| raises | cuts |
| record | probe |
| surge | lawsuit |
| rally | plunge |

Report wording:

> I extend VADER with a small finance-specific lexicon because finance headlines often use words that carry specialised investor meaning. For example, "upgrade", "beat", and "buyback" are usually positive, while "downgrade", "miss", and "probe" are usually negative.

Evidence to show:

- Base VADER versus Finance-VADER score comparison.
- Share of neutral headlines before and after adding the finance lexicon.
- Sector sentiment index under base VADER and Finance-VADER.
- Whether the finance-adjusted sentiment signal improves or changes portfolio fusion results.

Important interpretation:

> A better text signal does not need to guarantee higher returns. If the sentiment tilt does not improve the portfolio, the report can still argue that the experiment is useful because it shows headline sentiment is noisy and should be treated as a risk or information signal rather than an automatic trading rule.

## Neat Formulas For Report

Use Word's equation editor for the final report.

Portfolio return:

```text
R_{p,t} = sum_i w_{i,t-1} R_{i,t}
```

Annualised return:

```text
R_ann = (1 + R_cum)^(252 / T) - 1
```

Annualised volatility:

```text
sigma_ann = sigma_daily x sqrt(252)
```

Sharpe ratio:

```text
Sharpe = (R_ann - R_f) / sigma_ann
```

If the risk-free rate is assumed to be zero:

```text
Sharpe = R_ann / sigma_ann
```

Drawdown:

```text
DD_t = V_t / max(V_1, ..., V_t) - 1
```

Maximum drawdown:

```text
MaxDD = min_t DD_t
```

Turnover:

```text
Turnover_t = 0.5 x sum_i |w_{i,t} - w_{i,t-1}|
```

Sector sentiment index:

```text
S_{sector,t} = (1 / N_s) x sum_{i in sector} S_{i,t}
```

Sentiment tilt:

```text
w'_{i,t} = w_{i,t} x (1 + lambda S_{i,t-1})
```

Normalised tilted weight:

```text
w^{tilted}_{i,t} = w'_{i,t} / sum_j w'_{j,t}
```

Management fee:

```text
Fee_mgmt = AUM x f_m
```

Performance fee:

```text
Fee_perf = AUM x f_p x max(0, R_p - R_b)
```

Total fee:

```text
Fee_total = Fee_mgmt + Fee_perf
```

Finance-VADER headline score:

```text
S_{headline,t} = VADER(title_t ; L_base union L_finance)
```

## Possible Report Section

Suggested section title:

> Robustness, Benchmarking, and Product Economics

Possible paragraph:

> To test whether Stockist Funds' results depend on an arbitrary modelling choice, I use monthly rebalancing for the primary investable specification and rerun the same walk-forward design under daily, weekly, and bi-weekly diagnostic schedules. The estimation window and other model choices are held fixed while the out-of-sample holding period changes. I then benchmark each optimised fund against simple equal-weight alternatives and compare gross with cost-adjusted performance. This tests whether additional update frequency creates value after risk, turnover, and implementation complexity. Finally, I link the benchmark design to Stockist Funds' fee structure: investors pay a fixed management fee, while any performance fee is charged only on returns above the relevant benchmark.
