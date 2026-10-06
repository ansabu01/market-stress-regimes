"""Compatibility entry point for the app-contained dashboard exporter."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.scripts.export_dashboard_data import main


if __name__ == "__main__":
    main()
