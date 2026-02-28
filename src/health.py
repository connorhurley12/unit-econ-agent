"""Health diagnostic display helpers (pure Python — no Streamlit)."""

from __future__ import annotations

from typing import Dict, List

from src.model import HealthFlag


# Color scheme per severity
SEVERITY_COLORS: Dict[str, str] = {
    "positive": "#10B981",  # green
    "critical": "#EF4444",  # red
    "warning": "#F59E0B",   # amber
    "watch": "#3B82F6",     # blue
}

SEVERITY_BG_COLORS: Dict[str, str] = {
    "positive": "#D1FAE5",
    "critical": "#FEE2E2",
    "warning": "#FEF3C7",
    "watch": "#DBEAFE",
}

SEVERITY_ICONS: Dict[str, str] = {
    "positive": "🟢",
    "critical": "🔴",
    "warning": "🟡",
    "watch": "🔵",
}

SEVERITY_ORDER = ["positive", "critical", "warning", "watch"]


def sort_flags(flags: List[HealthFlag]) -> List[HealthFlag]:
    """Sort flags by severity: critical first, then warning, then watch."""
    order = {s: i for i, s in enumerate(SEVERITY_ORDER)}
    return sorted(flags, key=lambda f: order.get(f.severity, 99))


def health_score_color(score: int) -> str:
    """Return a hex color for the health score badge."""
    if score >= 70:
        return "#10B981"  # green
    if score >= 40:
        return "#F59E0B"  # amber
    return "#EF4444"      # red
