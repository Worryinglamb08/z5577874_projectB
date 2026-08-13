"""Focused tests for Stockist Funds chart encodings."""

from __future__ import annotations

import pandas as pd
import pytest
from src.allocation_history import AllocationHistory
from src.app_charts import (
    FAMILY_SYMBOLS,
    allocation_growth_figure,
    allocation_history_figure,
    fear_greed_figure,
    holdings_figure,
    risk_return_figure,
    sector_allocation_figure,
)
from src.app_logic import AllocationBenchmarkEvidence


def test_risk_return_marker_shape_encodes_asset_family() -> None:
    catalog = pd.DataFrame(
        [
            {
                "fund_id": "equity_equal_weight",
                "fund_name": "Equity Equal Weight",
                "asset_family": "equity",
                "family_label": "Equity",
                "method": "equal_weight",
                "method_label": "Equal Weight",
                "net_annualized_volatility": 0.15,
                "net_annualized_return": 0.10,
                "net_sharpe_ratio": 0.7,
            },
            {
                "fund_id": "crypto_equal_weight",
                "fund_name": "Crypto Equal Weight",
                "asset_family": "crypto",
                "family_label": "Crypto",
                "method": "equal_weight",
                "method_label": "Equal Weight",
                "net_annualized_volatility": 0.75,
                "net_annualized_return": 0.40,
                "net_sharpe_ratio": 0.6,
            },
            {
                "fund_id": "combined_equal_weight",
                "fund_name": "Combined Equal Weight",
                "asset_family": "combined",
                "family_label": "Combined",
                "method": "equal_weight",
                "method_label": "Equal Weight",
                "net_annualized_volatility": 0.16,
                "net_annualized_return": 0.12,
                "net_sharpe_ratio": 0.8,
            },
        ]
    )

    figure = risk_return_figure(catalog, ["equity_equal_weight"])

    symbols = {
        trace.legendgroup: trace.marker.symbol
        for trace in figure.data
    }
    assert symbols == FAMILY_SYMBOLS
    assert len(set(symbols.values())) == len(FAMILY_SYMBOLS)
    assert figure.data[0].marker.size == 15
    assert figure.data[0].marker.line.color == "#0F172A"
    assert all(trace.showlegend for trace in figure.data)


def test_sector_allocation_figure_is_a_complete_pie_chart() -> None:
    allocation = pd.DataFrame(
        {
            "sector": ["Tech", "Financials", "Crypto"],
            "sector_label": ["Technology", "Financials", "Crypto"],
            "target_weight": [0.4, 0.35, 0.25],
        }
    )

    figure = sector_allocation_figure(
        allocation,
        title="How is the target portfolio allocated by sector?",
    )

    assert len(figure.data) == 1
    assert figure.data[0].type == "pie"
    assert list(figure.data[0].labels) == allocation["sector_label"].tolist()
    assert sum(figure.data[0].values) == pytest.approx(100)
    assert figure.layout.title.text == "How is the target portfolio allocated by sector?"
    assert figure.layout.legend.orientation == "h"
    assert figure.layout.legend.entrywidthmode == "fraction"
    assert figure.layout.legend.entrywidth == pytest.approx(0.32)
    assert figure.layout.legend.y < 0
    assert figure.layout.margin.b >= 120


def test_holdings_and_sector_figures_have_matching_heights() -> None:
    latest = pd.DataFrame(
        {
            "asset": ["A", "B", "C"],
            "target_weight": [0.5, 0.3, 0.2],
        }
    )
    allocation = pd.DataFrame(
        {
            "sector": ["Tech", "Financials"],
            "sector_label": ["Technology", "Financials"],
            "target_weight": [0.6, 0.4],
        }
    )

    holdings = holdings_figure(latest, title="Holdings")
    sectors = sector_allocation_figure(allocation, title="Sectors")

    assert holdings.layout.height == sectors.layout.height == 500


def test_allocation_history_figure_stacks_categories_with_bottom_legend() -> None:
    dates = pd.to_datetime(["2023-11-01", "2023-12-01"])
    history = AllocationHistory(
        data=pd.DataFrame(
            {
                "rebalance_date": [dates[0], dates[0], dates[1], dates[1]],
                "category": ["Tech", "Crypto", "Tech", "Crypto"],
                "category_label": ["Technology", "Crypto"] * 2,
                "target_weight": [0.80, 0.20, 0.70, 0.30],
            }
        ),
        category_order=("Tech", "Crypto"),
        basis="sector",
    )

    figure = allocation_history_figure(history, title="Allocation through time")

    assert len(figure.data) == 2
    assert all(trace.stackgroup == "allocation" for trace in figure.data)
    assert {trace.name for trace in figure.data} == {"Technology", "Crypto"}
    assert figure.layout.yaxis.range == (0, 100)
    assert figure.layout.legend.orientation == "h"
    assert figure.layout.legend.entrywidth == pytest.approx(0.32)


def test_allocation_growth_figure_names_the_selected_benchmark() -> None:
    dates = pd.to_datetime(["2023-11-01", "2023-12-01"])
    evidence = AllocationBenchmarkEvidence(
        path=pd.DataFrame(
            {
                "date": dates,
                "allocation_growth_of_1": [1.0, 1.1],
                "benchmark_growth_of_1": [1.0, 1.05],
            }
        ),
        benchmark_id="sp500_spy",
        benchmark_label="S&P 500 (SPY total-return proxy)",
        allocation_metrics={},
        benchmark_metrics={},
        annualized_return_difference=0.05,
        tracking_error=0.10,
        first_date=dates[0],
        last_date=dates[1],
        observation_count=2,
        annualization_days=252,
        source="Test source",
        return_basis="Test basis",
    )

    figure = allocation_growth_figure(evidence)

    assert [trace.name for trace in figure.data] == [
        "Chosen allocation",
        "S&P 500 (SPY total-return proxy)",
    ]
    assert figure.layout.title.text == (
        "How did the hypothetical fund mix compound against its benchmark?"
    )
    assert figure.layout.yaxis.title.text == "Growth of $1 on aligned dates"


def test_fear_greed_figure_pairs_rolling_level_with_standardized_daily_bars() -> None:
    dates = pd.date_range("2023-01-02", periods=70, freq="B")
    market = pd.DataFrame(
        {
            "date": dates,
            "finance_fear_greed_index": [52 + 0.05 * index for index in range(70)],
            "finance_standardized_score": [
                (-1 if index % 2 else 1) * index / 20 for index in range(70)
            ],
            "headline_count": [100] * 70,
            "covered_tickers": [40] * 70,
            "ticker_count": [50] * 70,
        }
    )

    figure = fear_greed_figure(
        market,
        model_prefix="finance",
        model_label="Finance-adjusted VADER",
        window=21,
    )

    assert figure.layout.title.text == "Stockist News Fear and Greed Index"
    assert [trace.type for trace in figure.data] == ["scatter", "bar"]
    assert figure.data[0].name == "21-day news mood"
    assert figure.data[1].customdata[0].tolist() == [100, 40, 50]
    assert figure.layout.yaxis.range == (44, 66)
    assert figure.layout.yaxis.title.text == "Fear ↔ greed (0-100)"
    assert figure.layout.yaxis2.title.text == "Standardized daily mood (z)"
    assert len(figure.layout.shapes) == 5
