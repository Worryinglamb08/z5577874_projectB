"""Stockist Funds Streamlit entrypoint.

Run from the Project B root with ``streamlit run streamlit_app.py``.
The interface reads committed precomputed artifacts only; it does not load raw
data, score headlines, optimise portfolios, or rerun backtests.
"""

from __future__ import annotations

from pathlib import Path

from src.app_views import render_app

PROJECT_ROOT = Path(__file__).resolve().parent

render_app(PROJECT_ROOT)
