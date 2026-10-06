"""Formatting helpers for compact dashboard status views."""

from __future__ import annotations

from datetime import datetime


def human_bytes(size: int | float | None) -> str:
    """Format byte counts for small status cards."""
    if size is None:
        return "-"

    value = float(size)
    units = ["B", "KB", "MB", "GB"]
    for unit in units:
        if abs(value) < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{value:.0f} {unit}"
        value /= 1024

    return f"{value:.1f} GB"


def human_int(value: int | float | None) -> str:
    """Format integer-like values with separators."""
    if value is None:
        return "-"
    return f"{int(value):,}"


def human_datetime(value: datetime | None) -> str:
    """Format timestamps for file metadata."""
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def status_label(exists: bool, optional: bool = False) -> str:
    """Return a short status label."""
    if exists:
        return "Ready"
    if optional:
        return "Optional"
    return "Missing"

