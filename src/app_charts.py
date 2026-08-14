"""Interactive Plotly figures using the approved Stockist Funds visual system."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.allocation_history import AllocationHistory
from src.app_logic import (
    METHOD_LABELS,
    AllocationBenchmarkEvidence,
    BenchmarkEvidence,
)

INK = "#0F172A"
SECONDARY = "#475569"
ACCENT = "#0F766E"
RULE = "#CBD5E1"
ADVERSE = "#C2410C"
SOFT = "#F8FAFC"
METHOD_COLORS = {
    "equal_weight": SECONDARY,
    "minimum_variance": "#0072B2",
    "risk_parity": "#E69F00",
    "maximum_sharpe": "#CC79A7",
    "hierarchical_risk_parity": "#7C3AED",
}
COMPARISON_COLORS = (
    ACCENT,
    "#0072B2",
    "#E69F00",
    "#CC79A7",
    "#7C3AED",
)
SECTOR_COLORS = {
    "Comm": "#56B4E9",
    "Consumer": "#E69F00",
    "Energy": "#009E73",
    "Financials": "#0072B2",
    "Healthcare": "#CC79A7",
    "Industrials": "#D55E00",
    "Materials": "#F0E442",
    "RealEstate": "#8B5CF6",
    "Tech": "#0F766E",
    "Utilities": "#64748B",
    "Crypto": "#111827",
}
CRYPTO_COLORS = (
    "#0F766E",
    "#0072B2",
    "#E69F00",
    "#CC79A7",
    "#7C3AED",
    "#56B4E9",
    "#D55E00",
    "#009E73",
    "#64748B",
    "#111827",
)
FAMILY_SYMBOLS = {
    "equity": "diamond",
    "crypto": "circle",
    "combined": "square",
}


def _theme(
    fig: go.Figure,
    *,
    yaxis_title: str,
    height: int = 440,
    range_slider: bool = False,
) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 24, "r": 24, "t": 58, "b": 52 if range_slider else 34},
        font={"family": "Aptos, Inter, Segoe UI, sans-serif", "color": INK},
        title={"x": 0.0, "xanchor": "left", "font": {"size": 19}},
        legend={
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": 1.02,
            "yanchor": "bottom",
            "title": None,
        },
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(
        showgrid=False,
        rangeslider={"visible": range_slider},
        tickformat="%Y",
        automargin=True,
    )
    fig.update_yaxes(
        title=yaxis_title,
        showgrid=True,
        gridcolor=RULE,
        zerolinecolor=RULE,
        automargin=True,
    )
    return fig


def risk_return_figure(catalog: pd.DataFrame, selected_ids: list[str]) -> go.Figure:
    """Show risk and return together for the filtered monthly menu."""
    fig = go.Figure()
    displayed_families: set[str] = set()
    for row in catalog.itertuples(index=False):
        selected = row.fund_id in selected_ids
        show_family_legend = row.asset_family not in displayed_families
        fig.add_trace(
            go.Scatter(
                x=[100 * row.net_annualized_volatility],
                y=[100 * row.net_annualized_return],
                mode="markers",
                name=row.family_label,
                legendgroup=row.asset_family,
                showlegend=show_family_legend,
                marker={
                    "size": 15 if selected else 10,
                    "color": ACCENT if selected else METHOD_COLORS[row.method],
                    "symbol": FAMILY_SYMBOLS[row.asset_family],
                    "line": {
                        "color": INK if selected else "white",
                        "width": 2 if selected else 1.5,
                    },
                },
                customdata=[[row.family_label, row.method_label, row.net_sharpe_ratio]],
                hovertemplate=(
                    "<b>%{customdata[0]} · %{customdata[1]}</b><br>"
                    "Annualised volatility: %{x:.2f}%<br>"
                    "Annualised return after trading costs: %{y:.2f}%<br>"
                    "Sharpe ratio: %{customdata[2]:.3f}<extra></extra>"
                ),
            )
        )
        displayed_families.add(row.asset_family)
    fig.update_layout(title="How did return and volatility compare?")
    _theme(fig, yaxis_title="Annualised return after trading costs (%)", height=430)
    fig.update_layout(legend_title_text="Asset family")
    fig.update_xaxes(title="Annualised volatility (%)")
    return fig


def growth_figure(
    returns: pd.DataFrame,
    fund_ids: list[str],
    labels: Mapping[str, str],
    methods: Mapping[str, str],
    *,
    title: str,
) -> go.Figure:
    """Plot selected historical fund growth paths."""
    fig = go.Figure()
    for index, fund_id in enumerate(fund_ids):
        path = returns.loc[returns["fund_id"].eq(fund_id)].sort_values("date")
        method = methods[fund_id]
        fig.add_trace(
            go.Scatter(
                x=path["date"],
                y=path["growth_of_1_net"],
                name=labels[fund_id],
                mode="lines",
                line={
                    "color": COMPARISON_COLORS[index % len(COMPARISON_COLORS)],
                    "width": 2.5,
                    "dash": "dash" if method == "equal_weight" else "solid",
                },
                hovertemplate="%{x|%Y-%m-%d}<br>Growth of $1: $%{y:.3f}<extra></extra>",
            )
        )
    fig.update_layout(title=title)
    _theme(
        fig,
        yaxis_title="Growth of $1 after trading costs",
        height=500,
        range_slider=True,
    )
    fig.update_layout(
        margin={"t": 126},
        title={"y": 0.98, "yanchor": "top"},
        legend={
            "entrywidthmode": "fraction",
            "entrywidth": 0.32,
            "font": {"size": 11},
            "y": 1.02,
            "yanchor": "bottom",
        },
    )
    return fig


def benchmark_growth_figure(
    evidence: BenchmarkEvidence, fund_label: str
) -> go.Figure:
    """Plot one fund against the selected benchmark on exact common dates."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=evidence.path["date"],
            y=evidence.path["fund_growth_of_1"],
            name=fund_label,
            mode="lines",
            line={"color": ACCENT, "width": 2.6},
            hovertemplate="%{x|%Y-%m-%d}<br>Growth of $1: $%{y:.3f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=evidence.path["date"],
            y=evidence.path["benchmark_growth_of_1"],
            name=evidence.benchmark_label,
            mode="lines",
            line={"color": SECONDARY, "width": 2.2, "dash": "dash"},
            hovertemplate="%{x|%Y-%m-%d}<br>Growth of $1: $%{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(title="How did $1 compound against the selected benchmark?")
    return _theme(fig, yaxis_title="Growth of $1 on aligned dates", range_slider=True)


def drawdown_figure(
    returns: pd.DataFrame,
    fund_ids: list[str],
    labels: Mapping[str, str],
    *,
    title: str,
) -> go.Figure:
    """Plot aligned drawdown paths for one or more funds."""
    fig = go.Figure()
    colors = [ADVERSE, "#0072B2", "#E69F00"]
    for index, fund_id in enumerate(fund_ids):
        path = returns.loc[returns["fund_id"].eq(fund_id)].sort_values("date")
        fig.add_trace(
            go.Scatter(
                x=path["date"],
                y=100 * path["drawdown_net"],
                name=labels[fund_id],
                mode="lines",
                line={"color": colors[index % len(colors)], "width": 2},
                fill="tozeroy" if len(fund_ids) == 1 else None,
                fillcolor="rgba(194,65,12,0.14)" if len(fund_ids) == 1 else None,
                hovertemplate="%{x|%Y-%m-%d}<br>Drawdown: %{y:.2f}%<extra></extra>",
            )
        )
    fig.update_layout(title=title)
    return _theme(fig, yaxis_title="Drawdown from prior peak (%)", height=360)


def holdings_figure(latest: pd.DataFrame, *, title: str) -> go.Figure:
    """Show the ten largest latest simulated target holdings plus Other."""
    top = latest.head(10)[["asset", "target_weight"]].copy()
    other = float(latest.iloc[10:]["target_weight"].sum())
    if other > 1e-10:
        top = pd.concat(
            [top, pd.DataFrame([{"asset": "Other", "target_weight": other}])],
            ignore_index=True,
        )
    top = top.sort_values("target_weight")
    fig = go.Figure(
        go.Bar(
            x=100 * top["target_weight"],
            y=top["asset"],
            orientation="h",
            marker={"color": ACCENT},
            text=[f"{value:.1%}" for value in top["target_weight"]],
            textposition="outside",
            hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(title=title, showlegend=False)
    _theme(fig, yaxis_title="", height=500)
    fig.update_xaxes(title="Target weight (%)", range=[0, max(5, 110 * top["target_weight"].max())])
    return fig


def sector_allocation_figure(allocation: pd.DataFrame, *, title: str) -> go.Figure:
    """Show latest target allocation across supplied equity sectors and crypto."""
    fig = go.Figure(
        go.Pie(
            labels=allocation["sector_label"],
            values=100 * allocation["target_weight"],
            sort=False,
            direction="clockwise",
            textinfo="percent",
            textposition="inside",
            marker={
                "colors": allocation["sector"].map(SECTOR_COLORS),
                "line": {"color": "white", "width": 1.5},
            },
            hovertemplate="<b>%{label}</b><br>Target weight: %{value:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        template="plotly_white",
        height=500,
        margin={"l": 24, "r": 24, "t": 58, "b": 125},
        font={"family": "Aptos, Inter, Segoe UI, sans-serif", "color": INK},
        title={"text": title, "x": 0.0, "xanchor": "left", "font": {"size": 19}},
        legend={
            "title": None,
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": -0.08,
            "yanchor": "top",
            "entrywidth": 0.32,
            "entrywidthmode": "fraction",
        },
        paper_bgcolor="white",
        uniformtext={"minsize": 10, "mode": "hide"},
    )
    return fig


def allocation_history_figure(
    history: AllocationHistory, *, title: str
) -> go.Figure:
    """Show target sector or cryptoasset weights through monthly rebalances."""
    fig = go.Figure()
    label_lookup = history.data.drop_duplicates("category").set_index("category")[
        "category_label"
    ]
    color_lookup = (
        SECTOR_COLORS
        if history.basis == "sector"
        else {
            category: CRYPTO_COLORS[index % len(CRYPTO_COLORS)]
            for index, category in enumerate(history.category_order)
        }
    )
    for category in history.category_order:
        path = history.data.loc[history.data["category"].eq(category)].sort_values(
            "rebalance_date"
        )
        label = str(label_lookup.loc[category])
        fig.add_trace(
            go.Scatter(
                x=path["rebalance_date"],
                y=100 * path["target_weight"],
                name=label,
                mode="lines",
                stackgroup="allocation",
                line={"color": color_lookup[category], "width": 0.6},
                fillcolor=color_lookup[category],
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "%{x|%d %b %Y}<br>Target weight: %{y:.2f}%<extra></extra>"
                ),
            )
        )
    fig.update_layout(title=title)
    _theme(fig, yaxis_title="Target allocation (%)", height=520)
    fig.update_layout(
        margin={"l": 24, "r": 24, "t": 58, "b": 125},
        legend={
            "title": None,
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": -0.12,
            "yanchor": "top",
            "entrywidth": 0.32,
            "entrywidthmode": "fraction",
        },
        hovermode="x unified",
    )
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    return fig


def allocation_growth_figure(evidence: AllocationBenchmarkEvidence) -> go.Figure:
    """Compare a hypothetical allocation with its selected benchmark."""
    fig = go.Figure()
    for column, name, color, dash in (
        ("allocation_growth_of_1", "Chosen allocation", ACCENT, "solid"),
        (
            "benchmark_growth_of_1",
            evidence.benchmark_label,
            SECONDARY,
            "dash",
        ),
    ):
        fig.add_trace(
            go.Scatter(
                x=evidence.path["date"],
                y=evidence.path[column],
                name=name,
                mode="lines",
                line={"color": color, "dash": dash, "width": 2.5},
                hovertemplate="%{x|%Y-%m-%d}<br>Growth of $1: $%{y:.3f}<extra></extra>",
            )
        )
    fig.update_layout(
        title="How did the hypothetical fund mix compound against its benchmark?"
    )
    return _theme(
        fig,
        yaxis_title="Growth of $1 on aligned dates",
        range_slider=True,
    )


def allocation_drawdown_figure(path: pd.DataFrame) -> go.Figure:
    """Show the hypothetical allocation's historical drawdown."""
    fig = go.Figure(
        go.Scatter(
            x=path["date"],
            y=100 * path["drawdown"],
            name="Chosen allocation drawdown",
            line={"color": ADVERSE, "width": 2},
            fill="tozeroy",
            fillcolor="rgba(194,65,12,0.14)",
            hovertemplate="%{x|%Y-%m-%d}<br>Drawdown: %{y:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(title="When and how deeply did the allocation lose value?", showlegend=False)
    return _theme(fig, yaxis_title="Drawdown from prior peak (%)", height=350)


def exposure_figure(exposure: pd.DataFrame, *, title: str) -> go.Figure:
    """Show an exact horizontal exposure breakdown."""
    display = exposure.sort_values("look_through_weight").copy()
    label_column = "asset" if "asset" in display else "asset_class"
    fig = go.Figure(
        go.Bar(
            x=100 * display["look_through_weight"],
            y=display[label_column],
            orientation="h",
            marker={"color": ACCENT},
            hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(title=title, showlegend=False)
    _theme(fig, yaxis_title="", height=max(300, 25 * len(display) + 100))
    fig.update_xaxes(title="Look-through allocation (%)")
    return fig


def sentiment_figure(
    sector: pd.DataFrame, *, score_column: str, score_label: str, window: int
) -> go.Figure:
    """Pair the daily sector score with its selected rolling mean."""
    data = sector.sort_values("date").copy()
    rolling = data[score_column].rolling(window, min_periods=window).mean()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["date"],
            y=data[score_column],
            name="Daily score",
            line={"color": RULE, "width": 1},
            hovertemplate="%{x|%Y-%m-%d}<br>Daily score: %{y:.3f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["date"],
            y=rolling,
            name=f"{window}-day rolling mean",
            line={"color": ACCENT, "width": 2.5},
            hovertemplate="%{x|%Y-%m-%d}<br>Rolling mean: %{y:.3f}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line={"color": SECONDARY, "width": 1, "dash": "dot"})
    fig.update_layout(title=f"How did {score_label.lower()} change through time?")
    return _theme(fig, yaxis_title="Sentiment score (-1 to +1)", range_slider=True)


def fear_greed_figure(
    market: pd.DataFrame,
    *,
    model_prefix: str,
    model_label: str,
    window: int,
) -> go.Figure:
    """Show market news tone as a rolling level and full-sample daily z-score."""
    data = market.sort_values("date").copy()
    level_column = f"{model_prefix}_fear_greed_index"
    standardized_column = f"{model_prefix}_standardized_score"
    rolling = data[level_column].rolling(window, min_periods=window).mean()
    standardized = data[standardized_column]
    bar_colors = [ACCENT if value >= 0 else "#D96C8A" for value in standardized]
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        row_heights=[0.56, 0.44],
        subplot_titles=(
            f"{window}-trading-day market level",
            "Daily standardized market mood",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=data["date"],
            y=rolling,
            name=f"{window}-day news mood",
            mode="lines",
            line={"color": "#9F1239", "width": 2.6},
            hovertemplate=(
                "%{x|%Y-%m-%d}<br>News Fear and Greed: %{y:.2f}<extra></extra>"
            ),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=data["date"],
            y=standardized,
            name="Daily standardized mood",
            marker={"color": bar_colors, "line": {"width": 0}},
            customdata=data[
                ["headline_count", "covered_tickers", "ticker_count"]
            ].to_numpy(),
            hovertemplate=(
                "%{x|%Y-%m-%d}<br>Standardized mood: %{y:+.2f} z"
                "<br>Headlines: %{customdata[0]:,.0f}"
                "<br>Stocks with news: %{customdata[1]:.0f} of %{customdata[2]:.0f}"
                "<extra></extra>"
            ),
        ),
        row=2,
        col=1,
    )
    fig.add_hrect(
        y0=44,
        y1=45,
        fillcolor="#FDE7E7",
        line_width=0,
        layer="below",
        row=1,
        col=1,
    )
    fig.add_hrect(
        y0=45,
        y1=55,
        fillcolor="#F1F3F2",
        line_width=0,
        layer="below",
        row=1,
        col=1,
    )
    fig.add_hrect(
        y0=55,
        y1=66,
        fillcolor="#E2F1ED",
        line_width=0,
        layer="below",
        row=1,
        col=1,
    )
    fig.add_hline(
        y=50,
        line={"color": SECONDARY, "width": 1, "dash": "dot"},
        annotation_text="VADER neutral (50)",
        annotation_position="bottom left",
        row=1,
        col=1,
    )
    fig.add_hline(
        y=0,
        line={"color": SECONDARY, "width": 1},
        row=2,
        col=1,
    )
    fig.update_layout(
        template="plotly_white",
        height=650,
        margin={"l": 30, "r": 24, "t": 88, "b": 42},
        font={"family": "Aptos, Inter, Segoe UI, sans-serif", "color": INK},
        title={
            "text": "Stockist News Fear and Greed Index",
            "x": 0.0,
            "xanchor": "left",
            "font": {"size": 19},
        },
        showlegend=False,
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        bargap=0,
    )
    fig.update_annotations(font={"size": 13, "color": SECONDARY})
    fig.update_xaxes(showgrid=False, tickformat="%Y", automargin=True)
    fig.update_yaxes(
        title="Fear ↔ greed (0-100)",
        range=[44, 66],
        gridcolor=RULE,
        automargin=True,
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title="Standardized daily mood (z)",
        gridcolor=RULE,
        zeroline=False,
        automargin=True,
        row=2,
        col=1,
    )
    fig.layout.annotations[0].text += f" · {model_label}"
    return fig


def coverage_figure(sector: pd.DataFrame, *, window: int) -> go.Figure:
    """Show daily and rolling evidence support for the selected sector."""
    data = sector.sort_values("date").copy()
    rolling = data["coverage_confidence"].rolling(window, min_periods=window).mean()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["date"],
            y=data["coverage_confidence"],
            name="Daily confidence",
            line={"color": RULE, "width": 1},
            hovertemplate="%{x|%Y-%m-%d}<br>Confidence: %{y:.3f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["date"],
            y=rolling,
            name=f"{window}-day rolling mean",
            line={"color": "#0072B2", "width": 2.5},
            hovertemplate="%{x|%Y-%m-%d}<br>Rolling confidence: %{y:.3f}<extra></extra>",
        )
    )
    fig.update_layout(title="How broadly was the sentiment score supported?")
    _theme(fig, yaxis_title="Coverage confidence (0 to 1)", range_slider=True)
    fig.update_yaxes(range=[-0.03, 1.03])
    return fig


def fusion_growth_figure(returns: pd.DataFrame) -> go.Figure:
    """Show the base and pre-specified coverage-aware fusion paths."""
    chosen = returns.loc[
        returns["variant"].isin(["base", "coverage_aware_finance"])
    ].copy()
    fig = go.Figure()
    for variant, color, dash in (
        ("base", SECONDARY, "dash"),
        ("coverage_aware_finance", "#CC79A7", "solid"),
    ):
        path = chosen.loc[chosen["variant"].eq(variant)].sort_values("date")
        fig.add_trace(
            go.Scatter(
                x=path["date"],
                y=path["growth_of_1_net"],
                name=path["variant_label"].iloc[0],
                line={"color": color, "dash": dash, "width": 2.5},
                hovertemplate="%{x|%Y-%m-%d}<br>Growth of $1: $%{y:.3f}<extra></extra>",
            )
        )
    fig.update_layout(title="Did coverage-aware sentiment improve the base fund?")
    return _theme(fig, yaxis_title="Growth of $1 after trading costs", range_slider=True)


def frequency_figure(metrics: pd.DataFrame) -> go.Figure:
    """Separate monthly primary evidence from higher-frequency diagnostics."""
    fig = go.Figure()
    for row in metrics.itertuples(index=False):
        monthly = row.schedule_role == "primary_monthly"
        fig.add_trace(
            go.Scatter(
                x=[100 * row.annualized_turnover],
                y=[row.net_sharpe_ratio],
                name=f"{METHOD_LABELS[row.method]} · {row.schedule_label}",
                mode="markers+text",
                text=[row.schedule_label],
                textposition="top center",
                showlegend=False,
                marker={
                    "size": 15 if monthly else 11,
                    "symbol": "diamond" if monthly else "circle",
                    "color": ACCENT if monthly else METHOD_COLORS[row.method],
                    "line": {"color": INK if monthly else "white", "width": 1.2},
                },
                hovertemplate=(
                    f"<b>{METHOD_LABELS[row.method]} · {row.schedule_label}</b><br>"
                    "Annualised turnover: %{x:.1f}%<br>Net Sharpe ratio: %{y:.3f}"
                    "<extra></extra>"
                ),
            )
        )
    fig.update_layout(title="Did faster retraining improve Sharpe enough to justify turnover?")
    _theme(fig, yaxis_title="Net Sharpe ratio", height=460)
    fig.update_xaxes(title="Annualised turnover (%)", type="log")
    return fig


__all__ = [
    "ACCENT",
    "ADVERSE",
    "FAMILY_SYMBOLS",
    "INK",
    "RULE",
    "SECONDARY",
    "SECTOR_COLORS",
    "allocation_drawdown_figure",
    "allocation_growth_figure",
    "allocation_history_figure",
    "benchmark_growth_figure",
    "coverage_figure",
    "drawdown_figure",
    "exposure_figure",
    "frequency_figure",
    "fusion_growth_figure",
    "growth_figure",
    "holdings_figure",
    "risk_return_figure",
    "sector_allocation_figure",
    "sentiment_figure",
]
