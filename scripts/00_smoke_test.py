"""
Run a minimal project startup check.

Inputs:
- Project configuration from src/settings

Outputs:
- Verifies the data directory exists
- Prints the project root, data directory, and database path

Notes:
- Does not connect to DuckDB.
- Does not create database tables.
- Intended as the first lightweight check before running the full pipeline.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import settings


def main() -> None:
    settings.require_data_dir()

    print("Smoke test passed")
    print(f"Project root: {settings.PROJECT_ROOT}")
    print(f"Data directory: {settings.DATA_DIR}")
    print(f"Database path: {settings.DB_PATH}")


if __name__ == "__main__":
    main()
