"""Generate the EDA figures and the data dictionary.

Charts are built with Plotly and the shared "group2" theme in
scripts/plot_theme.py, then saved as static PNGs in figures/ so the
site renders reliably on GitHub Pages.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plot_theme  # noqa: E402  registers and activates the group2 template
from plot_theme import NAVY, TEAL, AQUA, LIGHT_BLUE, GOLD, GRAY  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "career_market_panel.csv"
FIGURE_DIR = ROOT / "figures"
DICTIONARY_PATH = (
    ROOT / "data" / "processed" / "career_market_data_dictionary.csv"
)

FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def hbar(labels, values, text, color, title, x_title, x_max, height=540):
    """Horizontal bar chart in the group2 theme."""
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=color,
            text=text,
            textposition="outside",
            textfont=dict(color=NAVY),
            cliponaxis=False,
            hovertemplate="%{y}: %{x:,}<extra></extra>",
        )
    )
    fig.update_layout(title=title, height=height, showlegend=False)
    fig.update_xaxes(title=x_title, range=[0, x_max])
    fig.update_yaxes(showgrid=False, ticks="")
    return fig


panel = pd.read_csv(DATA_PATH)
total_postings = len(panel)

# ------------------------------------------------------------
# 1. Job volume by occupation segment
# ------------------------------------------------------------

role_counts = (
    panel["occupation_group"]
    .fillna("Other")
    .value_counts()
    .sort_values()
)

role_labels = {
    "Other": "Other matched analytics roles",
    "Business Intelligence Analysts": "Business intelligence analysts",
    "Management Analysts": "Management analysts",
    "Database Architects": "Database architects / data engineers",
    "Data Scientists": "Data scientists / data analysts",
}
role_counts.index = [role_labels.get(value, value) for value in role_counts.index]

fig = hbar(
    role_counts.index,
    role_counts.values,
    [f"{v} ({v / total_postings:.1%})" for v in role_counts.values],
    TEAL,
    "Analytics Postings by Occupation Segment",
    "Number of postings",
    role_counts.max() * 1.25,
)
plot_theme.save(fig, "job_volume_by_segment")

# ------------------------------------------------------------
# 2. Salary distribution
# ------------------------------------------------------------

salary = panel["salary_midpoint"].dropna()
salary_median = salary.median()

fig = go.Figure(
    go.Histogram(
        x=salary,
        nbinsx=14,
        marker=dict(color=TEAL, line=dict(color="white", width=1)),
        hovertemplate="%{x}<br>%{y} postings<extra></extra>",
        showlegend=False,
    )
)
fig.add_vline(
    x=salary_median,
    line=dict(color=GOLD, width=3, dash="dash"),
    annotation_text=f"Median: ${salary_median:,.0f}",
    annotation_position="top right",
    annotation_font=dict(color=NAVY),
)
fig.update_layout(
    title="Distribution of Advertised Annual Salary Midpoints",
    bargap=0.03,
)
fig.update_xaxes(title="Annual salary midpoint (USD)", tickprefix="$", tickformat="~s")
fig.update_yaxes(title="Number of postings")
plot_theme.save(fig, "salary_distribution")

# ------------------------------------------------------------
# 3. Leading states
# ------------------------------------------------------------

state_counts = (
    panel.loc[panel["state"] != "Unspecified", "state"]
    .value_counts()
    .head(10)
    .sort_values()
)

fig = hbar(
    state_counts.index,
    state_counts.values,
    [str(v) for v in state_counts.values],
    AQUA,
    "Leading Identified States for Analytics Postings",
    "Number of postings",
    state_counts.max() * 1.15,
    height=600,
)
plot_theme.save(fig, "leading_states", height=600)

# ------------------------------------------------------------
# 4. Work arrangement
# ------------------------------------------------------------

work_order = ["Remote", "Hybrid", "On-site", "Unknown"]
work_counts = (
    panel["REMOTE_TYPE_NAME"]
    .fillna("Unknown")
    .value_counts()
    .reindex(work_order, fill_value=0)
)

fig = go.Figure(
    go.Bar(
        x=work_counts.index,
        y=work_counts.values,
        marker_color=[TEAL, AQUA, LIGHT_BLUE, GRAY],
        text=[f"{v}<br>({v / total_postings:.1%})" for v in work_counts.values],
        textposition="outside",
        textfont=dict(color=NAVY),
        cliponaxis=False,
        hovertemplate="%{x}: %{y:,}<extra></extra>",
    )
)
fig.update_layout(title="Remote, Hybrid, and On-site Classification", showlegend=False)
fig.update_xaxes(showgrid=False)
fig.update_yaxes(title="Number of postings", range=[0, work_counts.max() * 1.2])
plot_theme.save(fig, "work_arrangement")

# ------------------------------------------------------------
# 5. Top employers
# ------------------------------------------------------------

employer_counts = (
    panel["COMPANY_NAME"]
    .fillna("Unknown employer")
    .value_counts()
    .head(10)
    .sort_values()
)

fig = hbar(
    employer_counts.index,
    employer_counts.values,
    [str(v) for v in employer_counts.values],
    TEAL,
    "Employers with the Most Postings in the Panel",
    "Number of postings",
    employer_counts.max() * 1.15,
    height=600,
)
plot_theme.save(fig, "top_employers", height=600)

# ------------------------------------------------------------
# 6. Median salary by occupation segment
# ------------------------------------------------------------

salary_by_role = (
    panel.groupby("occupation_group")["salary_midpoint"]
    .agg(["count", "median"])
    .query("count >= 10")
    .sort_values("median")
)

salary_by_role.index = [
    role_labels.get(value, value) for value in salary_by_role.index
]

fig = hbar(
    salary_by_role.index,
    salary_by_role["median"],
    [f"${m:,.0f} (n={int(c)})" for m, c in zip(salary_by_role["median"], salary_by_role["count"])],
    TEAL,
    "Median Advertised Salary by Occupation Segment",
    "Median annual salary midpoint (USD)",
    salary_by_role["median"].max() * 1.35,
)
fig.update_xaxes(tickprefix="$", tickformat="~s")
fig.update_traces(hovertemplate="%{y}: $%{x:,.0f}<extra></extra>")
plot_theme.save(fig, "median_salary_by_occupation")

# ------------------------------------------------------------
# 7. Minimum experience requirement
# ------------------------------------------------------------

experience_bands = [
    "1-2 years",
    "3-4 years",
    "5-7 years",
    "8-10 years",
    "More than 10",
]
experience = panel["min_years_experience"].dropna()
experience_counts = (
    pd.cut(
        experience,
        bins=[0, 2, 4, 7, 10, 100],
        labels=experience_bands,
        right=True,
    )
    .value_counts()
    .reindex(experience_bands, fill_value=0)
)

fig = go.Figure(
    go.Bar(
        x=[str(label) for label in experience_counts.index],
        y=experience_counts.values,
        marker_color=[LIGHT_BLUE, AQUA, TEAL, NAVY, GRAY],
        text=[
            f"{v}<br>({v / len(experience):.1%})" for v in experience_counts.values
        ],
        textposition="outside",
        textfont=dict(color=NAVY),
        cliponaxis=False,
        hovertemplate="%{x}: %{y:,}<extra></extra>",
    )
)
fig.update_layout(
    title="Minimum Years of Experience Requested", showlegend=False
)
fig.update_xaxes(showgrid=False, title="Minimum experience requested")
fig.update_yaxes(
    title="Number of postings", range=[0, experience_counts.max() * 1.2]
)
plot_theme.save(fig, "experience_distribution")

# ------------------------------------------------------------
# Data dictionary
# ------------------------------------------------------------

dictionary_rows = [
    ["ID", "Integer", "Unique posting identifier", "Source field; used to assess duplicate records"],
    ["TITLE_CLEAN", "Text", "Cleaned job title", "Used for the analytics-career keyword filter"],
    ["COMPANY_NAME", "Text", "Employer name", "Retained as supplied; labels are not fully standardized"],
    ["COMPANY_IS_STAFFING", "Boolean", "Staffing-company indicator", "Retained from the source extract"],
    ["occupation_group", "Text", "Grouped O*NET occupation", "Valid analytics categories retained; other matched roles grouped as Other"],
    ["role_family", "Text", "Role family derived from the job title", "Assigned from the title keywords used in the role filter"],
    ["posted_date", "Date", "Job-posting date", "Converted to a valid calendar date"],
    ["state", "Text", "Derived U.S. state", "Recovered from available location fields; unresolved values marked Unspecified"],
    ["LOCATION", "Text", "Original location text", "Retained for traceability"],
    ["REMOTE_TYPE_NAME", "Text", "Remote-work classification", "Reported as Remote, Hybrid, On-site, or Unknown"],
    ["MAX_EDULEVELS_NAME", "Text", "Highest education level recorded", "Used as the available qualification measure"],
    ["MIN_EDULEVELS_NAME", "Text", "Minimum education value", "Retained but not used as the primary education measure"],
    ["min_years_experience", "Decimal", "Minimum years of experience requested", "Kept only for values from 1 to 20 years; others set to missing"],
    ["max_years_experience", "Decimal", "Maximum years of experience requested", "Kept only for values from 1 to 20 years; others set to missing"],
    ["salary_from_annual", "Decimal", "Annualized lower salary", "Hourly values annualized; zero and implausible values removed"],
    ["salary_to_annual", "Decimal", "Annualized upper salary", "Hourly values annualized; zero and implausible values removed"],
    ["salary_midpoint", "Decimal", "Midpoint of advertised salary range", "Calculated from valid annualized salary bounds"],
    ["ORIGINAL_PAY_PERIOD", "Text", "Original salary pay period", "Retained to document salary conversion"],
    ["SKILLS_NAME", "Text array", "Skills associated with the posting", "Full skill list from the v2 extract"],
    ["SPECIALIZED_SKILLS_NAME", "Text array", "Specialized skills associated with the posting", "Full skill list from the v2 extract"],
    ["NAICS_2022_4", "Text", "Four-digit NAICS code", "Filtered to 5415"],
    ["NAICS_2022_6_NAME", "Text", "Industry label", "Used because the four-digit industry-name field is blank"],
]

dictionary = pd.DataFrame(
    dictionary_rows,
    columns=["variable", "data_type", "description", "cleaning_or_use"],
)
dictionary.to_csv(DICTIONARY_PATH, index=False)

print(f"Loaded {total_postings} postings.")
print(f"Created seven figures in: {FIGURE_DIR}")
print(f"Created data dictionary: {DICTIONARY_PATH}")
print(f"Postings with usable salary: {len(salary)}")
print(f"Median salary midpoint: ${salary_median:,.2f}")