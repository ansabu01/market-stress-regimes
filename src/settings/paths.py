from pathlib import Path


PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
DB_PATH: Path = DATA_DIR / "lsr.duckdb"


def require_data_dir() -> None:
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Required data directory does not exist: {DATA_DIR}")

    if not DATA_DIR.is_dir():
        raise NotADirectoryError(f"Expected data directory, found something else: {DATA_DIR}")
