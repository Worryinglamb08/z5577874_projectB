"""Every-page Streamlit smoke tests for Stockist Funds."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIEWS = {
    "Overview": "Systematic funds, inspectable evidence",
    "Compare funds": "Aligned evidence",
    "Fund details": "Latest simulated target weights",
    "Allocation lab": "Combined historical evidence",
    "News signal": "Measured fund effect",
}


def test_metric_cards_wrap_at_two_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    from src import app_views

    row_sizes: list[int] = []
    rendered_labels: list[str] = []

    class MetricColumn:
        def metric(self, label: str, value: str, *, help: str) -> None:
            del value, help
            rendered_labels.append(label)

    def columns(count: int) -> list[MetricColumn]:
        row_sizes.append(count)
        return [MetricColumn() for _ in range(count)]

    monkeypatch.setattr(app_views.st, "columns", columns)
    metrics = [(f"Metric {index}", str(index), "Definition") for index in range(5)]

    app_views._metric_row(metrics)

    assert row_sizes == [2, 2, 1]
    assert rendered_labels == [f"Metric {index}" for index in range(5)]


@pytest.mark.parametrize(("view", "expected_text"), VIEWS.items())
def test_every_investor_view_renders(view: str, expected_text: str) -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = view
    app.query_params["fund"] = "combined_risk_parity"
    app.query_params["benchmark"] = "sp500_spy"
    app.query_params["sector"] = "Utilities"
    app.run()

    assert not app.exception, f"{view} raised: {app.exception}"
    assert not app.error, f"{view} displayed errors: {app.error}"
    rendered_text = "\n".join(
        str(element.value)
        for collection in [
            app.title,
            app.header,
            app.subheader,
            app.caption,
            app.markdown,
            app.info,
            app.warning,
            app.metric,
            app.button,
            getattr(app, "download_button", []),
        ]
        for element in collection
    )
    assert expected_text in rendered_text
    removed_strip = "Historical out-of-sample simulation · Monthly primary specification"
    assert removed_strip not in rendered_text


def test_overview_compare_button_navigates_without_mutating_rendered_widget() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Overview"
    app.run()

    compare_button = next(
        button for button in app.button if button.label == "Compare monthly funds"
    )
    stylesheet = next(
        markdown.value
        for markdown in app.markdown
        if "st-key-overview_compare_funds" in str(markdown.value)
    )
    assert compare_button.key == "overview_compare_funds"
    assert "color:#FFFFFF !important" in stylesheet
    compare_button.click().run()

    assert not app.exception, f"Navigation raised: {app.exception}"
    assert not app.error, f"Navigation displayed errors: {app.error}"
    assert app.session_state["stockist_view"] == "Compare funds"
    assert any(title.value == "Compare monthly funds" for title in app.title)


def test_sidebar_navigation_is_button_styled_with_bottom_metadata() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Overview"
    app.run()

    stylesheet = next(
        markdown.value
        for markdown in app.markdown
        if "stSidebarUserContent" in str(markdown.value)
    )
    footer = next(
        markdown.value
        for markdown in app.markdown
        if str(markdown.value).startswith('<div class="sidebar-footer">')
    )
    navigation = [
        button
        for button in app.button
        if str(button.key).startswith("sidebar_nav_")
    ]
    assert not app.radio
    assert [button.label for button in navigation] == list(VIEWS)
    assert ".st-key-sidebar_nav .stButton > button" in stylesheet
    assert '[data-testid^="stBaseButton-"] > div' in stylesheet
    assert "justify-content:flex-start !important" in stylesheet
    assert "font-size:1rem !important" in stylesheet
    assert '.st-key-sidebar_brand [data-testid="stImage"]' in stylesheet
    assert "justify-content:center" in stylesheet
    assert ".st-key-sidebar_footer" in stylesheet
    assert "margin-top:auto" in stylesheet
    assert "position:absolute" not in stylesheet
    assert "Funds follow a monthly review" in footer
    assert "Version 0.9 · Data through 2023" in footer

    next(button for button in navigation if button.label == "Fund details").click().run()
    assert not app.exception, f"Sidebar navigation raised: {app.exception}"
    assert app.session_state["stockist_view"] == "Fund details"


def test_sidebar_logo_is_a_local_transparent_asset() -> None:
    image_module = pytest.importorskip("PIL.Image")
    logo_path = PROJECT_ROOT / "assets" / "stockist_spartan_logo.png"

    assert logo_path.is_file()
    with image_module.open(logo_path) as logo:
        assert logo.mode == "RGBA"
        alpha = logo.getchannel("A")
        assert alpha.getextrema() == (0, 255)
        assert alpha.getpixel((0, 0)) == 0


def test_overview_explains_methods_after_asset_families() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Overview"
    app.run()

    assert not app.exception, f"Overview raised: {app.exception}"
    subheaders = [subheader.value for subheader in app.subheader]
    assert subheaders.index("Choose an asset family before choosing a method") < (
        subheaders.index("Choose a portfolio method")
    ) < subheaders.index("Build an allocation") < subheaders.index("What you can inspect")
    rendered_cards = "\n".join(str(markdown.value) for markdown in app.markdown)
    assert rendered_cards.count('class="step-grid"') == 1
    assert rendered_cards.count('class="step-card"') == 4
    assert rendered_cards.count('class="family-grid"') == 1
    assert rendered_cards.count('class="stockist-card family-card"') == 3
    assert rendered_cards.count('class="card-chips"') == 3
    assert rendered_cards.count('class="method-grid"') == 1
    assert rendered_cards.count('class="stockist-card method-card"') == 5
    assert rendered_cards.count('class="allocation-overview-grid"') == 1
    assert rendered_cards.count('class="stockist-card allocation-overview-card"') == 3
    assert rendered_cards.count('class="inspect-grid"') == 1
    assert rendered_cards.count('class="stockist-card inspect-card"') == 4
    assert ".inspect-grid { display:grid; grid-template-columns:repeat(4" in rendered_cards
    for method_label in (
        "Equal Weight",
        "Minimum Variance",
        "Risk Parity",
        "Maximum Sharpe",
        "Hierarchical Risk Parity",
    ):
        assert f"<h3>{method_label}</h3>" in rendered_cards
    for allocation_label in (
        "Set fund weights",
        "See the combined exposure",
        "Measure the historical outcome",
    ):
        assert f"<h3>{allocation_label}</h3>" in rendered_cards
    assert "Combine two to four Stockist funds" in rendered_cards
    assert any(button.label == "Open allocation lab" for button in app.button)
    for inspect_label in (
        "Performance &amp; risk",
        "Portfolio construction",
        "Implementation",
        "News signal experiment",
    ):
        assert f"<h3>{inspect_label}</h3>" in rendered_cards
    assert "coverage-aware sentiment tilt" in rendered_cards


def test_overview_allocation_button_opens_allocation_lab() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Overview"
    app.run()

    allocation_button = next(
        button for button in app.button if button.label == "Open allocation lab"
    )
    allocation_button.click().run()

    assert not app.exception, f"Allocation navigation raised: {app.exception}"
    assert app.session_state["stockist_view"] == "Allocation lab"
    assert any(title.value == "Allocation lab" for title in app.title)


def test_removed_methods_route_falls_back_to_overview() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Methods & data"
    app.session_state["stockist_view"] = "Methods & data"
    app.run()

    assert not app.exception, f"Removed route raised: {app.exception}"
    assert app.session_state["stockist_view"] == "Overview"
    navigation = [
        button.label
        for button in app.button
        if str(button.key).startswith("sidebar_nav_")
    ]
    assert navigation == list(VIEWS)
    assert "Methods & data" not in navigation
    assert any(title.value == "Systematic funds, inspectable evidence" for title in app.title)


def test_fund_details_can_switch_to_nasdaq_benchmark() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Fund details"
    app.query_params["fund"] = "equity_minimum_variance"
    app.query_params["benchmark"] = "sp500_spy"
    app.run()

    chart_titles = [
        json.loads(chart.proto.spec)["layout"]["title"]["text"]
        for chart in app.get("plotly_chart")
    ]
    assert "How is the target portfolio allocated by sector?" in chart_titles
    assert (
        "How did the target sector allocation change through time?" in chart_titles
    )

    benchmark_select = next(
        selectbox for selectbox in app.selectbox if selectbox.label == "Benchmark"
    )
    benchmark_select.select("nasdaq_composite_oneq").run()

    assert not app.exception, f"Benchmark switch raised: {app.exception}"
    assert not app.error, f"Benchmark switch displayed errors: {app.error}"
    assert app.session_state["selected_benchmark_id"] == "nasdaq_composite_oneq"
    assert any("Nasdaq Composite" in str(caption.value) for caption in app.caption)


def test_complete_weight_download_sits_beside_table_heading() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Fund details"
    app.query_params["fund"] = "combined_risk_parity"
    app.run()

    columns = list(app.get("column"))
    heading_index = next(
        index
        for index, column in enumerate(columns)
        if any(
            type(child).__name__ == "Markdown"
            and child.value == "**Complete target-weight table**"
            for child in column.children.values()
        )
    )
    download_index = next(
        index
        for index, column in enumerate(columns)
        if any(
            getattr(child, "label", None) == "Download complete weight vector"
            for child in column.children.values()
        )
    )
    assert download_index == heading_index + 1
    assert columns[heading_index].proto.weight == pytest.approx(0.76)
    assert columns[download_index].proto.weight == pytest.approx(0.24)


@pytest.mark.parametrize(
    ("view", "heading", "download_label"),
    [
        ("Compare funds", "Aligned evidence", "Download selected comparison"),
        (
            "Fund details",
            "Historical performance",
            "Download fund return history",
        ),
        ("Allocation lab", "Overlap and correlation", "Download allocation history"),
    ],
)
def test_section_download_is_right_aligned_beside_heading(
    view: str,
    heading: str,
    download_label: str,
) -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = view
    app.run()

    assert not app.exception, f"{view} raised: {app.exception}"
    columns = list(app.get("column"))
    heading_index = next(
        index
        for index, column in enumerate(columns)
        if any(
            type(child).__name__ == "Subheader" and child.value == heading
            for child in column.children.values()
        )
    )
    download_index = next(
        index
        for index, column in enumerate(columns)
        if any(
            getattr(child, "label", None) == download_label
            for child in column.children.values()
        )
    )
    assert download_index == heading_index + 1
    assert columns[heading_index].proto.weight == pytest.approx(0.76)
    assert columns[download_index].proto.weight == pytest.approx(0.24)


def test_compare_filters_remove_selected_funds_that_no_longer_match() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Compare funds"
    app.run()

    assert [control.label for control in app.multiselect] == ["Selected funds"]
    assert app.selectbox[0].label == "Benchmark"
    filters = app.get("button_group")
    assert [control.label for control in filters] == [
        "Asset family",
        "Portfolio method",
    ]
    assert app.multiselect[0].value == [
        "equity_minimum_variance",
        "combined_risk_parity",
    ]
    assert app.multiselect[0].max_selections == 5
    chart_titles = [
        json.loads(chart.proto.spec)["layout"]["title"]["text"]
        for chart in app.get("plotly_chart")
    ]
    assert chart_titles == [
        "How did the selected funds compound?",
        "How did return and volatility compare?",
    ]

    five_funds = [
        "equity_minimum_variance",
        "combined_risk_parity",
        "crypto_equal_weight",
        "equity_maximum_sharpe",
        "combined_hierarchical_risk_parity",
    ]
    app.multiselect[0].set_value(five_funds).run()
    assert not app.exception, f"Five-fund comparison raised: {app.exception}"
    assert app.multiselect[0].value == five_funds

    filters = app.get("button_group")
    filters[0].set_value(["equity"])
    filters[1].set_value(["minimum_variance"])
    app.run()

    assert not app.exception, f"Compare filter change raised: {app.exception}"
    assert app.multiselect[0].value == ["equity_minimum_variance"]
    assert len(app.multiselect[0].options) == 1
    assert any(
        caption.value == "1 of 15 funds available to add." for caption in app.caption
    )


def test_allocation_uses_one_component_and_reset_restores_equal_weights() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Allocation lab"
    app.run()

    component_key = (
        "allocation_mix_equity_equal_weight_to_crypto_equal_weight_to_"
        "combined_equal_weight"
    )
    assert len(app.get("bidi_component")) == 1
    assert not app.slider
    assert [field.label for field in app.number_input] == ["Illustrative balance (AUD)"]
    fee_metric = next(
        metric for metric in app.metric if metric.label == "Estimated annual product fee"
    )
    assert fee_metric.value == "A$12"
    assert fee_metric.delta == "0.12% of A$10,000; fixed by the fund"
    assert app.session_state[component_key] == {"weights": [34, 33, 33]}

    benchmark_select = next(
        selectbox
        for selectbox in app.selectbox
        if selectbox.label == "Allocation benchmark"
    )
    assert benchmark_select.value == "equal_selected_funds"
    assert any(
        info.value.startswith("The chosen weights are currently very close")
        for info in app.info
    )

    app.session_state[component_key] = {"weights": [20, 30, 50]}
    app.run()
    assert not app.exception, f"Custom allocation state raised: {app.exception}"
    assert app.session_state[component_key] == {"weights": [20, 30, 50]}

    reset = next(
        button
        for button in app.button
        if button.label == "Reset to equal-allocation example"
    )
    reset.click().run()

    assert not app.exception, f"Allocation reset raised: {app.exception}"
    assert not app.error, f"Allocation reset displayed errors: {app.error}"
    assert app.session_state[component_key] == {"weights": [34, 33, 33]}


def test_allocation_can_switch_to_external_benchmark() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "Allocation lab"
    app.run()

    benchmark_select = next(
        selectbox
        for selectbox in app.selectbox
        if selectbox.label == "Allocation benchmark"
    )
    benchmark_select.select("sp500_spy").run()

    assert not app.exception, f"Allocation benchmark switch raised: {app.exception}"
    assert not app.error, f"Allocation benchmark switch displayed errors: {app.error}"
    assert app.session_state["selected_allocation_benchmark_id"] == "sp500_spy"
    assert app.query_params["allocation_benchmark"] == ["sp500_spy"]
    assert any(
        "S&P 500 (SPY total-return proxy): 04 Jan 2021 to 29 Dec 2023"
        in str(caption.value)
        for caption in app.caption
    )
    chart_specs = [
        json.loads(chart.proto.spec) for chart in app.get("plotly_chart")
    ]
    growth = next(
        figure
        for figure in chart_specs
        if figure["layout"]["title"]["text"]
        == "How did the hypothetical fund mix compound against its benchmark?"
    )
    assert [trace["name"] for trace in growth["data"]] == [
        "Chosen allocation",
        "S&P 500 (SPY total-return proxy)",
    ]


def test_news_signal_omits_confusing_coverage_fields() -> None:
    pytest.importorskip("streamlit.testing.v1")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(PROJECT_ROOT / "streamlit_app.py", default_timeout=30)
    app.query_params["view"] = "News signal"
    app.query_params["sector"] = "Utilities"
    app.run()

    assert not app.exception, f"News Signal raised: {app.exception}"
    assert not app.error, f"News Signal displayed errors: {app.error}"
    metric_labels = [metric.label for metric in app.metric]
    assert "Coverage confidence" in metric_labels
    assert "Companies covered" not in metric_labels
    assert "Evidence status" not in metric_labels
    assert "Latest 21-day News Fear and Greed" in metric_labels
    chart_titles = [
        json.loads(chart.proto.spec)["layout"]["title"]["text"]
        for chart in app.get("plotly_chart")
    ]
    assert chart_titles[0] == "Stockist News Fear and Greed Index"
    subheaders = [subheader.value for subheader in app.subheader]
    assert subheaders.index("Market news mood") < subheaders.index(
        "Utilities sector detail"
    )
    assert any(
        "not the CNN Fear & Greed Index" in str(info.value) for info in app.info
    )
    display_window = next(
        selectbox for selectbox in app.selectbox if selectbox.label == "Display window"
    )
    assert list(display_window.options) == [
        "21 trading days (Monthly)",
        "63 trading days (Quarterly)",
    ]
    for table in app.dataframe:
        columns = set(table.value.columns)
        assert "Companies covered" not in columns
        assert "Evidence status" not in columns


def test_deployed_entrypoint_does_not_import_build_or_raw_data_modules() -> None:
    files = [
        PROJECT_ROOT / "streamlit_app.py",
        PROJECT_ROOT / "src" / "app_views.py",
        PROJECT_ROOT / "src" / "app_data.py",
        PROJECT_ROOT / "src" / "app_logic.py",
        PROJECT_ROOT / "src" / "app_charts.py",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    assert "import nltk" not in source
    assert "from src import data_access" not in source
    assert "from src.data_access" not in source
    assert "from src.portfolios" not in source
    assert "from src.sentiment" not in source
    assert "from src.fusion" not in source
    assert "import yfinance" not in source


def test_app_has_an_explicit_light_stockist_theme() -> None:
    config = tomllib.loads(
        (PROJECT_ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    )
    theme = config["theme"]
    sidebar = theme["sidebar"]

    assert theme["base"] == "light"
    assert theme["primaryColor"] == "#0F766E"
    assert theme["backgroundColor"] == "#F4F6F5"
    assert theme["secondaryBackgroundColor"] == "#FFFFFF"
    assert theme["textColor"] == "#0F172A"
    assert sidebar["backgroundColor"] == "#E9EFF0"
    assert sidebar["textColor"] == "#0F172A"
