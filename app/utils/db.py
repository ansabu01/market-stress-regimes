"""Cached read-only DuckDB access for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import duckdb

from app.utils.paths import DB_PATH


@st.cache_data(show_spinner=False)
def database_exists() -> bool:
    """Return whether the project DuckDB file exists."""
    return DB_PATH.exists()


@st.cache_data(show_spinner=False)
def query_duckdb(sql: str) -> pd.DataFrame:
    """Run a read-only query against the project DuckDB database."""
    if not DB_PATH.exists():
        return pd.DataFrame()

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(sql).fetchdf()


@st.cache_data(show_spinner=False)
def list_duckdb_tables() -> list[str]:
    """List available DuckDB tables using a read-only connection."""
    if not DB_PATH.exists():
        return []

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        rows = con.execute("SHOW TABLES").fetchall()

    return sorted(row[0] for row in rows)


@st.cache_data(show_spinner=False)
def duckdb_table_overview() -> pd.DataFrame:
    """Return table names and row counts for the status page."""
    if not DB_PATH.exists():
        return pd.DataFrame(columns=["table", "rows"])

    rows = []
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        table_names = sorted(row[0] for row in con.execute("SHOW TABLES").fetchall())
        for table_name in table_names:
            escaped_name = table_name.replace('"', '""')
            row_count = con.execute(f'SELECT COUNT(*) FROM "{escaped_name}"').fetchone()[0]
            rows.append({"table": table_name, "rows": int(row_count)})

    return pd.DataFrame(rows)
