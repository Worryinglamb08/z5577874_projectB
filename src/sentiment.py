"""Finance-adjusted VADER sentiment and the standalone sector index.

Headlines are scored exactly as supplied: casing, punctuation, negation, and
word order are preserved. Scores are aggregated headline -> ticker-day ->
sector-day. A ticker-day without headlines is an explicit neutral zero, but the
separate ``has_news`` field prevents zero from being mistaken for observed
neutral language. Tradable sector signals are lagged by one observed equity
trading day.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from statistics import stdev
from typing import Final

import numpy as np
import pandas as pd

from src.finance_lexicon import (
    ALL_AVERAGED_FAMILY_SCORES,
    ALL_FAMILY_RATIONALE,
    ALL_FAMILY_VARIANTS,
    EXPANSION_FAMILY_VARIANTS,
    EXPANSION_REVIEW_SCORES,
    FINANCE_LEXICON,
    REVIEW_SCORES,
    REVIEWER_ROLES,
)
from src.news_features import NewsCoverageFeatures

NEUTRAL_THRESHOLD: Final = 0.05
ROLLING_DISPLAY_WINDOW: Final = 21

class SentimentValidationError(ValueError):
    """Raised when sentiment inputs, timing, or output identities are invalid."""


@dataclass(frozen=True)
class SentimentResult:
    """In-memory sentiment panels and compact Phase 4 evidence."""

    headline_scores: pd.DataFrame
    ticker_day_scores: pd.DataFrame
    sector_index: pd.DataFrame
    market_index: pd.DataFrame
    lexicon_audit: pd.DataFrame
    lexicon_panel_scores: pd.DataFrame
    lexicon_panel_summary: pd.DataFrame
    model_summary: pd.DataFrame
    sector_summary: pd.DataFrame
    validation_cases: pd.DataFrame
    expansion_validation_cases: pd.DataFrame
    validation_summary: pd.DataFrame


def _require_columns(frame: pd.DataFrame, required: set[str], dataset: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise SentimentValidationError(f"{dataset} is missing required columns: {missing}")
    if frame.empty:
        raise SentimentValidationError(f"{dataset} is empty")


def _analyzers():
    """Return independent plain and finance-adjusted NLTK VADER analysers."""
    try:
        from nltk.sentiment import SentimentIntensityAnalyzer
    except ImportError as exc:  # pragma: no cover - environment-specific guard
        raise SentimentValidationError(
            "nltk is required for the build; install requirements-dev.txt"
        ) from exc
    try:
        plain = SentimentIntensityAnalyzer()
        finance = SentimentIntensityAnalyzer()
    except LookupError as exc:  # pragma: no cover - environment-specific guard
        raise SentimentValidationError(
            "VADER lexicon is missing; run python -m nltk.downloader vader_lexicon"
        ) from exc
    finance.lexicon.update(FINANCE_LEXICON)
    return plain, finance


def _label(compound: pd.Series) -> pd.Series:
    return pd.Series(
        np.select(
            [compound.ge(NEUTRAL_THRESHOLD), compound.le(-NEUTRAL_THRESHOLD)],
            ["positive", "negative"],
            default="neutral",
        ),
        index=compound.index,
        dtype="string",
    )


def score_headlines(aligned_headlines: pd.DataFrame) -> pd.DataFrame:
    """Score each preserved headline with plain and finance-adjusted VADER.

    The function rejects duplicate ``ticker, headline_date, title`` keys so the
    scoring layer cannot silently double-count a headline if upstream cleaning
    is bypassed.
    """
    required = {
        "headline_date",
        "aligned_trading_date",
        "alignment_status",
        "ticker",
        "sector",
        "title",
    }
    _require_columns(aligned_headlines, required, "aligned_headlines")
    result = aligned_headlines.copy(deep=True)
    if result[list(["ticker", "headline_date", "title"])].isna().any().any():
        raise SentimentValidationError("headline scoring keys must not be missing")
    if result.duplicated(["ticker", "headline_date", "title"]).any():
        raise SentimentValidationError("duplicate ticker-headline_date-title rows remain")
    if result["title"].astype("string").str.strip().eq("").any():
        raise SentimentValidationError("headline titles must not be blank")

    plain, finance = _analyzers()
    titles = result["title"].astype(str)
    plain_scores = pd.DataFrame.from_records(titles.map(plain.polarity_scores))
    finance_scores = pd.DataFrame.from_records(titles.map(finance.polarity_scores))
    plain_scores.index = result.index
    finance_scores.index = result.index
    for component in ("neg", "neu", "pos", "compound"):
        result[f"plain_{component}"] = plain_scores[component].astype(float)
        result[f"finance_{component}"] = finance_scores[component].astype(float)
    result["plain_label"] = _label(result["plain_compound"])
    result["finance_label"] = _label(result["finance_compound"])
    result["finance_score_change"] = (
        result["finance_compound"] - result["plain_compound"]
    )
    result["finance_score_changed"] = ~np.isclose(
        result["finance_compound"], result["plain_compound"], atol=1e-12, rtol=0
    )
    result["sentiment_label_changed"] = result["plain_label"].ne(
        result["finance_label"]
    )
    return result.sort_values(
        ["headline_date", "ticker", "title"], kind="stable"
    ).reset_index(drop=True)


def aggregate_ticker_day_scores(
    headline_scores: pd.DataFrame,
    ticker_day_panel: pd.DataFrame,
) -> pd.DataFrame:
    """Average headline scores by ticker-day on the complete coverage grid."""
    _require_columns(
        headline_scores,
        {
            "aligned_trading_date",
            "ticker",
            "plain_compound",
            "finance_compound",
        },
        "headline_scores",
    )
    _require_columns(
        ticker_day_panel,
        {"date", "ticker", "sector", "headline_count", "has_news"},
        "ticker_day_panel",
    )
    valid = headline_scores.loc[headline_scores["aligned_trading_date"].notna()]
    aggregated = (
        valid.groupby(["aligned_trading_date", "ticker"], sort=True)
        .agg(
            scored_headline_count=("title", "size"),
            plain_sentiment=("plain_compound", "mean"),
            finance_sentiment=("finance_compound", "mean"),
        )
        .reset_index()
        .rename(columns={"aligned_trading_date": "date"})
    )
    panel = ticker_day_panel[
        ["date", "ticker", "sector", "headline_count", "has_news"]
    ].copy()
    panel = panel.merge(
        aggregated, on=["date", "ticker"], how="left", validate="one_to_one"
    )
    panel["scored_headline_count"] = (
        panel["scored_headline_count"].fillna(0).astype("int64")
    )
    if not panel["scored_headline_count"].eq(panel["headline_count"]).all():
        raise SentimentValidationError("headline and scored-headline counts differ")
    for column in ("plain_sentiment", "finance_sentiment"):
        panel[column] = panel[column].fillna(0.0)
    panel["no_news_treatment"] = np.where(
        panel["has_news"], "observed headline mean", "neutral zero"
    )
    return panel.sort_values(["date", "ticker"], kind="stable").reset_index(drop=True)


def sector_sentiment_index(
    ticker_scores: pd.DataFrame,
    sector_coverage: pd.DataFrame,
) -> pd.DataFrame:
    """Equal-weight ticker-day sentiment within sector and add prior-day lags."""
    _require_columns(
        ticker_scores,
        {
            "date",
            "ticker",
            "sector",
            "headline_count",
            "has_news",
            "plain_sentiment",
            "finance_sentiment",
        },
        "ticker_scores",
    )
    _require_columns(
        sector_coverage,
        {
            "date",
            "sector",
            "headline_count",
            "covered_tickers",
            "constituent_count",
            "coverage_breadth",
            "ticker_coverage_hhi",
            "coverage_confidence",
        },
        "sector_coverage",
    )
    grouped = ticker_scores.groupby(["date", "sector"], sort=True)
    index = grouped.agg(
        ticker_count=("ticker", "nunique"),
        covered_tickers=("has_news", "sum"),
        headline_count=("headline_count", "sum"),
        plain_sentiment_index=("plain_sentiment", "mean"),
        finance_sentiment_index=("finance_sentiment", "mean"),
    ).reset_index()

    observed = (
        ticker_scores.loc[ticker_scores["has_news"]]
        .groupby(["date", "sector"], sort=True)
        .agg(
            plain_sentiment_covered_only=("plain_sentiment", "mean"),
            finance_sentiment_covered_only=("finance_sentiment", "mean"),
        )
        .reset_index()
    )
    index = index.merge(observed, on=["date", "sector"], how="left")
    coverage = sector_coverage[
        [
            "date",
            "sector",
            "constituent_count",
            "coverage_breadth",
            "ticker_coverage_hhi",
            "coverage_confidence",
            "has_news",
        ]
    ]
    index = index.merge(
        coverage, on=["date", "sector"], how="left", validate="one_to_one"
    )
    if not index["ticker_count"].eq(index["constituent_count"]).all():
        raise SentimentValidationError("sector ticker denominator changed unexpectedly")
    index = index.sort_values(["sector", "date"], kind="stable").reset_index(drop=True)
    for raw in ("plain_sentiment_index", "finance_sentiment_index"):
        index[f"{raw}_lag1"] = index.groupby("sector", sort=False)[raw].shift(1)
    index["tradable_signal_available"] = index["finance_sentiment_index_lag1"].notna()
    index["no_news_policy"] = "all constituent ticker-days retained; no-news score = 0"
    return index.sort_values(["date", "sector"], kind="stable").reset_index(drop=True)


def market_news_index(sector_index: pd.DataFrame) -> pd.DataFrame:
    """Build a descriptive all-stock news fear-greed index.

    Sector scores are weighted by their constituent counts, which is identical
    to equal-weighting all ticker-day scores. The standardized fields use the
    complete displayed sample and must not be treated as a live trading signal.
    """
    _require_columns(
        sector_index,
        {
            "date",
            "sector",
            "ticker_count",
            "covered_tickers",
            "headline_count",
            "plain_sentiment_index",
            "finance_sentiment_index",
        },
        "sector_index",
    )
    if sector_index.duplicated(["date", "sector"]).any():
        raise SentimentValidationError("sector index contains duplicate date-sector rows")
    working = sector_index.copy(deep=True)
    for model in ("plain", "finance"):
        working[f"{model}_weighted_sentiment"] = (
            working[f"{model}_sentiment_index"] * working["ticker_count"]
        )
    market = (
        working.groupby("date", sort=True)
        .agg(
            ticker_count=("ticker_count", "sum"),
            covered_tickers=("covered_tickers", "sum"),
            headline_count=("headline_count", "sum"),
            plain_weighted_sentiment=("plain_weighted_sentiment", "sum"),
            finance_weighted_sentiment=("finance_weighted_sentiment", "sum"),
        )
        .reset_index()
    )
    if market["ticker_count"].nunique() != 1 or market["ticker_count"].iloc[0] != 50:
        raise SentimentValidationError("market news index requires the fixed 50-stock universe")
    market["coverage_breadth"] = market["covered_tickers"] / market["ticker_count"]
    for model in ("plain", "finance"):
        score = market[f"{model}_weighted_sentiment"] / market["ticker_count"]
        standard_deviation = float(score.std(ddof=1))
        if not np.isfinite(standard_deviation) or standard_deviation <= 0:
            raise SentimentValidationError(
                f"{model} market sentiment cannot be standardized"
            )
        market[f"{model}_sentiment_index"] = score
        market[f"{model}_fear_greed_index"] = 50.0 * (score + 1.0)
        market[f"{model}_standardized_score"] = (
            score - float(score.mean())
        ) / standard_deviation
    market = market.drop(
        columns=["plain_weighted_sentiment", "finance_weighted_sentiment"]
    )
    if not market[
        ["plain_fear_greed_index", "finance_fear_greed_index"]
    ].apply(lambda values: values.between(0, 100)).all().all():
        raise SentimentValidationError("market fear-greed index escaped the 0-100 scale")
    market["standardization_basis"] = (
        f"full displayed sample {market['date'].min():%Y-%m-%d} to "
        f"{market['date'].max():%Y-%m-%d}; descriptive only"
    )
    market["no_news_policy"] = (
        "all 50 ticker-days retained; no-news score = 0"
    )
    return market.sort_values("date", kind="stable").reset_index(drop=True)


def _lexicon_family(term: str) -> str:
    for family, variants in ALL_FAMILY_VARIANTS.items():
        if term in variants:
            return family
    raise SentimentValidationError(f"finance lexicon term has no family: {term}")


def build_lexicon_audit(headline_scores: pd.DataFrame) -> pd.DataFrame:
    """Document plain scores, ten-reviewer mean scores, use, and rationale."""
    plain, _finance = _analyzers()
    token_counts: dict[str, int] = {term: 0 for term in FINANCE_LEXICON}
    pattern = re.compile(r"[A-Za-z][A-Za-z'-]*")
    for title in headline_scores["title"].astype(str):
        for token in pattern.findall(title.lower()):
            if token in token_counts:
                token_counts[token] += 1
    records = []
    for term, score in FINANCE_LEXICON.items():
        family = _lexicon_family(term)
        records.append(
            {
                "term": term,
                "canonical_family": family,
                "plain_vader_score": plain.lexicon.get(term, pd.NA),
                "finance_vader_score": score,
                "action": "override" if term in plain.lexicon else "add",
                "headline_token_occurrences": token_counts[term],
                "rationale": ALL_FAMILY_RATIONALE[family],
                "score_source": (
                    "unweighted arithmetic mean of 10 blind sub-agent reviews; "
                    "approved by student review"
                ),
                "reviewer_count": len(REVIEW_SCORES),
                "score_scale": "VADER lexical valence, approximately -4 to +4",
                "review_status": "student reviewed and approved",
            }
        )
    return pd.DataFrame.from_records(records).sort_values("term").reset_index(drop=True)


def build_lexicon_panel_evidence() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return every blinded score and the exact family-level arithmetic means."""
    panels = (
        ("initial_compact_lexicon", REVIEW_SCORES),
        ("researched_expansion", EXPANSION_REVIEW_SCORES),
    )
    raw_records = [
        {
            "review_round": review_round,
            "reviewer_id": reviewer,
            "reviewer_role": REVIEWER_ROLES[reviewer],
            "canonical_family": family,
            "score": score,
            "review_was_blind": True,
            "weight_in_mean": 0.1,
        }
        for review_round, panel_scores in panels
        for reviewer, scores in panel_scores.items()
        for family, score in scores.items()
    ]
    raw = pd.DataFrame.from_records(raw_records).sort_values(
        ["review_round", "reviewer_id", "canonical_family"], kind="stable"
    )
    summary_records = []
    for review_round, panel_scores in panels:
        for family in next(iter(panel_scores.values())):
            values = [scores[family] for scores in panel_scores.values()]
            summary_records.append(
                {
                    "review_round": review_round,
                    "canonical_family": family,
                    "reviewer_count": len(values),
                    "arithmetic_mean_score": ALL_AVERAGED_FAMILY_SCORES[family],
                    "sample_standard_deviation": stdev(values),
                    "minimum_score": min(values),
                    "maximum_score": max(values),
                    "zero_exclusion_votes": sum(value == 0.0 for value in values),
                    "aggregation_rule": "unweighted arithmetic mean including zeros",
                    "variants": ", ".join(ALL_FAMILY_VARIANTS[family]),
                    "rationale": ALL_FAMILY_RATIONALE[family],
                }
            )
    summary = pd.DataFrame.from_records(summary_records)
    return raw.reset_index(drop=True), summary.reset_index(drop=True)


def _model_summary(headlines: pd.DataFrame, sector: pd.DataFrame) -> pd.DataFrame:
    aligned = headlines["aligned_trading_date"].notna()
    records = [
        ("clean_headlines_scored", len(headlines), "rows"),
        ("aligned_headlines_indexed", int(aligned.sum()), "rows"),
        ("unaligned_post_sample_headlines", int((~aligned).sum()), "rows"),
        ("plain_neutral_headlines", int(headlines["plain_label"].eq("neutral").sum()), "rows"),
        ("plain_neutral_share", float(headlines["plain_label"].eq("neutral").mean()), "proportion"),
        ("finance_neutral_headlines", int(headlines["finance_label"].eq("neutral").sum()), "rows"),
        (
            "finance_neutral_share",
            float(headlines["finance_label"].eq("neutral").mean()),
            "proportion",
        ),
        ("finance_score_changed", int(headlines["finance_score_changed"].sum()), "rows"),
        ("sentiment_label_changed", int(headlines["sentiment_label_changed"].sum()), "rows"),
        ("sector_index_rows", len(sector), "rows"),
        ("sector_count", int(sector["sector"].nunique()), "sectors"),
        ("equity_date_count", int(sector["date"].nunique()), "dates"),
        ("sector_days_without_news", int((~sector["has_news"]).sum()), "rows"),
    ]
    return pd.DataFrame(records, columns=["metric", "value", "unit"])


def _sector_summary(sector: pd.DataFrame) -> pd.DataFrame:
    return (
        sector.groupby("sector", sort=True)
        .agg(
            date_start=("date", "min"),
            date_end=("date", "max"),
            trading_days=("date", "size"),
            days_with_news=("has_news", "sum"),
            headline_count=("headline_count", "sum"),
            mean_plain_sentiment=("plain_sentiment_index", "mean"),
            mean_finance_sentiment=("finance_sentiment_index", "mean"),
            volatility_finance_sentiment=("finance_sentiment_index", "std"),
            mean_coverage_breadth=("coverage_breadth", "mean"),
        )
        .reset_index()
    )


def _validation_cases(headlines: pd.DataFrame, rows: int = 20) -> pd.DataFrame:
    """Select real high-impact lexicon cases for explicit student review."""
    candidates = headlines.loc[headlines["finance_score_changed"]].copy()
    candidates["absolute_score_change"] = candidates["finance_score_change"].abs()
    candidates = candidates.sort_values(
        ["absolute_score_change", "headline_date", "ticker", "title"],
        ascending=[False, True, True, True],
        kind="stable",
    )
    # Prefer one positive and one negative finance-adjusted case per sector so
    # the review sheet cannot become a flattering list of earnings beats only.
    selected = (
        candidates.loc[candidates["finance_label"].isin(["positive", "negative"])]
        .groupby(["sector", "finance_label"], sort=True, group_keys=False)
        .head(1)
        .sort_values(["sector", "finance_label"], kind="stable")
        .head(rows)
        .copy()
    )
    selected["ai_expected_direction"] = selected["finance_label"]
    selected["student_expected_direction"] = pd.NA
    selected["student_review_status"] = "review required"
    columns = [
        "headline_date",
        "aligned_trading_date",
        "ticker",
        "sector",
        "title",
        "plain_compound",
        "finance_compound",
        "finance_score_change",
        "plain_label",
        "finance_label",
        "ai_expected_direction",
        "student_expected_direction",
        "student_review_status",
    ]
    return selected[columns].reset_index(drop=True)


def _expansion_validation_cases(headlines: pd.DataFrame) -> pd.DataFrame:
    """Select two real score-change cases for each expansion family."""
    records: list[pd.DataFrame] = []
    for family, variants in EXPANSION_FAMILY_VARIANTS.items():
        pattern = rf"(?i)(?<![A-Za-z])(?:{'|'.join(map(re.escape, variants))})(?![A-Za-z])"
        candidates = headlines.loc[
            headlines["title"].astype(str).str.contains(pattern, regex=True)
        ].copy()
        candidates["absolute_score_change"] = candidates["finance_score_change"].abs()
        candidates = candidates.sort_values(
            ["absolute_score_change", "headline_date", "ticker", "title"],
            ascending=[False, True, True, True],
            kind="stable",
        )
        selected = candidates.drop_duplicates("ticker").head(2).copy()
        selected.insert(0, "canonical_family", family)
        records.append(selected)
    result = pd.concat(records, ignore_index=True)
    result["ai_expected_direction"] = result["finance_label"]
    result["student_expected_direction"] = pd.NA
    result["student_review_status"] = "review required"
    columns = [
        "canonical_family",
        "headline_date",
        "aligned_trading_date",
        "ticker",
        "sector",
        "title",
        "plain_compound",
        "finance_compound",
        "finance_score_change",
        "plain_label",
        "finance_label",
        "ai_expected_direction",
        "student_expected_direction",
        "student_review_status",
    ]
    return result[columns]


def build_validation_summary(
    headlines: pd.DataFrame,
    ticker: pd.DataFrame,
    sector: pd.DataFrame,
) -> pd.DataFrame:
    """Reconcile required sentiment identities in machine-readable form."""
    lag_expected = (
        sector.sort_values(["sector", "date"], kind="stable")
        .groupby("sector", sort=False)["finance_sentiment_index"]
        .shift(1)
    )
    lag_actual = sector.sort_values(["sector", "date"], kind="stable")[
        "finance_sentiment_index_lag1"
    ]
    equal_weight = ticker.groupby(["date", "sector"], sort=True)[
        "finance_sentiment"
    ].mean()
    observed = sector.set_index(["date", "sector"])["finance_sentiment_index"]
    checks = {
        "headline_key_unique": not headlines.duplicated(
            ["ticker", "headline_date", "title"]
        ).any(),
        "all_aligned_headlines_indexed": int(ticker["headline_count"].sum())
        == int(headlines["aligned_trading_date"].notna().sum()),
        "ticker_day_key_unique": not ticker.duplicated(["date", "ticker"]).any(),
        "sector_day_key_unique": not sector.duplicated(["date", "sector"]).any(),
        "no_news_ticker_scores_are_zero": bool(
            ticker.loc[~ticker["has_news"], ["plain_sentiment", "finance_sentiment"]]
            .eq(0.0)
            .all()
            .all()
        ),
        "sector_index_is_equal_weight_ticker_mean": bool(
            np.allclose(equal_weight.sort_index(), observed.sort_index(), atol=1e-12)
        ),
        "lag_is_previous_observed_sector_day": bool(
            np.allclose(lag_expected, lag_actual, atol=1e-12, equal_nan=True)
        ),
        "scores_are_bounded": bool(
            headlines[["plain_compound", "finance_compound"]]
            .ge(-1.0)
            .all()
            .all()
            and headlines[["plain_compound", "finance_compound"]]
            .le(1.0)
            .all()
            .all()
        ),
    }
    return pd.DataFrame(
        [
            {
                "check": check,
                "status": "pass" if passed else "fail",
                "detail": "required identity satisfied" if passed else "identity failed",
            }
            for check, passed in checks.items()
        ]
    )


def prepare_sentiment(news: NewsCoverageFeatures) -> SentimentResult:
    """Build headline, ticker-day, and leakage-safe sector sentiment evidence."""
    headlines = score_headlines(news.aligned_headlines)
    ticker = aggregate_ticker_day_scores(headlines, news.ticker_day_panel)
    sector = sector_sentiment_index(ticker, news.sector_day_panel)
    market = market_news_index(sector)
    validation = build_validation_summary(headlines, ticker, sector)
    failures = validation.loc[validation["status"].eq("fail")]
    if not failures.empty:
        raise SentimentValidationError(
            f"sentiment validation failed: {failures['check'].tolist()}"
        )
    panel_scores, panel_summary = build_lexicon_panel_evidence()
    return SentimentResult(
        headline_scores=headlines,
        ticker_day_scores=ticker,
        sector_index=sector,
        market_index=market,
        lexicon_audit=build_lexicon_audit(headlines),
        lexicon_panel_scores=panel_scores,
        lexicon_panel_summary=panel_summary,
        model_summary=_model_summary(headlines, sector),
        sector_summary=_sector_summary(sector),
        validation_cases=_validation_cases(headlines),
        expansion_validation_cases=_expansion_validation_cases(headlines),
        validation_summary=validation,
    )


def save_sentiment_outputs(
    result: SentimentResult,
    *,
    data_dir: Path,
    tables_dir: Path,
) -> list[Path]:
    """Save the app-facing sector index and compact Phase 4 audit evidence."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        data_dir / "sector_sentiment_index.csv": result.sector_index,
        data_dir / "market_news_index.csv": result.market_index,
        data_dir / "ticker_sentiment_sample.csv": result.ticker_day_scores.tail(100),
        tables_dir / "finance_lexicon_audit.csv": result.lexicon_audit,
        tables_dir / "finance_lexicon_panel_scores.csv": result.lexicon_panel_scores,
        tables_dir / "finance_lexicon_panel_summary.csv": result.lexicon_panel_summary,
        tables_dir / "sentiment_model_summary.csv": result.model_summary,
        tables_dir / "sector_sentiment_summary.csv": result.sector_summary,
        tables_dir / "sentiment_validation_cases.csv": result.validation_cases,
        tables_dir / "finance_lexicon_expansion_validation_cases.csv": (
            result.expansion_validation_cases
        ),
        tables_dir / "sentiment_validation_summary.csv": result.validation_summary,
    }
    paths: list[Path] = []
    for path, frame in outputs.items():
        frame.to_csv(path, index=False)
        paths.append(path.resolve())
    return paths


__all__ = [
    "FINANCE_LEXICON",
    "NEUTRAL_THRESHOLD",
    "ROLLING_DISPLAY_WINDOW",
    "SentimentResult",
    "SentimentValidationError",
    "aggregate_ticker_day_scores",
    "build_lexicon_audit",
    "build_lexicon_panel_evidence",
    "build_validation_summary",
    "market_news_index",
    "prepare_sentiment",
    "save_sentiment_outputs",
    "score_headlines",
    "sector_sentiment_index",
]
