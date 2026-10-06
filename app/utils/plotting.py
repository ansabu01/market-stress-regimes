"""Reusable Plotly styling and chart builders for the dashboard.

A single dark template plus a small set of chart factories (heatmaps, dumbbell,
grouped bars, decomposition) so every page renders with identical typography,
gridlines, margins, and semantic colors.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app.utils.theme import CORR_DIVERGING, PALETTE, SEMANTIC

FONT_FAMILY = '-apple-system, "Segoe UI", Roboto, Inter, "Helvetica Neue", sans-serif'


def base_layout(height: int = 420, *, legend: bool = False, **overrides) -> dict:
    """Return a design-system layout dict shared by all figures."""
    layout = dict(
        height=height,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=12, color=PALETTE["text_muted"]),
        margin=dict(l=48, r=22, t=30, b=40),
        hoverlabel=dict(
            bgcolor=PALETTE["elevated"],
            bordercolor=PALETTE["border"],
            font=dict(family=FONT_FAMILY, size=12, color=PALETTE["text"]),
        ),
        showlegend=legend,
    )
    if legend:
        layout["legend"] = dict(
            orientation="h", yanchor="bottom", y=1.02, x=0,
            font=dict(size=11, color=PALETTE["text_muted"]),
            bgcolor="rgba(0,0,0,0)",
        )
    layout.update(overrides)
    # Drop None-valued keys (e.g. title=None) so Plotly does not render "undefined".
    return {key: value for key, value in layout.items() if value is not None}


def style_axes(fig: go.Figure) -> go.Figure:
    """Apply consistent axis styling (subtle grid, muted ticks, no spikes)."""
    fig.update_xaxes(
        gridcolor=PALETTE["grid"], zerolinecolor=PALETTE["border"],
        linecolor=PALETTE["border"], tickfont=dict(color=PALETTE["text_muted"], size=11),
        title_font=dict(color=PALETTE["text_muted"], size=12),
    )
    fig.update_yaxes(
        gridcolor=PALETTE["grid"], zerolinecolor=PALETTE["border"],
        linecolor=PALETTE["border"], tickfont=dict(color=PALETTE["text_muted"], size=11),
        title_font=dict(color=PALETTE["text_muted"], size=12),
    )
    return fig


def finalize(fig: go.Figure, height: int = 420, *, legend: bool = False, **overrides) -> go.Figure:
    """Apply the base layout + axis styling in one call."""
    fig.update_layout(**base_layout(height, legend=legend, **overrides))
    return style_axes(fig)


# --- Correlation heatmaps -----------------------------------------------------

def _matrix_text(matrix: pd.DataFrame) -> list[list[str]]:
    out = []
    for row in matrix.index:
        out.append(["" if pd.isna(matrix.loc[row, col]) else f"{matrix.loc[row, col]:.2f}"
                    for col in matrix.columns])
    return out


def correlation_heatmap(
    matrix: pd.DataFrame, *, title: str = "", zmin: float = -1.0, zmax: float = 1.0,
    value_label: str = "Correlation", height: int = 460, show_values: bool = True,
) -> go.Figure:
    """Single diverging correlation/delta heatmap on the design-system scale."""
    fig = go.Figure(
        go.Heatmap(
            z=matrix.to_numpy(dtype=float), x=list(matrix.columns), y=list(matrix.index),
            zmin=zmin, zmax=zmax, zmid=0.0, colorscale=CORR_DIVERGING,
            text=_matrix_text(matrix) if show_values else None,
            texttemplate="%{text}" if show_values else None,
            textfont=dict(size=10, color=PALETTE["text"]),
            colorbar=dict(
                title=dict(text=value_label, font=dict(color=PALETTE["text_muted"], size=11)),
                thickness=12, len=0.82, tickfont=dict(color=PALETTE["text_muted"], size=10),
                outlinecolor=PALETTE["border"], outlinewidth=1,
            ),
            hovertemplate="<b>%{y} · %{x}</b><br>" + value_label + ": %{z:.3f}<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(side="top", tickangle=-45)
    finalize(fig, height, title=(dict(text=title, font=dict(color=PALETTE["text"], size=14)) if title else None),
             margin=dict(l=54, r=20, t=64 if title else 46, b=20))
    return fig


# --- Regime paired bars (calm vs stress) --------------------------------------

def calm_stress_bars(
    categories: list[str], calm_values: list[float], stress_values: list[float], *,
    value_fmt: str = ".2f", tickformat: str | None = None, title: str = "",
    yaxis_title: str = "", height: int = 360, hover_suffix: str = "",
) -> go.Figure:
    """Grouped calm/stress bars with the fixed regime colors."""
    fig = go.Figure()
    fig.add_bar(
        x=categories, y=calm_values, name="Calm", marker_color=SEMANTIC["calm"],
        text=[f"{v:{value_fmt}}" for v in calm_values], textposition="outside",
        textfont=dict(color=PALETTE["text_muted"], size=10),
        hovertemplate="%{x}<br>Calm: %{y:" + value_fmt + "}" + hover_suffix + "<extra></extra>",
    )
    fig.add_bar(
        x=categories, y=stress_values, name="Stress", marker_color=SEMANTIC["stress"],
        text=[f"{v:{value_fmt}}" for v in stress_values], textposition="outside",
        textfont=dict(color=PALETTE["text_muted"], size=10),
        hovertemplate="%{x}<br>Stress: %{y:" + value_fmt + "}" + hover_suffix + "<extra></extra>",
    )
    finalize(fig, height, legend=True, barmode="group", yaxis_title=yaxis_title,
             title=(dict(text=title, font=dict(color=PALETTE["text"], size=13)) if title else None))
    if tickformat:
        fig.update_yaxes(tickformat=tickformat)
    return fig


# --- Dumbbell / slope for hedge behaviour across episodes ---------------------

def dumbbell(
    labels: list[str], values_by_series: dict[str, list[float]], *, colors: dict[str, str],
    title: str = "", xaxis_title: str = "", height: int = 380, xrange: tuple | None = None,
) -> go.Figure:
    """Horizontal dumbbell: one row per label, a colored marker per series."""
    fig = go.Figure()
    series_names = list(values_by_series)
    # connecting lines (min->max per row across series)
    for i, lab in enumerate(labels):
        row_vals = [values_by_series[s][i] for s in series_names if not pd.isna(values_by_series[s][i])]
        if len(row_vals) >= 2:
            fig.add_trace(go.Scatter(
                x=[min(row_vals), max(row_vals)], y=[lab, lab], mode="lines",
                line=dict(color=PALETTE["border"], width=2), hoverinfo="skip", showlegend=False,
            ))
    for s in series_names:
        fig.add_trace(go.Scatter(
            x=values_by_series[s], y=labels, mode="markers", name=s,
            marker=dict(size=12, color=colors.get(s, SEMANTIC["neutral"]),
                        line=dict(width=1, color=PALETTE["bg"])),
            hovertemplate="<b>%{y}</b><br>" + s + ": %{x:.3f}<extra></extra>",
        ))
    fig.add_vline(x=0, line_color=PALETTE["text_faint"], line_dash="dot", line_width=1)
    finalize(fig, height, legend=True, xaxis_title=xaxis_title,
             title=(dict(text=title, font=dict(color=PALETTE["text"], size=13)) if title else None),
             margin=dict(l=110, r=24, t=44, b=42))
    if xrange:
        fig.update_xaxes(range=list(xrange))
    return fig


# --- Horizontal contribution / decomposition bars -----------------------------

def horizontal_grouped(
    categories: list[str], series: dict[str, tuple[list[float], str]], *,
    title: str = "", xaxis_title: str = "", height: int = 380, tickformat: str | None = None,
) -> go.Figure:
    """Horizontal grouped bars; series maps name -> (values, color)."""
    fig = go.Figure()
    for name, (vals, color) in series.items():
        fig.add_bar(
            y=categories, x=vals, name=name, orientation="h", marker_color=color,
            hovertemplate="%{y}<br>" + name + ": %{x}<extra></extra>",
        )
    fig.add_vline(x=0, line_color=PALETTE["text_faint"], line_width=1)
    finalize(fig, height, legend=len(series) > 1, barmode="group", xaxis_title=xaxis_title,
             title=(dict(text=title, font=dict(color=PALETTE["text"], size=13)) if title else None),
             margin=dict(l=90, r=24, t=44, b=40))
    if tickformat:
        fig.update_xaxes(tickformat=tickformat)
    return fig


def variance_decomposition_bars(
    calm: tuple[float, float], stress: tuple[float, float], *, height: int = 320,
) -> go.Figure:
    """Stacked diagonal vs off-diagonal variance contribution for calm and stress.

    Each tuple is (diagonal_variance, offdiagonal_covariance). Off-diagonal can be
    negative; a stacked bar handles that correctly because Plotly stacks signed.
    """
    regimes = ["Calm", "Stress"]
    diag = [calm[0], stress[0]]
    offd = [calm[1], stress[1]]
    fig = go.Figure()
    fig.add_bar(x=regimes, y=diag, name="Own-variance (diagonal)",
                marker_color=SEMANTIC["neutral"],
                hovertemplate="%{x} · own-variance: %{y:.3e}<extra></extra>")
    fig.add_bar(x=regimes, y=offd, name="Covariance (off-diagonal)",
                marker_color=SEMANTIC["stress"],
                hovertemplate="%{x} · covariance: %{y:.3e}<extra></extra>")
    # total markers
    totals = [diag[0] + offd[0], diag[1] + offd[1]]
    fig.add_trace(go.Scatter(
        x=regimes, y=totals, mode="markers+text", name="Portfolio variance",
        marker=dict(symbol="line-ew", size=26, line=dict(width=3, color=PALETTE["text"])),
        text=[f"{t:.2e}" for t in totals], textposition="top center",
        textfont=dict(color=PALETTE["text"], size=11),
        hovertemplate="%{x} · portfolio variance: %{y:.3e}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=PALETTE["text_faint"], line_width=1)
    finalize(fig, height, legend=True, barmode="relative", yaxis_title="Variance contribution")
    return fig


def add_stress_bands(fig: go.Figure, spans, *, opacity: float = 0.10) -> go.Figure:
    """Shade official stress spans behind a time-series trace."""
    for start, end in spans:
        fig.add_vrect(x0=start, x1=end + pd.Timedelta(days=1),
                      fillcolor=SEMANTIC["stress"], opacity=opacity, line_width=0, layer="below")
    return fig


def empty_note(message: str, height: int = 300) -> go.Figure:
    """A blank figure carrying a centered note (for graceful empty states)."""
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(color=PALETTE["text_faint"], size=13),
                       x=0.5, y=0.5, xref="paper", yref="paper")
    finalize(fig, height)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig
