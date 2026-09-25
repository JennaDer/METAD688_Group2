"""Shared Plotly theme for the Group 2 site.

Import once at the top of a page or script:

    import sys
    sys.path.insert(0, "scripts")
    import plot_theme

This registers a Plotly template named "group2", built on the team palette
already used in the matplotlib charts, and makes it the default, so every
Plotly figure created afterwards shares the same colors, fonts, and layout.

plot_theme.save(fig, "name") writes a static PNG to figures/, so charts render
reliably on GitHub Pages as Module 3 recommends.
"""

from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

# Team palette, matching scripts/build_market_baseline.py and the skill gap page.
NAVY = "#123B4A"
TEAL = "#2A7F83"
AQUA = "#63B7AF"
LIGHT_BLUE = "#9CCFD0"
GOLD = "#D7A84B"
GRAY = "#65757D"
TEXT = "#25353C"
GRID = "#E6ECEE"
AXIS = "#D9E2E5"

COLORWAY = [TEAL, GOLD, NAVY, AQUA, GRAY, LIGHT_BLUE]
SEQUENTIAL = ["#F3F8F9", LIGHT_BLUE, TEAL, NAVY]      # skill heatmap scale
GAP_SCALE = ["#FFFFFF", "#F2DDB0", GOLD, "#9A6B16"]   # skill gap scale

# Matches the site's Cosmo theme, with common fallbacks.
FONT_FAMILY = "Source Sans Pro, Segoe UI, Helvetica Neue, Arial, sans-serif"

_axis = dict(
    showgrid=True,
    gridcolor=GRID,
    linecolor=AXIS,
    zeroline=False,
    ticks="outside",
    tickcolor=AXIS,
    title=dict(standoff=10),
)

pio.templates["group2"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family=FONT_FAMILY, size=13, color=TEXT),
        title=dict(font=dict(size=18, color=NAVY), x=0, xanchor="left"),
        colorway=COLORWAY,
        colorscale=dict(sequential=SEQUENTIAL),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=60, r=30, t=70, b=50),
        xaxis=_axis,
        yaxis=_axis,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(bgcolor="white", bordercolor=TEAL, font=dict(family=FONT_FAMILY, color=TEXT)),
    )
)
pio.templates.default = "plotly_white+group2"

FIGURES = Path(__file__).resolve().parent.parent / "figures"


def save(fig, name, width=900, height=540, scale=2):
    """Write the figure to figures/<name>.png and return the path."""
    FIGURES.mkdir(exist_ok=True)
    path = FIGURES / f"{name}.png"
    fig.write_image(path, width=width, height=height, scale=scale)
    return path
