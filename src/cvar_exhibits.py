"""Report-ready comparison figure for the isolated minimum-CVaR prototype."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

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
from src.portfolios import FAMILY_LABELS, METHOD_LABELS

INK = "#0F172A"
SECONDARY = "#475569"
RULE = "#CBD5E1"
METHOD_COLORS = {
    "minimum_variance": "#0072B2",
    "hierarchical_risk_parity": "#7C3AED",
    "conditional_value_at_risk": "#C2410C",
}
SOURCE = "Course-provided project_data.zip; Stockist Funds calculations"


def generate_cvar_prototype_figure(
    metrics: pd.DataFrame,
    *,
    output_dir: Path,
    tables_dir: Path,
) -> list[Path]:
    """Export and validate a four-measure CVaR comparison scorecard."""
    families = ("equity", "crypto", "combined")
    methods = (
        "minimum_variance",
        "hierarchical_risk_parity",
        "conditional_value_at_risk",
    )
    lookup = metrics.set_index(["asset_family", "method"])
    panels = (
        ("sharpe_ratio", "Net Sharpe ratio", 1.0, False),
        ("oos_daily_cvar_95", "Out-of-sample daily CVaR", 100.0, True),
        ("maximum_drawdown", "Maximum drawdown magnitude", -100.0, True),
        ("average_rebalance_turnover", "Average monthly turnover", 100.0, True),
    )
    settings = theme_rc("word_a4", style="ft", ft_background=False)
    settings.update(
        {
            "axes.edgecolor": RULE,
            "axes.labelcolor": INK,
            "axes.labelsize": 8.5,
            "axes.titlecolor": INK,
            "axes.titlesize": 9,
            "figure.facecolor": "#FFFFFF",
            "figure.constrained_layout.use": False,
            "figure.titlesize": 15,
            "grid.color": RULE,
            "savefig.facecolor": "#FFFFFF",
            "text.color": INK,
            "xtick.color": SECONDARY,
            "xtick.labelsize": 8,
            "ytick.color": SECONDARY,
            "ytick.labelsize": 8,
        }
    )
    positions = np.arange(len(families), dtype=float)
    width = 0.24
    with plt.rc_context(settings):
        fig, axes_array = plt.subplots(2, 2, figsize=(6.27, 5.45))
        axes = list(axes_array.flat)
        for ax, (field, title, scale, lower_is_better) in zip(
            axes, panels, strict=True
        ):
            for index, method in enumerate(methods):
                values = [
                    float(lookup.loc[(family, method), field]) * scale
                    for family in families
                ]
                offset = (index - 1) * width
                bars = ax.bar(
                    positions + offset,
                    values,
                    width=width * 0.9,
                    color=METHOD_COLORS[method],
                    label=METHOD_LABELS[method],
                    zorder=3,
                )
                ax.bar_label(
                    bars,
                    labels=[
                        f"{value:.2f}" if scale == 1.0 else f"{value:.1f}"
                        for value in values
                    ],
                    padding=2 + 7 * index,
                    fontsize=7.0,
                    color=SECONDARY,
                )
            qualifier = "Lower is better" if lower_is_better else "Higher is better"
            ax.set_title(f"{title}\n{qualifier}", loc="left", fontsize=9)
            ax.set_xlabel("Asset family")
            ax.set_ylabel(title)
            ax.set_xticks(
                positions,
                [FAMILY_LABELS[family] for family in families],
            )
            ax.set_ylim(bottom=0)
            ax.margins(y=0.22)
            if scale != 1.0:
                ax.yaxis.set_major_formatter(PercentFormatter(100, decimals=0))
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(axis="y", alpha=0.55, linewidth=0.7)
            ax.grid(axis="x", visible=False)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.045),
            ncol=3,
            frameon=False,
            fontsize=7.5,
        )
        fig.suptitle(
            "Minimum CVaR did not beat Minimum Variance",
            y=0.985,
        )
        fig.text(
            0.01,
            0.003,
            f"Source: {SOURCE}. Monthly walk-forward simulation, 2021-2023; "
            "net of 10 bp turnover costs.",
            ha="left",
            va="bottom",
            fontsize=7,
            color=SECONDARY,
        )
        fig.subplots_adjust(
            left=0.11,
            right=0.99,
            bottom=0.18,
            top=0.88,
            hspace=0.48,
            wspace=0.34,
        )

    context = FigureContext(
        title="Out-of-sample minimum-CVaR prototype comparison",
        note=(
            "Minimum CVaR minimises the average loss beyond the trailing 95% loss "
            "threshold. It is compared with Minimum Variance and Hierarchical Risk "
            "Parity using identical monthly dates, constraints and trading costs. "
            "Daily CVaR and drawdown are shown as positive loss magnitudes."
        ),
        source=SOURCE,
        sample="2021-01-01 to 2023-12-31 (family-specific observed calendars)",
        units="Sharpe ratio and percentage loss, drawdown, and turnover",
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    paths = export_word_figure(
        fig,
        output_dir,
        "cvar_prototype_comparison",
        context=context,
        spec="portrait_tall",
    )
    spec = word_figure_spec("portrait_tall")
    issues = [
        *validate_figure_context(context),
        *validate_titles_within_canvas(fig),
        *validate_word_readability(
            fig,
            width_inches=spec.width_inches,
            min_font_size=7.0,
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
                "figure": "cvar_prototype_comparison",
                "status": "fail",
                "check": issue.code,
                "detail": issue.message,
            }
            for issue in issues
        ]
        if issues
        else [
            {
                "figure": "cvar_prototype_comparison",
                "status": "pass",
                "check": "all_selected_checks",
                "detail": "Context, labels, layout, ticks, readability, and image passed.",
            }
        ]
    )
    validation_path = tables_dir / "cvar_prototype_figure_validation.csv"
    validation.to_csv(validation_path, index=False)
    plt.close(fig)
    if validation["status"].eq("fail").any():
        raise ValueError(
            f"CVaR prototype figure validation failed: {validation.to_dict('records')}"
        )
    return [paths["png"], paths["caption"], validation_path]


__all__ = ["generate_cvar_prototype_figure"]
