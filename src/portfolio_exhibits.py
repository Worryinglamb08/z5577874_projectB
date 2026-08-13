"""Report-ready Phase 2 exhibits using the Stockist Funds visual system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, PercentFormatter

from fintools.figures import (
    FigureContext,
    export_word_figure,
    validate_axes_labels,
    validate_display_labels,
    validate_figure_context,
    validate_image_not_blank,
    validate_no_tick_label_overlap,
    validate_titles_within_canvas,
    validate_word_readability,
    word_figure_spec,
)
from fintools.figures.theme import theme_rc
from src.allocation_history import SECTOR_LABELS, allocation_history
from src.portfolios import FAMILY_LABELS, METHOD_LABELS, PortfolioSuite

INK: Final = "#0F172A"
SECONDARY_INK: Final = "#475569"
CANVAS: Final = "#FFFFFF"
RULE: Final = "#CBD5E1"
ACCENT: Final = "#0F766E"
METHOD_COLORS: Final = {
    "equal_weight": "#0F766E",
    "minimum_variance": "#0072B2",
    "risk_parity": "#E69F00",
    "maximum_sharpe": "#CC79A7",
    "hierarchical_risk_parity": "#7C3AED",
}
SECTOR_COLORS: Final = {
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
SOURCE: Final = "Course-provided project_data.zip; Stockist Funds calculations"


class PortfolioExhibitError(ValueError):
    """Raised when a generated Phase 2 exhibit fails selected checks."""


@dataclass(frozen=True)
class PortfolioExhibits:
    """Exported figure paths and rendered validation evidence."""

    figure_paths: list[Path]
    caption_paths: list[Path]
    validation: pd.DataFrame


def _stockist_rc() -> dict[str, object]:
    settings = theme_rc("word_a4", style="ft", ft_background=False)
    settings.update(
        {
            "axes.edgecolor": RULE,
            "axes.labelcolor": INK,
            "axes.prop_cycle": cycler(color=tuple(METHOD_COLORS.values())),
            "axes.titlecolor": INK,
            "figure.facecolor": CANVAS,
            "figure.constrained_layout.use": False,
            "grid.color": RULE,
            "savefig.facecolor": CANVAS,
            "text.color": INK,
            "xtick.color": SECONDARY_INK,
            "ytick.color": SECONDARY_INK,
        }
    )
    return settings


def _style_axis(ax: plt.Axes) -> None:
    ax.set_facecolor(CANVAS)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(RULE)
    ax.spines["bottom"].set_color(RULE)
    ax.grid(axis="y", alpha=0.55, linewidth=0.7)
    ax.grid(axis="x", visible=False)


def _finish_figure(fig: plt.Figure) -> None:
    fig.text(
        0.01,
        0.003,
        f"Source: {SOURCE}. Historical simulation; net of 10 bp turnover costs.",
        ha="left",
        va="bottom",
        fontsize=7,
        color=SECONDARY_INK,
    )


def _sample(suite: PortfolioSuite) -> str:
    dates = pd.to_datetime(suite.fund_returns["date"])
    return f"{dates.min():%Y-%m-%d} to {dates.max():%Y-%m-%d}"


def _export_validated(
    fig: plt.Figure,
    axes: list[plt.Axes],
    *,
    output_dir: Path,
    stem: str,
    context: FigureContext,
    spec: str,
) -> tuple[dict[str, Path], list[dict[str, str]]]:
    paths = export_word_figure(fig, output_dir, stem, context=context, spec=spec)
    figure_spec = word_figure_spec(spec)
    issues = [
        *validate_figure_context(context),
        *validate_titles_within_canvas(fig),
        *validate_word_readability(
            fig, width_inches=figure_spec.width_inches, min_font_size=7.0
        ),
        *validate_image_not_blank(paths["png"]),
    ]
    for ax in axes:
        issues.extend(validate_axes_labels(ax))
        issues.extend(validate_display_labels(ax))
        issues.extend(validate_no_tick_label_overlap(ax, axis="x"))
        issues.extend(validate_no_tick_label_overlap(ax, axis="y"))
    records = (
        [
            {
                "figure": stem,
                "status": "fail",
                "check": issue.code,
                "detail": issue.message,
            }
            for issue in issues
        ]
        if issues
        else [
            {
                "figure": stem,
                "status": "pass",
                "check": "all_selected_checks",
                "detail": "Context, labels, layout, ticks, readability, and image passed.",
            }
        ]
    )
    plt.close(fig)
    return paths, records


def _growth_figure(suite: PortfolioSuite) -> tuple[plt.Figure, list[plt.Axes], FigureContext]:
    returns = suite.fund_returns.copy()
    returns["date"] = pd.to_datetime(returns["date"])
    with plt.rc_context(_stockist_rc()):
        fig, axes_array = plt.subplots(3, 1, sharex=False, figsize=(6.27, 7.35))
        axes = list(axes_array)
        for ax, family in zip(axes, ("equity", "crypto", "combined"), strict=True):
            subset = returns.loc[returns["asset_family"].eq(family)]
            for method, method_frame in subset.groupby("method", sort=False):
                ax.plot(
                    method_frame["date"],
                    method_frame["growth_of_1_net"],
                    color=METHOD_COLORS[method],
                    linewidth=1.35,
                    alpha=0.95,
                    label=METHOD_LABELS[method],
                )
            ax.set_title(FAMILY_LABELS[family], loc="left", fontsize=10, pad=5)
            ax.set_xlabel("Date")
            ax.set_ylabel("Growth of $1")
            ax.set_yscale("log")
            tick_values = {
                "equity": [1.0, 1.1, 1.2, 1.3, 1.4],
                "crypto": [1.0, 2.0, 4.0, 8.0],
                "combined": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
            }[family]
            ax.yaxis.set_major_locator(FixedLocator(tick_values))
            ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"${value:g}"))
            ax.yaxis.set_minor_formatter(NullFormatter())
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            _style_axis(ax)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.035),
            ncol=5,
            frameon=False,
            fontsize=8,
        )
        fig.suptitle("Monthly funds produced sharply different wealth paths", y=0.992)
        fig.subplots_adjust(top=0.94, bottom=0.14, hspace=0.48)
        _finish_figure(fig)
    context = FigureContext(
        title="Net growth of one dollar across the fifteen monthly funds",
        note=(
            "Weights use fixed prior-only windows and first-of-month rebalancing. "
            "The logarithmic scale permits comparison despite the wider crypto range."
        ),
        source=SOURCE,
        sample=_sample(suite),
        units="Growth of $1, net of 10 basis-point turnover costs",
    )
    return fig, axes, context


def _drawdown_figure(
    suite: PortfolioSuite,
) -> tuple[plt.Figure, list[plt.Axes], FigureContext]:
    subset = suite.fund_returns.loc[
        suite.fund_returns["asset_family"].eq("combined")
    ].copy()
    subset["date"] = pd.to_datetime(subset["date"])
    with plt.rc_context(_stockist_rc()):
        fig, ax = plt.subplots(figsize=(6.27, 3.75))
        for method, method_frame in subset.groupby("method", sort=False):
            ax.plot(
                method_frame["date"],
                method_frame["drawdown_net"],
                color=METHOD_COLORS[method],
                linewidth=1.15,
                alpha=0.85,
                label=METHOD_LABELS[method],
            )
        ax.axhline(0, color=RULE, linewidth=0.8)
        ax.set_title("Risk rules reduced the deepest combined-fund losses", loc="left")
        ax.set_xlabel("Date")
        ax.set_ylabel("Drawdown")
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.19),
            frameon=False,
            fontsize=8,
            ncol=5,
        )
        _style_axis(ax)
        fig.subplots_adjust(bottom=0.31, top=0.88)
        _finish_figure(fig)
    context = FigureContext(
        title="Net drawdowns of the combined monthly funds",
        note=(
            "Drawdown is each fund's percentage decline from its prior net wealth peak. "
            "Lower lines indicate deeper historical losses."
        ),
        source=SOURCE,
        sample=_sample(suite),
        units="Percentage drawdown from prior peak",
    )
    return fig, [ax], context


def _risk_return_figure(
    suite: PortfolioSuite,
) -> tuple[plt.Figure, list[plt.Axes], FigureContext]:
    metrics = suite.performance_metrics.copy()
    with plt.rc_context(_stockist_rc()):
        fig, axes_array = plt.subplots(1, 3, figsize=(6.27, 3.75))
        axes = list(axes_array)
        for ax, family in zip(axes, ("equity", "crypto", "combined"), strict=True):
            family_metrics = metrics.loc[metrics["asset_family"].eq(family)]
            for row in family_metrics.itertuples(index=False):
                ax.scatter(
                    100 * row.annualized_volatility,
                    100 * row.annualized_return,
                    s=48,
                    color=METHOD_COLORS[row.method],
                    edgecolor=CANVAS,
                    linewidth=0.7,
                    zorder=3,
                )
                short_label = {
                    "equal_weight": "EW",
                    "minimum_variance": "Min Var",
                    "risk_parity": "Risk Parity",
                    "maximum_sharpe": "Max Sharpe",
                    "hierarchical_risk_parity": "HRP",
                }[row.method]
                offsets = {
                    ("equity", "equal_weight"): (-20, 8),
                    ("equity", "minimum_variance"): (4, 5),
                    ("equity", "risk_parity"): (4, 8),
                    ("equity", "maximum_sharpe"): (-62, -17),
                    ("equity", "hierarchical_risk_parity"): (4, -16),
                    ("crypto", "equal_weight"): (4, -16),
                    ("crypto", "minimum_variance"): (4, 8),
                    ("crypto", "risk_parity"): (4, 8),
                    ("crypto", "maximum_sharpe"): (4, -17),
                    ("crypto", "hierarchical_risk_parity"): (-27, -17),
                    ("combined", "equal_weight"): (-20, 8),
                    ("combined", "minimum_variance"): (4, 5),
                    ("combined", "risk_parity"): (4, 8),
                    ("combined", "maximum_sharpe"): (4, -20),
                    ("combined", "hierarchical_risk_parity"): (4, -16),
                }[(family, row.method)]
                ax.annotate(
                    short_label,
                    (100 * row.annualized_volatility, 100 * row.annualized_return),
                    xytext=offsets,
                    textcoords="offset points",
                    fontsize=7.2,
                    color=INK,
                )
            ax.set_title(FAMILY_LABELS[family], loc="left", fontsize=10)
            ax.set_xlabel("Annualised volatility (%)")
            ax.set_ylabel("Annualised net return (%)")
            ax.margins(x=0.30, y=0.20)
            _style_axis(ax)
        fig.suptitle("Higher estimated complexity did not guarantee higher net return", y=0.98)
        fig.subplots_adjust(left=0.09, right=0.99, bottom=0.24, top=0.82, wspace=0.42)
        _finish_figure(fig)
    context = FigureContext(
        title="Annualised net return and volatility across monthly funds",
        note=(
            "Each point is one asset-family and portfolio-method fund. Returns are CAGR; "
            "volatility is the annualised standard deviation of daily net returns."
        ),
        source=SOURCE,
        sample=_sample(suite),
        units="Annualised percentage return and volatility",
    )
    return fig, axes, context


def _sharpe_bar_figure(
    suite: PortfolioSuite,
) -> tuple[plt.Figure, list[plt.Axes], FigureContext]:
    metrics = suite.performance_metrics.copy()
    families = ("equity", "crypto", "combined")
    methods = (
        "equal_weight",
        "minimum_variance",
        "risk_parity",
        "maximum_sharpe",
        "hierarchical_risk_parity",
    )
    lookup = metrics.set_index(["asset_family", "method"])["net_sharpe_ratio"]
    group_positions = np.arange(len(families), dtype=float)
    bar_width = 0.15
    offsets = (np.arange(len(methods), dtype=float) - 2) * bar_width
    with plt.rc_context(_stockist_rc()):
        fig, ax = plt.subplots(figsize=(6.27, 3.75))
        for method, offset in zip(methods, offsets, strict=True):
            values = [float(lookup.loc[(family, method)]) for family in families]
            bars = ax.bar(
                group_positions + offset,
                values,
                width=bar_width * 0.9,
                color=METHOD_COLORS[method],
                label=METHOD_LABELS[method],
                zorder=3,
            )
            ax.bar_label(
                bars,
                labels=[f"{value:.2f}" for value in values],
                padding=2,
                fontsize=7.2,
                color=SECONDARY_INK,
            )
        ax.set_xlabel("Asset family")
        ax.set_ylabel("Net Sharpe ratio")
        ax.set_xticks(group_positions, [FAMILY_LABELS[family] for family in families])
        ax.set_ylim(0, max(1.18, float(lookup.max()) + 0.12))
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.19),
            frameon=False,
            fontsize=7.4,
            ncol=3,
        )
        _style_axis(ax)
        fig.suptitle(
            "Out-of-sample net Sharpe by fund family and method",
            x=0.09,
            y=0.975,
            ha="left",
        )
        fig.text(
            0.09,
            0.91,
            "Higher is better · 0% risk-free rate · after simulated trading costs",
            ha="left",
            va="top",
            fontsize=8,
            color=SECONDARY_INK,
        )
        fig.subplots_adjust(left=0.10, right=0.99, bottom=0.30, top=0.82)
        _finish_figure(fig)
    context = FigureContext(
        title="Out-of-sample net Sharpe ratio by fund family and method",
        note=(
            "Bars compare the fifteen primary monthly funds after the 10 basis-point "
            "turnover-cost assumption. Sharpe uses a 0% annual risk-free rate. Equity "
            "and Combined use 252-day annualisation; Crypto uses 365-day annualisation. "
            "Higher historical Sharpe is not a forecast of future performance."
        ),
        source=SOURCE,
        sample=_sample(suite),
        units="Net Sharpe ratio",
    )
    return fig, [ax], context


def _weight_history_figure(
    suite: PortfolioSuite, sector_source: pd.DataFrame
) -> tuple[plt.Figure, list[plt.Axes], FigureContext]:
    with plt.rc_context(_stockist_rc()):
        fig, axes_array = plt.subplots(
            2, 3, sharex=True, sharey=True, figsize=(6.27, 5.25)
        )
        axes = list(axes_array.flat)
        methods = (
            "equal_weight",
            "minimum_variance",
            "risk_parity",
            "maximum_sharpe",
            "hierarchical_risk_parity",
        )
        category_order: tuple[str, ...] | None = None
        for ax, method in zip(
            axes[: len(methods)],
            methods,
            strict=True,
        ):
            history = allocation_history(
                suite.fund_weights,
                f"combined_{method}",
                sector_source,
            )
            if category_order is None:
                category_order = history.category_order
            elif history.category_order != category_order:
                raise PortfolioExhibitError(
                    "Combined methods must share one sector display order"
                )
            panel = (
                history.data.pivot_table(
                    index="rebalance_date",
                    columns="category",
                    values="target_weight",
                    aggfunc="sum",
                    fill_value=0,
                )
                .reindex(columns=category_order, fill_value=0)
            )
            ax.stackplot(
                panel.index,
                *[panel[column] for column in category_order],
                labels=[SECTOR_LABELS[category] for category in category_order],
                colors=[SECTOR_COLORS[category] for category in category_order],
                alpha=0.95,
                linewidth=0,
            )
            ax.set_title(METHOD_LABELS[method], loc="left", fontsize=9)
            ax.set_xlabel("Rebalance date")
            ax.set_ylabel("Target weight")
            ax.set_ylim(0, 1)
            ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            _style_axis(ax)
        axes[-1].set_visible(False)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.035),
            ncol=4,
            frameon=False,
            fontsize=7.0,
        )
        fig.suptitle(
            "Combined-fund sector exposures changed by method and month", y=0.985
        )
        fig.subplots_adjust(
            left=0.10,
            right=0.99,
            bottom=0.22,
            top=0.90,
            hspace=0.34,
            wspace=0.32,
        )
        _finish_figure(fig)
    context = FigureContext(
        title="Monthly sector-allocation history for the five combined funds",
        note=(
            "Each band is a supplied equity sector's share of the target fund, with all "
            "cryptoassets shown as one Crypto band. Bands sum to 100% on every rebalance "
            "date, so a widening band means that method allocated more to that sector. "
            "Weights are monthly targets before daily drift."
        ),
        source=SOURCE,
        sample=_sample(suite),
        units="Share of target portfolio weight",
    )
    return fig, axes[: len(methods)], context


def generate_portfolio_exhibits(
    suite: PortfolioSuite,
    output_dir: Path,
    tables_dir: Path,
    sector_source: pd.DataFrame,
) -> PortfolioExhibits:
    """Generate, validate, and export the five core Phase 2 exhibits."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    builders = (
        ("fund_growth", _growth_figure, "portrait_full"),
        ("combined_fund_drawdowns", _drawdown_figure, "full_width"),
        ("fund_risk_return", _risk_return_figure, "full_width"),
        ("fund_sharpe_by_family", _sharpe_bar_figure, "full_width"),
        (
            "combined_weight_history",
            lambda selected_suite: _weight_history_figure(
                selected_suite, sector_source
            ),
            "portrait_tall",
        ),
    )
    figure_paths: list[Path] = []
    caption_paths: list[Path] = []
    validation_records: list[dict[str, str]] = []
    for stem, builder, spec in builders:
        fig, axes, context = builder(suite)
        paths, records = _export_validated(
            fig,
            axes,
            output_dir=output_dir,
            stem=stem,
            context=context,
            spec=spec,
        )
        figure_paths.append(paths["png"].resolve())
        caption_paths.append(paths["caption"].resolve())
        validation_records.extend(records)
    validation = pd.DataFrame.from_records(validation_records)
    validation_path = tables_dir / "portfolio_figure_validation.csv"
    validation.to_csv(validation_path, index=False)
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise PortfolioExhibitError(f"portfolio figure validation failed: {failures}")
    return PortfolioExhibits(figure_paths, caption_paths, validation)


__all__ = [
    "PortfolioExhibitError",
    "PortfolioExhibits",
    "generate_portfolio_exhibits",
]
