"""Reusable Streamlit UI components built on the design system.

Page headers, stat-card rows, interpretation panels, the pipeline diagram, and
the official/exploratory provenance chips. HTML is produced here once so pages
stay declarative and visually consistent.
"""

from __future__ import annotations

from html import escape

import streamlit as st

from app.utils.theme import PALETTE, SEMANTIC


def page_header(eyebrow: str, title: str, subtitle: str, *, provenance: str | None = None) -> None:
    """Compact page header: eyebrow label, question-style title, subtitle."""
    chip = ""
    if provenance == "official":
        chip = '<span class="ds-chip ds-official">Official paper result</span>'
    elif provenance == "exploratory":
        chip = '<span class="ds-chip ds-exploratory">Exploratory recomputation</span>'
    st.markdown(
        f"""
        <div class="ds-eyebrow">{escape(eyebrow)}</div>
        <div class="ds-h1">{escape(title)}</div>
        <div class="ds-sub">{escape(subtitle)} {chip}</div>
        """,
        unsafe_allow_html=True,
    )


def section(label: str) -> None:
    """A thin uppercase section divider."""
    st.markdown(f'<div class="ds-section">{escape(label)}</div>', unsafe_allow_html=True)


def caption(text: str) -> None:
    st.markdown(f'<div class="ds-caption">{text}</div>', unsafe_allow_html=True)


def stat_card(label: str, value: str, *, delta: str | None = None, delta_color: str | None = None,
              sub: str | None = None) -> str:
    """Return HTML for one stat card (render several with :func:`stat_row`)."""
    delta_html = ""
    if delta is not None:
        color = delta_color or PALETTE["text_faint"]
        delta_html = f'<div class="delta" style="color:{color}">{escape(delta)}</div>'
    sub_html = f'<div class="sub">{escape(sub)}</div>' if sub else ""
    return (
        f'<div class="ds-card"><div class="lab">{escape(label)}</div>'
        f'<div class="val">{escape(value)}</div>{delta_html}{sub_html}</div>'
    )


def stat_row(cards: list[str]) -> None:
    """Render a row of equal-width stat cards from :func:`stat_card` HTML."""
    cols = st.columns(len(cards))
    for col, card_html in zip(cols, cards):
        with col:
            st.markdown(card_html, unsafe_allow_html=True)


def interpretation_panel(paragraphs: list[str], *, title: str = "What this shows") -> None:
    """Deterministic interpretation panel (accepts inline <b> markup)."""
    body = "".join(f"<p>{para}</p>" for para in paragraphs)
    st.markdown(
        f'<div class="ds-interp"><div class="head">{escape(title)}</div>{body}</div>',
        unsafe_allow_html=True,
    )


def pipeline_diagram() -> None:
    """Six-step research-pipeline process diagram (native HTML/CSS)."""
    steps = [
        ("01", "Market data", "Daily ETF prices, adjusted closes"),
        ("02", "Regime identification", "Two-state Markov stress label on SPY"),
        ("03", "Conditional dependence", "Calm vs stress correlations"),
        ("04", "Bootstrap inference", "Block bootstrap + FDR control"),
        ("05", "PCA concentration", "PC1 share and effective bets"),
        ("06", "Forbes–Rigobon", "Volatility-adjusted diagnosis"),
    ]
    cells = "".join(
        f'<div class="ds-pipe-step"><div class="n">{n}</div>'
        f'<div class="t">{escape(t)}</div><div class="d">{escape(d)}</div></div>'
        for n, t, d in steps
    )
    st.markdown(f'<div class="ds-pipe">{cells}</div>', unsafe_allow_html=True)


def finding_card(kicker_color: str, kicker: str, heading: str, body: str) -> str:
    """Return HTML for a home-page empirical-finding card."""
    return (
        f'<div class="ds-find"><div class="k" style="color:{kicker_color}">{escape(kicker)}</div>'
        f'<div class="h">{escape(heading)}</div><div class="b">{escape(body)}</div></div>'
    )


def module_card(title: str, description: str) -> str:
    """Return HTML for a navigation module card."""
    return (
        f'<div class="ds-card" style="min-height:96px">'
        f'<div class="val" style="font-size:1.02rem">{escape(title)}</div>'
        f'<div class="sub" style="margin-top:0.3rem">{escape(description)}</div></div>'
    )


def signed(value: float, fmt: str = "+.3f", *, pct: bool = False) -> tuple[str, str]:
    """Return (text, color) for a signed delta on the neutral/stress/calm scale."""
    if value is None or value != value:  # NaN
        return "—", PALETTE["text_faint"]
    text = f"{value * 100:{fmt}}%" if pct else f"{value:{fmt}}"
    if abs(value) < 1e-9:
        return text, PALETTE["text_faint"]
    return text, (SEMANTIC["stress"] if value > 0 else SEMANTIC["calm"])
