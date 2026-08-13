"""Word/A4-ready before-versus-after exhibit for the Phase 5 fusion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

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
from src.fusion import FusionResult
from src.portfolio_exhibits import (
    CANVAS,
    INK,
    RULE,
    SECONDARY_INK,
    SOURCE,
    _stockist_rc,
    _style_axis,
)

BASE_COLOR = "#475569"
FUSION_COLOR = "#CC79A7"


class FusionExhibitError(ValueError):
    """Raised when the fusion exhibit fails its selected rendered checks."""


@dataclass(frozen=True)
class FusionExhibit:
    """Exported fusion figure, caption, and validation evidence."""

    figure_path: Path
    caption_path: Path
    validation: pd.DataFrame


def generate_fusion_exhibit(
    result: FusionResult, *, output_dir: Path, tables_dir: Path
) -> FusionExhibit:
    """Compare net growth of the identical base and coverage-aware funds."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    selected = result.fusion_returns.loc[
        result.fusion_returns["variant"].isin(["base", "coverage_aware_finance"])
    ].copy()
    selected["date"] = pd.to_datetime(selected["date"])
    pivot = selected.pivot(
        index="date", columns="variant", values="growth_of_1_net"
    ).sort_index()
    if list(pivot.columns) != ["base", "coverage_aware_finance"]:
        raise FusionExhibitError("fusion figure requires base and coverage-aware paths")
    sample = f"{pivot.index.min():%Y-%m-%d} to {pivot.index.max():%Y-%m-%d}"
    base_label = selected.loc[selected["variant"].eq("base"), "variant_label"].iloc[0]

    with plt.rc_context(_stockist_rc()):
        fig, ax = plt.subplots(figsize=(6.27, 3.7))
        ax.plot(
            pivot.index,
            pivot["base"],
            color=BASE_COLOR,
            linewidth=1.5,
            linestyle="--",
            label=base_label,
        )
        ax.plot(
            pivot.index,
            pivot["coverage_aware_finance"],
            color=FUSION_COLOR,
            linewidth=1.8,
            label="Coverage-aware sentiment tilt",
        )
        ax.axhline(1.0, color=RULE, linewidth=0.8, zorder=0)
        ax.set_title("Coverage-aware sentiment did not improve compounding", loc="left")
        ax.set_xlabel("Date")
        ax.set_ylabel("Growth of $1, net")
        ax.set_yscale("log")
        lower = np.floor(pivot.min().min() * 20) / 20
        upper = np.ceil(pivot.max().max() * 20) / 20
        ticks = np.arange(lower, upper + 0.001, 0.05)
        ax.set_ylim(lower * 0.995, upper * 1.005)
        ax.yaxis.set_major_locator(FixedLocator(ticks))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:.2f}"))
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.legend(loc="upper left", frameon=False, fontsize=8)
        _style_axis(ax)
        ax.set_facecolor(CANVAS)
        ax.tick_params(colors=SECONDARY_INK)
        ax.title.set_color(INK)
        fig.text(
            0.01,
            0.008,
            (
                f"Source: {SOURCE}. Monthly historical simulation; 10 bp turnover "
                "cost; signal lagged one observed trading day."
            ),
            ha="left",
            va="bottom",
            fontsize=7,
            color=SECONDARY_INK,
        )
        fig.subplots_adjust(left=0.12, right=0.985, bottom=0.19, top=0.90)

    context = FigureContext(
        title="Coverage-aware sentiment fusion versus its base equity fund",
        note=(
            "Net growth of $1 for the same Equity Minimum Variance method, monthly "
            "rebalance dates, eligible assets, constraints, sample, and 10 bp cost "
            "assumption. The augmented target applies a fixed 0.20 exponential tilt "
            "to the prior observed day's finance sentiment multiplied by coverage "
            "confidence. The comparison does not establish future performance."
        ),
        source=SOURCE,
        sample=sample,
        units="Growth of $1, net of simulated transaction costs",
    )
    paths = export_word_figure(
        fig, output_dir, "fusion_growth_comparison", context=context, spec="full_width"
    )
    spec = word_figure_spec("full_width")
    issues = [
        *validate_figure_context(context),
        *validate_titles_within_canvas(fig),
        *validate_word_readability(fig, width_inches=spec.width_inches, min_font_size=7.0),
        *validate_image_not_blank(paths["png"]),
        *validate_axes_labels(ax),
        *validate_display_labels(ax),
        *validate_no_tick_label_overlap(ax, axis="x"),
        *validate_no_tick_label_overlap(ax, axis="y"),
    ]
    validation = pd.DataFrame.from_records(
        [
            {
                "figure": "fusion_growth_comparison",
                "status": "fail",
                "check": issue.code,
                "detail": issue.message,
            }
            for issue in issues
        ]
        if issues
        else [
            {
                "figure": "fusion_growth_comparison",
                "status": "pass",
                "check": "all_selected_checks",
                "detail": "Context, labels, layout, ticks, readability, and image passed.",
            }
        ]
    )
    plt.close(fig)
    validation_path = tables_dir / "fusion_figure_validation.csv"
    validation.to_csv(validation_path, index=False)
    if validation["status"].eq("fail").any():
        raise FusionExhibitError(
            f"fusion figure validation failed: {validation.to_dict('records')}"
        )
    return FusionExhibit(
        figure_path=paths["png"].resolve(),
        caption_path=paths["caption"].resolve(),
        validation=validation,
    )


__all__ = ["FusionExhibit", "FusionExhibitError", "generate_fusion_exhibit"]
