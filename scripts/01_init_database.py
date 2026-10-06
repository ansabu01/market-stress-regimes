"""
Initialize and verify the project DuckDB database file.

Inputs:
- Project database path from settings.DB_PATH

Outputs:
- Verifies the data directory exists
- Creates or opens the DuckDB database file
- Removes an empty placeholder database file before DuckDB opens it

Notes:
- Does not create analysis tables.
- Later scripts create their own tables from SQL schema files.
"""

from pathlib import Path
import sys

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from settings import DB_PATH, require_data_dir


def main() -> None:
    require_data_dir()

    if DB_PATH.exists() and DB_PATH.stat().st_size == 0:
        DB_PATH.unlink()

    with duckdb.connect(str(DB_PATH)) as con:
        con.execute("SELECT 1")

    print(f"Database initialized: {DB_PATH}")


if __name__ == "__main__":
    main()
