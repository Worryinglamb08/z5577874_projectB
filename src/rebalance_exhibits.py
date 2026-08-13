"""Report-ready exhibit for the controlled rebalance-frequency experiment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
import pandas as pd
from cycler import cycler
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter, NullLocator

from fintools.figures import (
    FigureContext,
    export_word_figure,
    validate_axes_labels,
    validate_display_labels,
    validate_figure_context,
    validate_image_not_blank,
    validate_markers_within_axes,
    validate_no_tick_label_overlap,
    validate_titles_within_canvas,
    validate_word_readability,
    word_figure_spec,
)
from fintools.figures.theme import theme_rc
from src.portfolio_exhibits import CANVAS, INK, RULE, SECONDARY_INK, SOURCE
from src.rebalance_experiments import RebalanceExperimentResult

SCHEDULE_COLORS: Final = {
    "monthly": "#0F766E",
    "biweekly": "#0072B2",
    "weekly": "#E69F00",
    "daily": "#C2410C",
}
LABEL_OFFSETS: Final = {
    "monthly": (5, -13),
    "biweekly": (5, 7),
    "weekly": (5, -13),
    "daily": (5, 7),
}


class RebalanceExhibitError(ValueError):
    """Raised when the frequency exhibit fails rendered checks."""


@dataclass(frozen=True)
class RebalanceExhibit:
    """Exported figure, caption, and validation evidence."""

    figure_path: Path
    caption_path: Path
    validation: pd.DataFrame


def _stockist_rc() -> dict[str, object]:
    settings = theme_rc("word_a4", style="ft", ft_background=False)
    settings.update(
        {
            "axes.edgecolor": RULE,
            "axes.labelcolor": INK,
            "axes.prop_cycle": cycler(color=tuple(SCHEDULE_COLORS.values())),
            "axes.titlecolor": INK,
            "figure.constrained_layout.use": False,
            "figure.facecolor": CANVAS,
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


def _figure(
    result: RebalanceExperimentResult,
) -> tuple[plt.Figure, list[plt.Axes], FigureContext]:
    metrics = result.frequency_metrics.copy()
    with plt.rc_context(_stockist_rc()):
        fig, axes_array = plt.subplots(1, 2, sharey=True, figsize=(6.27, 3.75))
        axes = list(axes_array)
        for ax, method in zip(
            axes, ("risk_parity", "maximum_sharpe"), strict=True
        ):
            subset = metrics.loc[metrics["method"].eq(method)].copy()
            monthly_sharpe = subset.loc[
                subset["rebalance_schedule"].eq("monthly"), "sharpe_ratio"
            ].item()
            ax.axhline(
                monthly_sharpe,
                color=RULE,
                linestyle="--",
                linewidth=0.9,
                zorder=1,
            )
            for row in subset.itertuples(index=False):
                turnover_pct = 100 * row.annualized_turnover
                ax.scatter(
                    turnover_pct,
                    row.sharpe_ratio,
                    s=62,
                    color=SCHEDULE_COLORS[row.rebalance_schedule],
                    edgecolor=CANVAS,
                    linewidth=0.8,
                    zorder=3,
                )
                ax.annotate(
                    row.schedule_label,
                    (turnover_pct, row.sharpe_ratio),
                    xytext=LABEL_OFFSETS[row.rebalance_schedule],
                    textcoords="offset points",
                    fontsize=7.2,
                    color=INK,
                )
            ax.set_title(row.method_label, loc="left", fontsize=10)
            ax.set_xlabel("Annualised turnover (%)")
            ax.set_ylabel("Net Sharpe ratio")
            ax.set_xscale("log")
            tick_values = (
                [60, 100, 200]
                if method == "risk_parity"
                else [300, 500, 1_000, 1_500]
            )
            ax.xaxis.set_major_locator(FixedLocator(tick_values))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:.0f}%"))
            ax.xaxis.set_minor_locator(NullLocator())
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.tick_params(axis="x", labelsize=8)
            ax.set_ylim(0.74, 0.92)
            ax.margins(x=0.28)
            _style_axis(ax)
        fig.suptitle("Frequency raised turnover more consistently than Sharpe", y=0.98)
        fig.text(
            0.01,
            0.004,
            (
                f"Source: {SOURCE}. Combined funds; 10 bp turnover cost; "
                "higher-frequency paths are diagnostic."
            ),
            ha="left",
            va="bottom",
            fontsize=7,
            color=SECONDARY_INK,
        )
        fig.subplots_adjust(left=0.10, right=0.99, bottom=0.24, top=0.82, wspace=0.28)
    dates = pd.to_datetime(result.experiment_returns["date"])
    context = FigureContext(
        title="Turnover and net Sharpe across rebalance-frequency experiments",
        note=(
            "Each panel holds the combined universe, 252-observation trailing window, "
            "constraints, first live date, and optimiser fixed. Dashed lines show the "
            "monthly net Sharpe. Daily, every-5-day, and every-10-day paths are "
            "diagnostics rather than assignment-compliant product funds."
        ),
        source=SOURCE,
        sample=f"{dates.min():%Y-%m-%d} to {dates.max():%Y-%m-%d}",
        units="Annualised turnover (%) and net Sharpe ratio at 10 basis points",
    )
    return fig, axes, context


def generate_rebalance_exhibit(
    result: RebalanceExperimentResult,
    *,
    output_dir: Path,
    tables_dir: Path,
) -> RebalanceExhibit:
    """Generate, export, and validate the Phase 3 trade-off figure."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    fig, axes, context = _figure(result)
    spec = word_figure_spec("full_width")
    paths = export_word_figure(
        fig,
        output_dir,
        "rebalance_frequency_tradeoff",
        context=context,
        spec=spec,
    )
    issues = [
        *validate_figure_context(context),
        *validate_titles_within_canvas(fig),
        *validate_word_readability(fig, width_inches=spec.width_inches, min_font_size=7.0),
        *validate_image_not_blank(paths["png"]),
    ]
    for ax in axes:
        issues.extend(validate_axes_labels(ax))
        issues.extend(validate_display_labels(ax))
        issues.extend(validate_no_tick_label_overlap(ax, axis="x"))
        issues.extend(validate_no_tick_label_overlap(ax, axis="y"))
        issues.extend(validate_markers_within_axes(ax))
    validation = pd.DataFrame.from_records(
        [
            {
                "figure": "rebalance_frequency_tradeoff",
                "status": "fail",
                "check": issue.code,
                "detail": issue.message,
            }
            for issue in issues
        ]
        if issues
        else [
            {
                "figure": "rebalance_frequency_tradeoff",
                "status": "pass",
                "check": "all_selected_checks",
                "detail": "Context, labels, ticks, readability, markers, and image passed.",
            }
        ]
    )
    validation.to_csv(
        tables_dir / "rebalance_frequency_figure_validation.csv", index=False
    )
    plt.close(fig)
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise RebalanceExhibitError(f"frequency figure validation failed: {failures}")
    return RebalanceExhibit(
        figure_path=paths["png"].resolve(),
        caption_path=paths["caption"].resolve(),
        validation=validation,
    )


__all__ = [
    "RebalanceExhibit",
    "RebalanceExhibitError",
    "generate_rebalance_exhibit",
]
