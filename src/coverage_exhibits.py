"""Word/A4-ready evidence-quality exhibit for sector sentiment coverage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

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
from src.portfolio_exhibits import CANVAS, INK, RULE, SECONDARY_INK, SOURCE, _stockist_rc
from src.sentiment import ROLLING_DISPLAY_WINDOW, SentimentResult

RAW_COLOR = "#94A3B8"
ROLLING_COLOR = "#0072B2"


class CoverageExhibitError(ValueError):
    """Raised when the coverage-confidence exhibit fails selected checks."""


@dataclass(frozen=True)
class CoverageExhibit:
    """Exported coverage figure, caption, and validation evidence."""

    figure_path: Path
    caption_path: Path
    validation: pd.DataFrame


def _figure(result: SentimentResult) -> tuple[plt.Figure, list[plt.Axes], FigureContext]:
    data = result.sector_index[
        ["date", "sector", "coverage_confidence"]
    ].copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values(["sector", "date"], kind="stable")
    data["confidence_21d"] = data.groupby("sector", sort=False)[
        "coverage_confidence"
    ].transform(
        lambda values: values.rolling(
            ROLLING_DISPLAY_WINDOW, min_periods=ROLLING_DISPLAY_WINDOW
        ).mean()
    )
    sectors = sorted(data["sector"].unique())
    if len(sectors) != 10:
        raise CoverageExhibitError(f"expected 10 sectors; observed {len(sectors)}")

    with plt.rc_context(_stockist_rc()):
        fig, axes_array = plt.subplots(5, 2, sharex=True, sharey=True, figsize=(6.27, 8.0))
        axes = list(axes_array.ravel())
        handles = None
        for ax, sector in zip(axes, sectors, strict=True):
            subset = data.loc[data["sector"].eq(sector)]
            raw = ax.plot(
                subset["date"],
                subset["coverage_confidence"],
                color=RAW_COLOR,
                linewidth=0.5,
                alpha=0.28,
                label="Daily confidence",
            )[0]
            rolling = ax.plot(
                subset["date"],
                subset["confidence_21d"],
                color=ROLLING_COLOR,
                linewidth=1.2,
                label="21-day rolling mean",
            )[0]
            if handles is None:
                handles = [raw, rolling]
            ax.set_title(sector, loc="left", fontsize=8.5, pad=3)
            ax.set_xlabel("Date")
            ax.set_ylabel("Coverage confidence")
            ax.xaxis.label.set_visible(False)
            ax.yaxis.label.set_visible(False)
            ax.set_ylim(-0.03, 1.03)
            ax.set_yticks([0.0, 0.5, 1.0], labels=["0", "0.5", "1"])
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            ax.tick_params(axis="both", labelsize=7, colors=SECONDARY_INK)
            ax.set_facecolor(CANVAS)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(RULE)
            ax.spines["bottom"].set_color(RULE)
            ax.grid(axis="y", color=RULE, alpha=0.45, linewidth=0.6)
            ax.grid(axis="x", visible=False)
            ax.title.set_color(INK)

        fig.suptitle("Sentiment evidence quality varies by sector and date", y=0.995)
        fig.supylabel("Coverage confidence", x=0.012, fontsize=9)
        fig.supxlabel("Date", y=0.032, fontsize=9)
        fig.legend(
            handles,
            ["Daily confidence", "21-day rolling mean"],
            loc="upper center",
            bbox_to_anchor=(0.5, 0.963),
            frameon=False,
            ncol=2,
            fontsize=7.5,
        )
        fig.text(
            0.01,
            0.004,
            (
                f"Source: {SOURCE}. Confidence combines covered-company breadth "
                "and headline-share concentration; no-news days = 0."
            ),
            ha="left",
            va="bottom",
            fontsize=6.8,
            color=SECONDARY_INK,
        )
        fig.subplots_adjust(
            left=0.105,
            right=0.99,
            bottom=0.075,
            top=0.915,
            hspace=0.30,
            wspace=0.17,
        )

    context = FigureContext(
        title="Coverage confidence across equity-sector sentiment indices",
        note=(
            "Confidence equals covered-company breadth multiplied by one minus "
            "headline-share HHI, scaled relative to an equal five-company sector and "
            "clipped to [0, 1]. Zero means no usable news evidence; values near one "
            "indicate broad, comparatively even coverage. Confidence measures evidence "
            "support, not whether the sentiment classification is correct."
        ),
        source=SOURCE,
        sample=f"{data['date'].min():%Y-%m-%d} to {data['date'].max():%Y-%m-%d}",
        units="Confidence score on [0, 1]",
    )
    return fig, axes, context


def generate_coverage_exhibit(
    result: SentimentResult, *, output_dir: Path, tables_dir: Path
) -> CoverageExhibit:
    """Generate and validate the Phase 6 evidence-quality small multiples."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    fig, axes, context = _figure(result)
    spec = word_figure_spec("portrait_full")
    paths = export_word_figure(
        fig,
        output_dir,
        "coverage_confidence_index",
        context=context,
        spec="portrait_full",
    )
    issues = [
        *validate_figure_context(context),
        *validate_titles_within_canvas(fig),
        *validate_word_readability(fig, width_inches=spec.width_inches, min_font_size=6.5),
        *validate_image_not_blank(paths["png"]),
    ]
    for ax in axes:
        issues.extend(validate_axes_labels(ax))
        issues.extend(validate_display_labels(ax))
        issues.extend(validate_no_tick_label_overlap(ax, axis="x"))
        issues.extend(validate_no_tick_label_overlap(ax, axis="y"))
    validation = pd.DataFrame.from_records(
        [
            {
                "figure": "coverage_confidence_index",
                "status": "fail",
                "check": issue.code,
                "detail": issue.message,
            }
            for issue in issues
        ]
        if issues
        else [
            {
                "figure": "coverage_confidence_index",
                "status": "pass",
                "check": "all_selected_checks",
                "detail": "Context, labels, layout, ticks, readability, and image passed.",
            }
        ]
    )
    plt.close(fig)
    validation.to_csv(tables_dir / "coverage_figure_validation.csv", index=False)
    if validation["status"].eq("fail").any():
        raise CoverageExhibitError(
            f"coverage figure validation failed: {validation.to_dict('records')}"
        )
    return CoverageExhibit(
        figure_path=paths["png"].resolve(),
        caption_path=paths["caption"].resolve(),
        validation=validation,
    )


__all__ = ["CoverageExhibit", "CoverageExhibitError", "generate_coverage_exhibit"]
