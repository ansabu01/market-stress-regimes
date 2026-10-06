"""Cached dashboard data-file loaders."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from app.utils.paths import (
    APP_DATA_DIR,
    EXPECTED_PARQUET_FILES,
    OPTIONAL_PARQUET_FILES,
    repo_relative,
)


def _file_record(filename: str, label: str, optional: bool) -> dict[str, object]:
    path = APP_DATA_DIR / filename
    exists = path.exists()
    stat = path.stat() if exists else None
    modified = datetime.fromtimestamp(stat.st_mtime) if stat else None
    return {
        "file": filename,
        "label": label,
        "optional": optional,
        "exists": exists,
        "path": repo_relative(path),
        "size_bytes": stat.st_size if stat else None,
        "modified": modified,
    }


@st.cache_data(show_spinner=False)
def list_parquet_exports() -> pd.DataFrame:
    """Return expected and optional dashboard parquet export status."""
    records = [
        _file_record(filename, label, optional=False)
        for filename, label in EXPECTED_PARQUET_FILES.items()
    ]
    records.extend(
        _file_record(filename, label, optional=True)
        for filename, label in OPTIONAL_PARQUET_FILES.items()
    )
    return pd.DataFrame(records)


@st.cache_data(show_spinner=False)
def load_parquet(filename: str) -> pd.DataFrame:
    """Load one dashboard parquet file from app/data."""
    path = APP_DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


@st.cache_data(show_spinner=False)
def parquet_schema(filename: str) -> pd.DataFrame:
    """Return a small schema preview for one dashboard parquet file."""
    frame = load_parquet(filename)
    if frame.empty:
        return pd.DataFrame(columns=["column", "dtype"])
    return pd.DataFrame(
        {
            "column": frame.columns,
            "dtype": [str(dtype) for dtype in frame.dtypes],
        }
    )


def parquet_path(filename: str) -> Path:
    """Return the app/data path for a parquet export."""
    return APP_DATA_DIR / filename
