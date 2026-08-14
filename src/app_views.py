# ruff: noqa: E501, RUF001
"""Six-page Streamlit interface for the Stockist Funds investor journey."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.allocation_component import allocation_slider
from src.allocation_history import allocation_history
from src.app_charts import (
    allocation_drawdown_figure,
    allocation_growth_figure,
    allocation_history_figure,
    benchmark_growth_figure,
    coverage_figure,
    drawdown_figure,
    exposure_figure,
    fear_greed_figure,
    fusion_growth_figure,
    growth_figure,
    holdings_figure,
    risk_return_figure,
    sector_allocation_figure,
    sentiment_figure,
)
from src.app_data import AppArtifactError, AppArtifacts, load_app_artifacts
from src.app_logic import (
    ALLOCATION_BENCHMARK_LABELS,
    BENCHMARK_LABELS,
    FAMILY_LABELS,
    FAMILY_PURPOSE,
    FAMILY_RISKS,
    METHOD_LABELS,
    METHOD_OBJECTIVES,
    METHOD_SUMMARIES,
    allocation_analysis,
    allocation_benchmark_evidence,
    benchmark_evidence,
    comparison_table,
    fund_catalog,
    latest_fund_weights,
    latest_weight_changes,
    sector_allocation,
)
from src.app_settings import DEFAULT_APP_SETTINGS

VIEWS = (
    "Overview",
    "Compare funds",
    "Fund details",
    "Allocation lab",
    "News signal",
)
BUILD_DATE = "13 August 2026"
APP_VERSION = "0.9"


@st.cache_data(ttl=86_400, show_spinner=False)
def _cached_artifacts(project_root: str) -> AppArtifacts:
    return load_app_artifacts(Path(project_root))


def _css() -> None:
    st.markdown(
        """
        <style>
        :root { --ink:#0F172A; --secondary:#475569; --canvas:#F4F6F5;
                --surface:#FFFFFF; --soft:#EEF2F3;
                --rule:#D7DEE3; --accent:#0F766E; --accent-soft:#DDF3EF;
                --warning:#B45309; --adverse:#C2410C; }
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background:var(--canvas); color:var(--ink);
            font-family:Aptos,Inter,-apple-system,BlinkMacSystemFont,
                "Segoe UI",sans-serif;
        }
        [data-testid="stHeader"] { background:rgba(244,246,245,0.94); }
        [data-testid="stToolbar"] { color:var(--secondary); }
        section[data-testid="stSidebar"] {
            background:#E9EFF0; border-right:1px solid #CCD6D9;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
            height:3.25rem; min-height:3.25rem; padding-top:0.45rem;
            margin-bottom:0;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            color:var(--ink); height:calc(100% - 3.25rem); box-sizing:border-box;
            padding-top:0; padding-bottom:1rem;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]
        > div[data-testid="stVerticalBlock"] {
            min-height:100%; display:flex; flex-direction:column;
        }
        .st-key-sidebar_brand { margin-bottom:0.65rem; }
        .st-key-sidebar_brand [data-testid="stImage"] {
            display:flex; justify-content:center; margin:0 0 0.35rem 0;
        }
        .st-key-sidebar_brand [data-testid="stImage"] img {
            width:88px; max-width:88px;
        }
        .st-key-sidebar_brand h2 {
            margin-top:0; margin-bottom:0.2rem; padding-top:0;
        }
        .st-key-sidebar_nav .stButton { margin-bottom:0.12rem; }
        .st-key-sidebar_nav .stButton > button {
            width:100%; min-height:2.8rem; justify-content:flex-start;
            border:0; border-left:3px solid transparent; border-radius:6px;
            padding:0.55rem 0.72rem; font-size:1rem; font-weight:500;
            color:var(--ink); background:transparent; box-shadow:none;
        }
        .st-key-sidebar_nav [data-testid^="stBaseButton-"] {
            justify-content:flex-start !important; text-align:left !important;
            font-size:1rem !important;
        }
        .st-key-sidebar_nav [data-testid^="stBaseButton-"] > div,
        .st-key-sidebar_nav [data-testid^="stBaseButton-"] > div > span {
            justify-content:flex-start !important; text-align:left !important;
        }
        .st-key-sidebar_nav .stButton > button:hover {
            color:var(--ink); background:rgba(255,255,255,0.72);
            border-left-color:#77AAA4;
        }
        .st-key-sidebar_nav .stButton > button[kind="primary"] {
            color:#0B514C; background:#DCE9E7; border-left-color:var(--accent);
            font-weight:700;
        }
        .st-key-sidebar_nav .stButton > button p { color:inherit; }
        .st-key-overview_compare_funds [data-testid="stBaseButton-primary"],
        .st-key-overview_compare_funds [data-testid="stBaseButton-primary"] * {
            color:#FFFFFF !important;
        }
        .sidebar-section-label {
            color:#64748B; font-size:0.72rem; font-weight:700;
            letter-spacing:0.08em; margin:0.25rem 0 0.38rem 0.15rem;
        }
        .st-key-sidebar_footer {
            margin-top:auto; padding-top:1rem;
        }
        .sidebar-footer {
            border-top:1px solid #CCD6D9; padding-top:0.95rem;
            color:#64748B; font-size:0.8rem; line-height:1.5;
        }
        .sidebar-footer p { color:#64748B; margin:0 0 0.7rem 0; }
        .sidebar-footer p:last-child { margin-bottom:0; }
        .block-container {
            max-width:1240px; padding-top:2.1rem; padding-bottom:2.4rem;
        }
        h1, h2, h3, [data-testid="stHeadingWithActionElements"] {
            color:var(--ink); letter-spacing:-0.015em;
        }
        p, label, [data-testid="stCaptionContainer"] { color:var(--secondary); }
        .stockist-card { background:var(--surface); border:1px solid var(--rule);
            border-radius:9px; padding:1.05rem 1.1rem; min-height:168px; }
        .stockist-card h3 { font-size:1.05rem; margin:0 0 0.55rem 0; }
        .step-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
            gap:1rem; align-items:stretch; margin-bottom:1rem; }
        .step-card { background:var(--surface); border:1px solid var(--rule);
            border-radius:9px; padding:1.05rem 1.1rem; min-height:140px;
            box-sizing:border-box; }
        .step-card strong { display:block; margin-bottom:0.65rem; }
        .step-card p { margin:0; }
        .family-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
            gap:1rem; align-items:stretch; margin-bottom:1rem; }
        .family-card { display:flex; flex-direction:column; box-sizing:border-box; }
        .family-card .card-chips { margin-top:auto; padding-top:0.25rem; }
        .method-grid { display:grid; grid-template-columns:repeat(6,minmax(0,1fr));
            gap:1rem; align-items:stretch; margin-bottom:1rem; }
        .method-card { grid-column:span 2; min-height:190px; box-sizing:border-box; }
        .method-card:nth-child(4) { grid-column:2 / span 2; }
        .method-card:nth-child(5) { grid-column:4 / span 2; }
        .allocation-overview-grid { display:grid;
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:1rem; align-items:stretch; margin:0.75rem 0 0.8rem 0; }
        .allocation-overview-card { min-height:132px; box-sizing:border-box; }
        .allocation-overview-card p { margin-bottom:0; }
        .inspect-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
            gap:1rem; align-items:stretch; margin-bottom:1rem; }
        .inspect-card { min-height:126px; box-sizing:border-box; }
        .inspect-card p { margin-bottom:0; }
        @media (max-width:900px) {
            .step-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
            .family-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
            .family-card:nth-child(3) { grid-column:1 / span 2;
                width:calc(50% - 0.5rem); justify-self:center; }
            .method-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
            .method-card, .method-card:nth-child(4) { grid-column:auto; min-height:170px; }
            .method-card:nth-child(5) { grid-column:1 / span 2;
                width:calc(50% - 0.5rem); justify-self:center; min-height:170px; }
            .inspect-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
        }
        @media (max-width:640px) {
            .step-grid { grid-template-columns:1fr; }
            .family-grid { grid-template-columns:1fr; }
            .family-card:nth-child(3) { grid-column:auto; width:auto; }
            .method-grid { grid-template-columns:1fr; }
            .method-card, .method-card:nth-child(4), .method-card:nth-child(5) {
                grid-column:auto; width:auto; min-height:0; }
            .allocation-overview-grid { grid-template-columns:1fr; }
            .allocation-overview-card { min-height:0; }
            .inspect-grid { grid-template-columns:1fr; }
            .inspect-card { min-height:0; }
        }
        .chip { display:inline-block; border:1px solid var(--rule); border-radius:999px;
            padding:0.18rem 0.52rem; margin:0 0.35rem 0.35rem 0;
            background:var(--soft); color:var(--ink); font-size:0.8rem; font-weight:600; }
        .chip-accent { border-color:var(--accent); background:var(--accent-soft); }
        .fine-print { color:var(--secondary); font-size:0.86rem; line-height:1.45; }
        .footer { border-top:1px solid var(--rule); margin-top:2.5rem;
            padding-top:1rem; color:var(--secondary); font-size:0.82rem; }
        div[data-testid="stMetric"] {
            background:var(--surface); border:1px solid var(--rule);
            border-radius:9px; padding:0.82rem 0.92rem;
        }
        div[data-testid="stMetricLabel"] p { color:var(--secondary); }
        div[data-testid="stMetricValue"] { color:var(--ink); }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background:var(--surface); border-color:var(--rule); border-radius:9px;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            background:var(--surface); border-radius:8px;
        }
        [data-baseweb="input"], [data-baseweb="select"] > div,
        [data-baseweb="textarea"] {
            background:var(--surface); color:var(--ink);
        }
        [data-baseweb="tag"] {
            background:var(--accent-soft); color:#0B514C;
            border:1px solid #9ACAC1;
        }
        [data-testid="stAlert"] { border-radius:8px; }
        [data-testid="stExpander"] {
            background:var(--surface); border:1px solid var(--rule);
            border-radius:8px;
        }
        .stButton > button, .stDownloadButton > button {
            border-color:#AEBBC1; font-weight:600;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            border-color:var(--accent); color:var(--accent);
        }
        a { color:var(--accent); }
        @media (max-width: 768px) {
            .block-container { padding-top:1.35rem; padding-left:1rem; padding-right:1rem; }
            .stockist-card { min-height:auto; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _page_header(title: str, purpose: str) -> None:
    st.title(title)
    st.markdown(f"<p style='font-size:1.08rem;color:#475569'>{purpose}</p>", unsafe_allow_html=True)


def _metric_row(metrics: list[tuple[str, str, str]]) -> None:
    columns_per_row = 2
    for start in range(0, len(metrics), columns_per_row):
        row = metrics[start : start + columns_per_row]
        columns = st.columns(len(row))
        for column, (label, value, help_text) in zip(columns, row, strict=True):
            column.metric(label, value, help=help_text)


def _display_table(frame: pd.DataFrame, *, height: int | None = None) -> None:
    kwargs: dict[str, object] = {"width": "stretch", "hide_index": True}
    if height is not None:
        kwargs["height"] = height
    st.dataframe(frame, **kwargs)


def _download(
    frame: pd.DataFrame,
    label: str,
    file_name: str,
    key: str,
    *,
    stretch: bool = False,
) -> None:
    st.download_button(
        label,
        data=frame.to_csv(index=False).encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
        key=key,
        icon=":material/download:",
        width="stretch" if stretch else "content",
    )


def _section_header_with_download(
    title: str,
    frame: pd.DataFrame,
    label: str,
    file_name: str,
    key: str,
) -> None:
    heading, download = st.columns(
        [0.76, 0.24],
        vertical_alignment="center",
    )
    heading.subheader(title)
    with download:
        _download(
            frame,
            label,
            file_name,
            key,
            stretch=True,
        )


def _sync_query(key: str, value: str) -> None:
    if st.query_params.get(key) != value:
        st.query_params[key] = value


def _navigate(view: str) -> None:
    """Queue navigation so the radio-backed state changes before widget creation."""
    if view not in VIEWS:
        raise ValueError(f"Unknown Stockist view: {view}")
    st.session_state["stockist_pending_view"] = view
    st.rerun()


def _benchmark_selector(*, key: str) -> str:
    options = list(BENCHMARK_LABELS)
    query_benchmark = st.query_params.get("benchmark")
    preserved = st.session_state.get("selected_benchmark_id")
    default = query_benchmark if query_benchmark in options else preserved
    if default not in options:
        default = "same_family_equal_weight"
    selected = st.selectbox(
        "Benchmark",
        options,
        index=options.index(default),
        format_func=BENCHMARK_LABELS.get,
        key=key,
        help="Equal Weight tests the portfolio rule; SPY and ONEQ provide external market context.",
    )
    st.session_state["selected_benchmark_id"] = selected
    _sync_query("benchmark", selected)
    return selected


def _allocation_benchmark_selector(*, key: str) -> str:
    options = list(ALLOCATION_BENCHMARK_LABELS)
    query_benchmark = st.query_params.get("allocation_benchmark")
    preserved = st.session_state.get("selected_allocation_benchmark_id")
    default = query_benchmark if query_benchmark in options else preserved
    if default not in options:
        default = "equal_selected_funds"
    selected = st.selectbox(
        "Allocation benchmark",
        options,
        index=options.index(default),
        format_func=ALLOCATION_BENCHMARK_LABELS.get,
        key=key,
        help=(
            "Equal allocation tests your weighting choice. SPY and ONEQ add "
            "market context but may not match the allocation's asset mix or risk."
        ),
    )
    st.session_state["selected_allocation_benchmark_id"] = selected
    _sync_query("allocation_benchmark", selected)
    return selected


def _fund_selector(catalog: pd.DataFrame, *, key: str) -> str:
    fund_ids = catalog["fund_id"].tolist()
    labels = catalog.set_index("fund_id")["display_name"].to_dict()
    query_fund = st.query_params.get("fund")
    preserved = st.session_state.get("selected_fund_id")
    default = query_fund if query_fund in fund_ids else preserved
    if default not in fund_ids:
        default = "combined_risk_parity"
    selected = st.selectbox(
        "Fund",
        fund_ids,
        index=fund_ids.index(default),
        format_func=labels.get,
        key=key,
    )
    st.session_state["selected_fund_id"] = selected
    _sync_query("fund", selected)
    return selected


def _overview(artifacts: AppArtifacts, catalog: pd.DataFrame) -> None:
    _page_header(
        "Systematic funds, inspectable evidence",
        "Compare repeatable equity, crypto and combined strategies with risk, costs and evidence limits kept visible.",
    )
    st.subheader("How Stockist Funds works")
    steps = (
        (
            "1 · Observe",
            "Validated prices and headlines form the historical evidence base.",
        ),
        (
            "2 · Estimate",
            "Each rule uses only trailing observations available before the next return.",
        ),
        (
            "3 · Rebalance",
            f"The {len(catalog)} primary funds reset monthly under fixed caps and trading costs.",
        ),
        (
            "4 · Inspect",
            "Returns, drawdowns, holdings, turnover and signal confidence remain auditable.",
        ),
    )
    step_cards = "".join(
        (
            '<div class="step-card">'
            f"<strong>{title}</strong>"
            f'<p class="fine-print">{body}</p>'
            "</div>"
        )
        for title, body in steps
    )
    st.markdown(
        f'<div class="step-grid">{step_cards}</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Choose an asset family before choosing a method")
    family_cards: list[str] = []
    for family in ("equity", "crypto", "combined"):
        subset = catalog.loc[catalog["asset_family"].eq(family)]
        family_cards.append(
            '<div class="stockist-card family-card">'
            f"<h3>{FAMILY_LABELS[family]} funds</h3>"
            f"<p>{FAMILY_PURPOSE[family]}</p>"
            '<p class="fine-print"><strong>Principal risks:</strong> '
            f"{FAMILY_RISKS[family]}</p>"
            '<div class="card-chips">'
            f'<span class="chip">{catalog["method"].nunique()} monthly methods</span>'
            f'<span class="chip">{len(subset)} fact sheets</span>'
            "</div></div>"
        )
    st.markdown(
        f'<div class="family-grid">{"".join(family_cards)}</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Choose a portfolio method")
    st.caption(
        "After choosing an asset family, select how its fund will set target weights. "
        "Every method uses the same eligible assets and rebalances monthly."
    )
    method_order = (
        "equal_weight",
        "minimum_variance",
        "risk_parity",
        "maximum_sharpe",
        "hierarchical_risk_parity",
    )
    method_cards = "".join(
        (
            '<div class="stockist-card method-card">'
            f"<h3>{METHOD_LABELS[method]}</h3>"
            f"<p>{METHOD_SUMMARIES[method]}</p>"
            "</div>"
        )
        for method in method_order
    )
    st.markdown(
        f'<div class="method-grid">{method_cards}</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Build an allocation")
    st.markdown(
        "Combine two to four Stockist funds into a hypothetical portfolio and see "
        "how the allocation would have performed historically."
    )
    allocation_steps = (
        (
            "Set fund weights",
            "Adjust how much of the portfolio is allocated to each selected fund.",
        ),
        (
            "See the combined exposure",
            "Inspect the underlying asset mix, overlap and concentration created by the allocation.",
        ),
        (
            "Measure the historical outcome",
            "Compare return, volatility, Sharpe ratio, drawdown and the estimated product fee.",
        ),
    )
    allocation_cards = "".join(
        (
            '<div class="stockist-card allocation-overview-card">'
            f"<h3>{title}</h3>"
            f"<p>{body}</p>"
            "</div>"
        )
        for title, body in allocation_steps
    )
    st.markdown(
        f'<div class="allocation-overview-grid">{allocation_cards}</div>',
        unsafe_allow_html=True,
    )
    if st.button("Open allocation lab", key="overview_allocation_lab"):
        _navigate("Allocation lab")

    st.subheader("What you can inspect")
    inspectable_evidence = (
        (
            "Performance &amp; risk",
            "Returns, benchmarks, volatility and drawdowns.",
        ),
        (
            "Portfolio construction",
            "Holdings, target weights, sector exposures and concentration.",
        ),
        (
            "Implementation",
            "Turnover, trading-cost assumptions and rebalance changes.",
        ),
        (
            "News signal experiment",
            "Headline sentiment, coverage support and the measured effect of a coverage-aware sentiment tilt.",
        ),
    )
    inspect_cards = "".join(
        (
            '<div class="stockist-card inspect-card">'
            f"<h3>{title}</h3>"
            f"<p>{body}</p>"
            "</div>"
        )
        for title, body in inspectable_evidence
    )
    st.markdown(
        f'<div class="inspect-grid">{inspect_cards}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("The primary menu is deliberately not ranked by return.")
    if st.button(
        "Compare monthly funds",
        key="overview_compare_funds",
        type="primary",
    ):
        _navigate("Compare funds")

    dates = artifacts.fund_returns["date"]
    st.caption(
        f"Fund evidence: {dates.min():%d %B %Y} to {dates.max():%d %B %Y} · "
        f"{catalog['fund_id'].nunique()} primary monthly funds · Phase 6 validation passed"
    )


def _compare_funds(artifacts: AppArtifacts, catalog: pd.DataFrame) -> None:
    _page_header(
        "Compare monthly funds",
        "Select up to five funds and compare return, risk, drawdown, implementation cost and benchmark evidence on aligned definitions.",
    )
    family_options = list(FAMILY_LABELS)
    method_options = list(METHOD_LABELS)
    family_filter_key = "compare_family_filters"
    method_filter_key = "compare_method_filters"
    families = [
        family
        for family in st.session_state.get(family_filter_key, family_options)
        if family in family_options
    ]
    methods = [
        method
        for method in st.session_state.get(method_filter_key, method_options)
        if method in method_options
    ]
    filtered = catalog.loc[
        catalog["asset_family"].isin(families) & catalog["method"].isin(methods)
    ].copy()
    labels = catalog.set_index("fund_id")["display_name"].to_dict()
    defaults = [
        fund_id
        for fund_id in ("equity_minimum_variance", "combined_risk_parity")
        if fund_id in catalog["fund_id"].values
    ]
    if not defaults:
        defaults = catalog["fund_id"].head(2).tolist()
    selected_key = "compare_selected_funds"
    filtered_ids = set(filtered["fund_id"])
    stored_selection = st.session_state.get(selected_key, defaults)
    current_selection = [
        fund_id
        for fund_id in stored_selection
        if fund_id in filtered_ids
    ]
    if selected_key in st.session_state and current_selection != list(stored_selection):
        st.session_state[selected_key] = current_selection
    available_funds = filtered["fund_id"].tolist()
    default_selection = [fund_id for fund_id in defaults if fund_id in filtered_ids]
    if not default_selection:
        default_selection = available_funds[:2]
    selection_columns = st.columns([1.45, 1])
    selected_funds = selection_columns[0].multiselect(
        "Selected funds",
        available_funds,
        default=default_selection if selected_key not in st.session_state else None,
        max_selections=5,
        format_func=labels.get,
        key=selected_key,
        help="These funds control the comparison table and charts below.",
    )
    with selection_columns[1]:
        benchmark_option = _benchmark_selector(key="compare_benchmark")

    with st.container(border=True):
        st.markdown("**Filter available funds**")
        st.caption(
            "Filters narrow the choices in Selected funds. A selected fund is removed "
            "when it no longer matches, and the comparison updates automatically."
        )
        filter_columns = st.columns(2)
        filter_columns[0].pills(
            "Asset family",
            family_options,
            selection_mode="multi",
            default=family_options if family_filter_key not in st.session_state else None,
            format_func=FAMILY_LABELS.get,
            key=family_filter_key,
            width="stretch",
        )
        filter_columns[1].pills(
            "Portfolio method",
            method_options,
            selection_mode="multi",
            default=method_options if method_filter_key not in st.session_state else None,
            format_func=METHOD_LABELS.get,
            key=method_filter_key,
            width="stretch",
        )
        st.caption(f"{len(filtered)} of {len(catalog)} funds available to add.")

    if not selected_funds:
        st.info("Select at least one fund to show the aligned comparison.")
        return
    selected = comparison_table(catalog, selected_funds)
    benchmark_results = {
        fund_id: benchmark_evidence(artifacts, fund_id, benchmark_option)
        for fund_id in selected_funds
    }
    selected["selected_benchmark"] = selected["fund_id"].map(
        lambda fund_id: benchmark_results[fund_id].benchmark_label
    )
    selected["return_vs_selected_benchmark"] = selected["fund_id"].map(
        lambda fund_id: benchmark_results[fund_id].annualized_return_difference
    )
    comparison = selected[
        [
            "display_name",
            "family_label",
            "method_label",
            "selected_benchmark",
            "net_annualized_return",
            "net_annualized_volatility",
            "net_sharpe_ratio",
            "net_maximum_drawdown",
            "average_rebalance_turnover",
            "return_vs_selected_benchmark",
        ]
    ].rename(
        columns={
            "display_name": "Fund",
            "family_label": "Family",
            "method_label": "Method",
            "selected_benchmark": "Selected benchmark",
            "net_annualized_return": "Annualised return after trading costs (%)",
            "net_annualized_volatility": "Annualised volatility (%)",
            "net_sharpe_ratio": "Sharpe ratio",
            "net_maximum_drawdown": "Maximum drawdown (%)",
            "average_rebalance_turnover": "Average turnover per rebalance (%)",
            "return_vs_selected_benchmark": "Return versus selected benchmark (%)",
        }
    )
    percent_columns = [
        "Annualised return after trading costs (%)",
        "Annualised volatility (%)",
        "Maximum drawdown (%)",
        "Average turnover per rebalance (%)",
        "Return versus selected benchmark (%)",
    ]
    comparison[percent_columns] = 100 * comparison[percent_columns]
    name_map = catalog.set_index("fund_id")["display_name"].to_dict()
    method_map = catalog.set_index("fund_id")["method"].to_dict()
    st.plotly_chart(
        growth_figure(
            artifacts.fund_returns,
            selected_funds,
            name_map,
            method_map,
            title="How did the selected funds compound?",
        ),
        width="stretch",
    )
    st.plotly_chart(risk_return_figure(catalog, selected_funds), width="stretch")
    st.caption(
        "Crypto-only funds use a 365-day calendar; equity and combined funds use 252 observed equity dates. "
        "Cross-family annualised metrics therefore follow different valid calendar conventions."
    )
    _section_header_with_download(
        "Aligned evidence",
        comparison,
        "Download selected comparison",
        "stockist_fund_comparison.csv",
        "compare_download",
    )
    st.caption(
        "Fund returns are historical simulations after the internal 10 bp turnover cost. "
        "Benchmark differences use each fund's exact common dates with the selected reference."
    )
    _display_table(comparison.round(3), height=36 * len(comparison) + 38)
    with st.expander("Metric definitions and comparison limits"):
        st.markdown(
            "**Annualised return** is compound annual growth. **Volatility** is the annualised standard deviation "
            "of daily after-trading-cost returns. **Sharpe** uses a 0% annual risk-free rate. **Maximum drawdown** "
            "is the largest decline from a prior simulated wealth peak. Historical differences are not forecasts."
        )


def _fund_details(artifacts: AppArtifacts, catalog: pd.DataFrame) -> None:
    _page_header(
        "Fund fact sheet",
        "Inspect one monthly fund's objective, risk, benchmark, historical path, latest simulated weights and implementation evidence.",
    )
    selection_columns = st.columns([1.35, 1])
    with selection_columns[0]:
        fund_id = _fund_selector(catalog, key="details_fund")
    with selection_columns[1]:
        benchmark_option = _benchmark_selector(key="details_benchmark")
    row = catalog.set_index("fund_id").loc[fund_id]
    benchmark = benchmark_evidence(artifacts, fund_id, benchmark_option)
    st.header(row["display_name"])
    st.markdown(
        f"<span class='chip chip-accent'>Monthly primary</span>"
        f"<span class='chip'>Historical OOS</span>"
        f"<span class='chip'>{row['family_label']}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Objective:** {row['objective']}")
    st.markdown(f"**Intended use:** {row['family_purpose']}")
    st.warning(f"Principal risks: {row['principal_risks']} Past simulated performance is not a forecast.")
    returns_download = artifacts.fund_returns.loc[
        artifacts.fund_returns["fund_id"].eq(fund_id)
    ]
    _section_header_with_download(
        "Historical performance",
        returns_download,
        "Download fund return history",
        f"{fund_id}_returns.csv",
        "fund_returns_download",
    )
    _metric_row(
        [
            (
                "Annualised return after trading costs",
                f"{row['net_annualized_return']:.2%}",
                "Compound annual growth after the internal turnover cost.",
            ),
            (
                "Annualised volatility",
                f"{row['net_annualized_volatility']:.2%}",
                "Annualised dispersion of daily after-trading-cost returns.",
            ),
            ("Sharpe ratio", f"{row['net_sharpe_ratio']:.3f}", "0% annual risk-free rate."),
            (
                "Maximum drawdown",
                f"{row['net_maximum_drawdown']:.2%}",
                "Largest decline from a prior simulated wealth peak.",
            ),
        ]
    )
    st.plotly_chart(
        benchmark_growth_figure(benchmark, row["display_name"]),
        width="stretch",
    )
    st.caption(
        f"Benchmark evidence — {benchmark.benchmark_label}: "
        f"{benchmark.first_date:%d %b %Y} to {benchmark.last_date:%d %b %Y} · "
        f"{benchmark.observation_count:,} common observations · {benchmark.annualization_days}-day convention · "
        f"Source: {benchmark.source}. {benchmark.return_basis}."
    )
    names = catalog.set_index("fund_id")["display_name"].to_dict()
    st.plotly_chart(
        drawdown_figure(
            artifacts.fund_returns,
            [fund_id],
            names,
            title="When and how deeply did the fund lose value?",
        ),
        width="stretch",
    )

    latest_date, latest = latest_fund_weights(artifacts.fund_weights, fund_id)
    sectors = sector_allocation(latest, artifacts.fusion_weights)
    st.subheader(f"Latest simulated target weights · effective {latest_date:%d %B %Y}")
    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.plotly_chart(
            holdings_figure(latest, title="What does the target portfolio hold?"),
            width="stretch",
        )
    with chart_columns[1]:
        st.plotly_chart(
            sector_allocation_figure(
                sectors,
                title="How is the target portfolio allocated by sector?",
            ),
            width="stretch",
        )
    st.caption(
        "Equities use the supplied sector classifications. Crypto is shown as a "
        "separate asset-class slice because no crypto-sector taxonomy was supplied."
    )
    holdings = latest[["asset", "asset_class", "target_weight"]].rename(
        columns={
            "asset": "Asset",
            "asset_class": "Asset class",
            "target_weight": "Target weight (%)",
        }
    )
    holdings["Target weight (%)"] *= 100
    table_heading, table_download = st.columns(
        [0.76, 0.24],
        vertical_alignment="center",
    )
    table_heading.markdown("**Complete target-weight table**")
    with table_download:
        _download(
            latest,
            "Download complete weight vector",
            f"{fund_id}_latest_weights.csv",
            "holdings_download",
            stretch=True,
        )
    _display_table(holdings.round(3), height=430)

    st.subheader("Implementation and concentration")
    _metric_row(
        [
            (
                "Average turnover per rebalance",
                f"{row['average_rebalance_turnover']:.2%}",
                "One-way turnover measured against drifted pre-trade weights.",
            ),
            (
                "Cumulative turnover",
                f"{row['cumulative_turnover']:.2f}×",
                "Sum of one-way monthly turnover over the live sample.",
            ),
            (
                "Effective number of assets",
                f"{row['latest_effective_number_of_assets']:.1f}",
                "Inverse latest target-weight HHI; larger means less concentration.",
            ),
            (
                "Return versus benchmark",
                f"{benchmark.annualized_return_difference:+.2%}",
                f"Annualised return difference from {benchmark.benchmark_label} on exact common dates.",
            ),
        ]
    )
    changes = latest_weight_changes(artifacts.fund_weights, fund_id).head(10).copy()
    changes = changes[["asset", "previous_weight", "latest_weight", "change"]].rename(
        columns={
            "asset": "Asset",
            "previous_weight": "Previous target (%)",
            "latest_weight": "Latest target (%)",
            "change": "Change (percentage points)",
        }
    )
    changes.iloc[:, 1:] *= 100
    st.subheader("Largest target-weight changes at the latest rebalance")
    st.caption("These are mechanical optimisation outputs, not causal explanations for why markets moved.")
    history = allocation_history(
        artifacts.fund_weights,
        fund_id,
        artifacts.fusion_weights,
    )
    history_title = (
        "How did the target sector allocation change through time?"
        if history.basis == "sector"
        else "How did the target cryptoasset allocation change through time?"
    )
    st.plotly_chart(
        allocation_history_figure(history, title=history_title),
        width="stretch",
    )
    st.caption(
        "Each band is a share of the target fund and the bands sum to 100% at "
        "every monthly rebalance. A widening band means the method allocated more "
        "to that sector or cryptoasset."
    )
    _display_table(changes.round(3), height=36 * len(changes) + 38)
    with st.expander("Method, assumptions and evidence limit"):
        st.markdown(
            f"**Rule:** {METHOD_OBJECTIVES[row['method']]}  \n"
            f"**Estimation window:** {int(row['estimation_window'])} observations  \n"
            f"**Selected benchmark:** {benchmark.benchmark_label}  \n"
            f"**Benchmark basis:** {benchmark.return_basis}  \n"
            f"**First live simulated date:** {row['first_live_date']:%d %B %Y}  \n"
            f"**Trading cost:** {row['transaction_cost_bps']:.0f} basis points per unit of turnover  \n"
            f"**Evidence limit:** {row['evidence_limit']}"
        )
def _equal_integer_weights(count: int) -> list[int]:
    base, remainder = divmod(100, count)
    return [base + (1 if index < remainder else 0) for index in range(count)]


def _allocation_lab(artifacts: AppArtifacts, catalog: pd.DataFrame) -> None:
    _page_header(
        "Allocation lab",
        "Combine two to four monthly funds and inspect the historical consequences, underlying exposure, overlap and fixed product fee estimate.",
    )
    labels = catalog.set_index("fund_id")["display_name"].to_dict()
    defaults = ["equity_equal_weight", "crypto_equal_weight", "combined_equal_weight"]
    selection_columns = st.columns([1.35, 1])
    with selection_columns[0]:
        selected = st.multiselect(
            "Funds in the hypothetical allocation",
            catalog["fund_id"].tolist(),
            default=defaults,
            max_selections=4,
            format_func=labels.get,
        )
    with selection_columns[1]:
        benchmark_option = _allocation_benchmark_selector(
            key="allocation_benchmark_selector"
        )
    if len(selected) < 2:
        st.warning("Select at least two funds to build a hypothetical allocation.")
        return
    default_weights = _equal_integer_weights(len(selected))
    allocation_key = "allocation_mix_" + "_to_".join(selected)
    if st.button("Reset to equal-allocation example"):
        st.session_state[allocation_key] = {"weights": default_weights}
        st.rerun()

    st.subheader("Hypothetical fund weights")
    selected_weights = allocation_slider(
        [labels[fund_id] for fund_id in selected],
        default_weights,
        key=allocation_key,
    )
    percentages = dict(zip(selected, map(float, selected_weights), strict=True))
    st.caption(
        "Every divider transfers whole percentage points between two neighbouring funds, "
        "so the allocation always remains at 100%."
    )

    left, right = st.columns([0.42, 0.58])
    with left:
        total = sum(percentages.values())
        amount = st.number_input(
            "Illustrative balance (AUD)",
            min_value=1_000,
            max_value=10_000_000,
            value=10_000,
            step=1_000,
        )
        st.caption(
            "Underlying fund returns already include the 10 bp internal turnover-cost assumption. "
            "The 0.12% annual product fee is set by Stockist and is not deducted from the historical metrics."
        )
    if not np.isclose(total, 100):  # defensive guard against malformed component state
        with right:
            st.warning(f"Allocation totals {total:.0f}%. Adjust the fund weights to exactly 100% to view results.")
        return

    allocations = {fund_id: value / 100 for fund_id, value in percentages.items()}
    analysis = allocation_analysis(artifacts, allocations)
    equal_allocations = {fund_id: 1 / len(selected) for fund_id in selected}
    equal_analysis = allocation_analysis(artifacts, equal_allocations)
    benchmark = allocation_benchmark_evidence(
        artifacts,
        analysis.path,
        equal_analysis.path,
        benchmark_option,
        analysis.annualization_days,
    )
    with right:
        st.subheader("Combined historical evidence")
        _metric_row(
            [
                ("Annualised return after trading costs", f"{analysis.metrics['annualized_return']:.2%}", "Monthly fund-level mix."),
                ("Annualised volatility", f"{analysis.metrics['annualized_volatility']:.2%}", "Common selected-fund dates."),
                ("Sharpe ratio", f"{analysis.metrics['sharpe_ratio']:.3f}", "0% annual risk-free rate."),
                ("Maximum drawdown", f"{analysis.metrics['maximum_drawdown']:.2%}", "Largest peak-to-trough loss."),
            ]
        )
        product_fee_rate = DEFAULT_APP_SETTINGS.annual_product_fee_rate
        annual_fee = amount * product_fee_rate
        st.metric(
            "Estimated annual product fee",
            f"A${annual_fee:,.0f}",
            delta=f"{product_fee_rate:.2%} of A${amount:,.0f}; fixed by the fund",
            delta_color="off",
            help="This code-configured annual fee is disclosed for illustration and is not deducted from the historical metrics.",
        )

    st.plotly_chart(allocation_growth_figure(benchmark), width="stretch")
    if benchmark_option == "equal_selected_funds" and max(
        abs(value - 1 / len(selected)) for value in allocations.values()
    ) < 0.015:
        st.info(
            "The chosen weights are currently very close to equal allocation, "
            "so the two growth paths substantially overlap."
        )
    st.subheader("Selected benchmark evidence")
    _metric_row(
        [
            (
                "Allocation return on aligned dates",
                f"{benchmark.allocation_metrics['annualized_return']:.2%}",
                "Annualised compound return on dates shared with the selected benchmark.",
            ),
            (
                "Benchmark return on aligned dates",
                f"{benchmark.benchmark_metrics['annualized_return']:.2%}",
                f"Annualised compound return for {benchmark.benchmark_label}.",
            ),
            (
                "Return versus benchmark",
                f"{benchmark.annualized_return_difference:+.2%}",
                "Allocation annualised return minus benchmark annualised return.",
            ),
            (
                "Tracking error",
                f"{benchmark.tracking_error:.2%}",
                "Annualised variability of daily allocation-minus-benchmark returns.",
            ),
        ]
    )
    st.caption(
        f"{benchmark.benchmark_label}: {benchmark.first_date:%d %b %Y} to "
        f"{benchmark.last_date:%d %b %Y} · {benchmark.observation_count:,} common "
        f"observations · {benchmark.annualization_days}-day convention · "
        f"Source: {benchmark.source}. {benchmark.return_basis}."
    )
    if benchmark_option != "equal_selected_funds":
        st.caption(
            "The external benchmark provides market context and may not match "
            "the allocation's asset mix or risk."
        )
    st.plotly_chart(allocation_drawdown_figure(analysis.path), width="stretch")
    st.caption(
        f"The mix is reset to the selected fund weights monthly across {len(analysis.path):,} common observations "
        f"using a {analysis.annualization_days}-day convention. It is hypothetical, historical and not personalised advice."
    )

    st.subheader("Look-through exposure")
    top = analysis.underlying_exposure.head(12).copy()
    remainder = analysis.underlying_exposure.iloc[12:]["look_through_weight"].sum()
    if remainder > 1e-10:
        top = pd.concat(
            [top, pd.DataFrame([{"asset": "Other", "asset_class": "Mixed", "look_through_weight": remainder}])],
            ignore_index=True,
        )
    exposure_columns = st.columns(2)
    with exposure_columns[0]:
        st.plotly_chart(exposure_figure(top, title="Largest underlying asset exposures"), width="stretch")
    with exposure_columns[1]:
        classes = analysis.asset_class_exposure.rename(
            columns={"asset_class": "Asset class", "look_through_weight": "Look-through allocation (%)"}
        )
        classes["Look-through allocation (%)"] *= 100
        _display_table(classes.round(3), height=36 * len(classes) + 38)
        crypto_weight = float(
            analysis.asset_class_exposure.loc[
                analysis.asset_class_exposure["asset_class"].eq("crypto"), "look_through_weight"
            ].sum()
        )
        st.metric("Look-through crypto exposure", f"{crypto_weight:.2%}")

    allocation_download = analysis.path.assign(
        allocation_definition="; ".join(
            f"{fund_id}={weight:.4f}" for fund_id, weight in allocations.items()
        )
    )
    _section_header_with_download(
        "Overlap and correlation",
        allocation_download,
        "Download allocation history",
        "stockist_hypothetical_allocation.csv",
        "allocation_download",
    )
    if not analysis.overlap.empty:
        overlap = analysis.overlap.rename(
            columns={"fund_a": "Fund A", "fund_b": "Fund B", "holdings_overlap": "Latest holdings overlap (%)"}
        )
        overlap["Latest holdings overlap (%)"] *= 100
        average_overlap = float(analysis.overlap["holdings_overlap"].mean())
        if average_overlap >= 0.50:
            st.warning(
                f"Average pairwise holdings overlap is {average_overlap:.1%}. Several fund labels may not provide equivalent underlying diversification."
            )
        else:
            st.info(f"Average pairwise holdings overlap is {average_overlap:.1%} across the selected funds.")
        _display_table(overlap.round(2), height=36 * len(overlap) + 38)
    correlation = analysis.correlation.copy()
    correlation.insert(0, "Fund", correlation.index)
    _display_table(correlation.round(3), height=36 * len(correlation) + 38)


def _news_signal(artifacts: AppArtifacts) -> None:
    _page_header(
        "News signal",
        "Read market and sector headline tone together with the breadth and concentration of the evidence supporting it.",
    )
    sectors = sorted(artifacts.sentiment["sector"].unique())
    controls = st.columns(3)
    requested_sector = st.query_params.get("sector")
    default_sector = requested_sector if requested_sector in sectors else "Utilities"
    sector_name = controls[0].selectbox("Equity sector", sectors, index=sectors.index(default_sector))
    model_label = controls[1].selectbox("Sentiment model", ["Finance-adjusted VADER", "Plain VADER"])
    window_labels = {
        21: "21 trading days (Monthly)",
        63: "63 trading days (Quarterly)",
    }
    window = controls[2].selectbox(
        "Display window",
        list(window_labels),
        format_func=window_labels.__getitem__,
    )
    _sync_query("sector", sector_name)
    model_prefix = "finance" if model_label.startswith("Finance") else "plain"
    score_column = f"{model_prefix}_sentiment_index"
    market = artifacts.market_sentiment.sort_values("date").copy()
    market_level_column = f"{model_prefix}_fear_greed_index"
    rolling_market = market[market_level_column].rolling(
        window,
        min_periods=window,
    ).mean()
    comparable_market = rolling_market.dropna()
    latest_market_level = float(comparable_market.iloc[-1])
    latest_market_percentile = float(
        comparable_market.le(latest_market_level).mean()
    )
    if latest_market_level < 25:
        latest_market_label = "Extreme fear"
    elif latest_market_level < 45:
        latest_market_label = "Fear"
    elif latest_market_level <= 55:
        latest_market_label = "Neutral"
    elif latest_market_level <= 75:
        latest_market_label = "Greed"
    else:
        latest_market_label = "Extreme greed"
    st.subheader("Market news mood")
    _metric_row(
        [
            (
                f"Latest {window}-day News Fear and Greed",
                f"{latest_market_level:.2f} · {latest_market_label}",
                f"Observed through {market['date'].max():%d %B %Y}; 0 to 100 with VADER neutral at 50.",
            ),
            (
                f"Position among {window}-day readings",
                f"Higher than {latest_market_percentile:.1%}",
                "Compared with historical rolling readings calculated using the same window.",
            ),
            (
                "Rolling readings above neutral",
                f"{comparable_market.gt(50).mean():.1%}",
                "The positive raw-level bias is why the standardized panel is also shown.",
            ),
        ]
    )
    st.plotly_chart(
        fear_greed_figure(
            market,
            model_prefix=model_prefix,
            model_label=model_label,
            window=window,
        ),
        width="stretch",
    )
    st.caption(
        "Equal-weight headline tone across all 50 supplied stocks. The upper panel directly rescales "
        "VADER from -1 to +1 onto 0 to 100 and is zoomed to 44–66 for readability. The lower panel "
        "standardizes daily market tone against the fixed 2020–2023 sample; it is descriptive and is "
        "not the lagged coverage-aware signal used in the fund experiment."
    )
    st.info(
        "This is the Stockist News Fear and Greed Index, not the CNN Fear & Greed Index. "
        "It measures headline language only; low standardized readings can also coincide with thin news coverage."
    )

    st.subheader(f"{sector_name} sector detail")
    sector = artifacts.sentiment.loc[artifacts.sentiment["sector"].eq(sector_name)].sort_values("date")
    supported = sector.loc[sector["has_news"]]
    latest = supported.iloc[-1] if not supported.empty else sector.iloc[-1]
    _metric_row(
        [
            (f"Latest supported {model_label} score", f"{latest[score_column]:+.3f}", f"Observed {latest['date']:%d %B %Y}; -1 to +1."),
            ("Coverage confidence", f"{latest['coverage_confidence']:.2f}", "Evidence breadth and headline-share concentration; not accuracy."),
        ]
    )
    st.caption(
        f"Latest news-supported observation: {latest['date']:%d %B %Y}. "
        f"{int(latest['headline_count'])} aligned headlines; ticker headline-share HHI {latest['ticker_coverage_hhi']:.3f}."
    )
    st.plotly_chart(
        sentiment_figure(sector, score_column=score_column, score_label=model_label, window=window),
        width="stretch",
    )
    st.plotly_chart(coverage_figure(sector, window=window), width="stretch")
    st.info(
        "Coverage confidence measures how broadly and evenly a sector score is supported. "
        "It does not measure whether the language classification is correct or predict a return."
    )

    recent = sector.tail(20)[
        [
            "date",
            "finance_sentiment_index",
            "headline_count",
            "ticker_coverage_hhi",
            "coverage_confidence",
            "has_news",
        ]
    ].copy()
    recent = recent.rename(
        columns={
            "date": "Date",
            "finance_sentiment_index": "Finance sentiment",
            "headline_count": "Headlines",
            "ticker_coverage_hhi": "Headline-share HHI",
            "coverage_confidence": "Coverage confidence",
            "has_news": "Has news",
        }
    )
    with st.expander("Recent exact observations and positive-but-thin examples"):
        numeric = recent.select_dtypes(include="number").columns
        recent[numeric] = recent[numeric].round(3)
        _display_table(recent, height=400)
        examples = artifacts.sentiment.loc[
            artifacts.sentiment["has_news"]
            & artifacts.sentiment["finance_sentiment_index"].gt(0)
            & artifacts.sentiment["coverage_confidence"].lt(0.25),
            ["date", "sector", "finance_sentiment_index", "headline_count", "coverage_confidence"],
        ].tail(12)
        st.markdown("**Positive finance sentiment with thin coverage evidence**")
        st.caption("A positive score is not automatically a buy signal, especially when sector coverage is narrow.")
        examples = examples.rename(
            columns={
                "date": "Date",
                "sector": "Sector",
                "finance_sentiment_index": "Finance sentiment",
                "headline_count": "Headlines",
                "coverage_confidence": "Coverage confidence",
            }
        )
        numeric = examples.select_dtypes(include="number").columns
        examples[numeric] = examples[numeric].round(3)
        _display_table(examples, height=400)

    st.subheader("Plain versus finance-adjusted VADER")
    validation = artifacts.plain_finance_validation.copy()
    validation["measure"] = validation["measure"].str.replace("_", " ").str.title()
    validation = validation.rename(
        columns={
            "measure": "Measure",
            "plain_vader": "Plain VADER",
            "finance_vader": "Finance-adjusted VADER",
            "difference_finance_minus_plain": "Difference",
            "unit": "Unit",
            "interpretation_limit": "Interpretation limit",
        }
    )
    _display_table(validation.round(4), height=36 * len(validation) + 38)

    st.subheader("Measured fund effect")
    st.plotly_chart(fusion_growth_figure(artifacts.fusion_returns), width="stretch")
    comparison = artifacts.fusion_comparison.loc[
        artifacts.fusion_comparison["variant"].isin(["base", "coverage_aware_finance"]),
        [
            "variant_label",
            "net_annualized_return",
            "net_annualized_volatility",
            "net_sharpe_ratio",
            "net_maximum_drawdown",
            "cumulative_turnover",
        ],
    ].copy()
    comparison.columns = [
        "Variant",
        "Annualised return after trading costs (%)",
        "Annualised volatility (%)",
        "Sharpe ratio",
        "Maximum drawdown (%)",
        "Cumulative turnover (×)",
    ]
    comparison.iloc[:, [1, 2, 4]] *= 100
    _display_table(comparison.round(3), height=36 * len(comparison) + 38)
    st.warning(
        "The pre-specified coverage-aware tilt produced a lower annualised return and Sharpe than its otherwise-identical base. "
        "It achieved a slightly shallower maximum drawdown but increased turnover. The negative result is retained."
    )
    st.caption(
        "The same-day finance score is multiplied by coverage confidence, then lagged by one observed sector date before a monthly decision. "
        "Crypto receives no invented news signal."
    )


def _footer() -> None:
    st.markdown(
        f"""
        <div class="footer">
        Stockist Funds v{APP_VERSION} · FINS5545 coursework prototype · Analytical artifacts validated {BUILD_DATE}.<br>
        Historical simulation using supplied 2020–2023 data. Past simulated performance is not a forecast or financial advice.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_app(project_root: Path) -> None:
    """Render the complete artifact-only Stockist Funds experience."""
    st.set_page_config(
        page_title="Stockist Funds",
        page_icon=":material/account_balance:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    requested = st.query_params.get("view")
    pending_view = st.session_state.pop("stockist_pending_view", None)
    if pending_view in VIEWS:
        st.session_state["stockist_view"] = pending_view
    elif st.session_state.get("stockist_view") not in VIEWS:
        st.session_state["stockist_view"] = requested if requested in VIEWS else VIEWS[0]
    view = st.session_state["stockist_view"]
    with st.sidebar.container(key="sidebar_brand"):
        st.image(
            Path(project_root).resolve() / "assets" / "stockist_spartan_logo.png",
            width=88,
        )
        st.markdown("## Stockist Funds")
        st.caption("Systematic investing with inspectable evidence")
    navigation = (
        ("Overview", ":material/dashboard:"),
        ("Compare funds", ":material/compare_arrows:"),
        ("Fund details", ":material/description:"),
        ("Allocation lab", ":material/pie_chart:"),
        ("News signal", ":material/newspaper:"),
    )
    with st.sidebar.container(key="sidebar_nav"):
        st.markdown(
            '<div class="sidebar-section-label">NAVIGATION</div>',
            unsafe_allow_html=True,
        )
        for destination, icon in navigation:
            if st.button(
                destination,
                key=f"sidebar_nav_{destination.lower().replace(' ', '_')}",
                icon=icon,
                type="primary" if destination == view else "tertiary",
                width="stretch",
            ):
                _navigate(destination)
    _sync_query("view", view)
    with st.sidebar.container(key="sidebar_footer"):
        st.markdown(
            f"""
            <div class="sidebar-footer">
                <p>Funds follow a monthly review and rebalancing schedule.</p>
                <p>Version {APP_VERSION} · Data through 2023</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    try:
        artifacts = _cached_artifacts(str(Path(project_root).resolve()))
    except (AppArtifactError, OSError, pd.errors.ParserError) as exc:
        st.error("Stockist Funds could not load its validated evidence files.")
        st.code(str(exc))
        st.info("Run `python scripts/run_part_b.py`, then reload the app.")
        st.stop()
    catalog = fund_catalog(artifacts)
    renderers = {
        "Overview": lambda: _overview(artifacts, catalog),
        "Compare funds": lambda: _compare_funds(artifacts, catalog),
        "Fund details": lambda: _fund_details(artifacts, catalog),
        "Allocation lab": lambda: _allocation_lab(artifacts, catalog),
        "News signal": lambda: _news_signal(artifacts),
    }
    renderers[view]()
    _footer()


__all__ = ["VIEWS", "render_app"]
