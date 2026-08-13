"""Report-ready standalone sector-sentiment exhibit for Phase 4."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler

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
from src.portfolio_exhibits import CANVAS, INK, RULE, SECONDARY_INK, SOURCE
from src.sentiment import ROLLING_DISPLAY_WINDOW, SentimentResult

RAW_COLOR = "#94A3B8"
ROLLING_COLOR = "#0F766E"


class SentimentExhibitError(ValueError):
    """Raised when the sentiment exhibit fails selected rendered checks."""


@dataclass(frozen=True)
class SentimentExhibit:
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
            "axes.prop_cycle": cycler(color=(RAW_COLOR, ROLLING_COLOR)),
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
    ax.grid(axis="y", alpha=0.45, linewidth=0.6)
    ax.grid(axis="x", visible=False)


def _figure(
    result: SentimentResult,
) -> tuple[plt.Figure, list[plt.Axes], FigureContext]:
    index = result.sector_index.copy()
    index["date"] = pd.to_datetime(index["date"])
    index = index.sort_values(["sector", "date"], kind="stable")
    index["finance_sentiment_21d"] = index.groupby("sector", sort=False)[
        "finance_sentiment_index"
    ].transform(
        lambda values: values.rolling(
            ROLLING_DISPLAY_WINDOW, min_periods=ROLLING_DISPLAY_WINDOW
        ).mean()
    )
    sectors = sorted(index["sector"].unique())
    if len(sectors) != 10:
        raise SentimentExhibitError(f"expected 10 sectors; observed {len(sectors)}")
    raw_limit = float(index["finance_sentiment_index"].abs().max())
    y_limit = min(1.0, max(0.2, np.ceil(raw_limit * 10) / 10))

    with plt.rc_context(_stockist_rc()):
        fig, axes_array = plt.subplots(5, 2, sharex=True, sharey=True, figsize=(6.27, 8.0))
        axes = list(axes_array.ravel())
        legend_handles = None
        for position, (ax, sector) in enumerate(zip(axes, sectors, strict=True)):
            subset = index.loc[index["sector"].eq(sector)]
            raw_line = ax.plot(
                subset["date"],
                subset["finance_sentiment_index"],
                color=RAW_COLOR,
                linewidth=0.55,
                alpha=0.35,
                label="Daily sector index",
            )[0]
            rolling_line = ax.plot(
                subset["date"],
                subset["finance_sentiment_21d"],
                color=ROLLING_COLOR,
                linewidth=1.2,
                label="21-day rolling mean",
            )[0]
            if legend_handles is None:
                legend_handles = [raw_line, rolling_line]
            ax.axhline(0.0, color=RULE, linewidth=0.7, zorder=0)
            ax.set_title(sector, loc="left", fontsize=8.5, pad=3)
            ax.set_xlabel("Date")
            ax.set_ylabel("Sentiment score")
            ax.xaxis.label.set_visible(False)
            ax.yaxis.label.set_visible(False)
            ax.set_ylim(-y_limit, y_limit)
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            ax.tick_params(axis="both", labelsize=7)
            _style_axis(ax)

        fig.suptitle("Finance sentiment varied across equity sectors", y=0.995)
        fig.supylabel("Sentiment score", x=0.012, fontsize=9)
        fig.supxlabel("Date", y=0.032, fontsize=9)
        fig.legend(
            legend_handles,
            ["Daily sector index", "21-day rolling mean"],
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
                f"Source: {SOURCE}. Finance-adjusted VADER; ticker-equal-weight "
                "sector indices; no-news ticker-days = 0."
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
        title="Finance-adjusted VADER sentiment across equity sectors",
        note=(
            "The daily index first averages headlines within ticker-day, assigns zero "
            "to ticker-days without news, then equal-weights the five tickers in each "
            "sector. The solid line is a 21-observed-day rolling mean shown for "
            "readability; the faint line is the underlying daily index. Trading uses "
            "the separately stored one-day-lagged value, never the same-day score."
        ),
        source=SOURCE,
        sample=f"{index['date'].min():%Y-%m-%d} to {index['date'].max():%Y-%m-%d}",
        units="VADER compound score on [-1, 1]",
    )
    return fig, axes, context


def generate_sentiment_exhibit(
    result: SentimentResult,
    *,
    output_dir: Path,
    tables_dir: Path,
) -> SentimentExhibit:
    """Generate, export, and validate the Phase 4 sector time-series figure."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    fig, axes, context = _figure(result)
    spec = word_figure_spec("portrait_full")
    paths = export_word_figure(
        fig,
        output_dir,
        "sector_sentiment_index",
        context=context,
        spec=spec,
    )
    issues = [
        *validate_figure_context(context),
        *validate_titles_within_canvas(fig),
        *validate_word_readability(
            fig, width_inches=spec.width_inches, min_font_size=6.5
        ),
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
                "figure": "sector_sentiment_index",
                "status": "fail",
                "check": issue.code,
                "detail": issue.message,
            }
            for issue in issues
        ]
        if issues
        else [
            {
                "figure": "sector_sentiment_index",
                "status": "pass",
                "check": "all_selected_checks",
                "detail": "Context, labels, layout, ticks, readability, and image passed.",
            }
        ]
    )
    validation_path = tables_dir / "sentiment_figure_validation.csv"
    validation.to_csv(validation_path, index=False)
    plt.close(fig)
    if validation["status"].eq("fail").any():
        failures = validation.loc[validation["status"].eq("fail")].to_dict("records")
        raise SentimentExhibitError(f"sentiment figure validation failed: {failures}")
    return SentimentExhibit(
        figure_path=paths["png"].resolve(),
        caption_path=paths["caption"].resolve(),
        validation=validation,
    )


__all__ = [
    "SentimentExhibit",
    "SentimentExhibitError",
    "generate_sentiment_exhibit",
]
