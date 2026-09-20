"""Generate Module 2 market-baseline figures and data dictionary."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "career_market_panel.csv"
FIGURE_DIR = ROOT / "figures"
DICTIONARY_PATH = (
    ROOT / "data" / "processed" / "career_market_data_dictionary.csv"
)

FIGURE_DIR.mkdir(parents=True, exist_ok=True)

NAVY = "#123B4A"
TEAL = "#2A7F83"
AQUA = "#63B7AF"
LIGHT_BLUE = "#9CCFD0"
GOLD = "#D7A84B"
GRAY = "#65757D"

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#D9E2E5",
        "axes.titlecolor": NAVY,
        "axes.labelcolor": "#25353C",
        "font.size": 10,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
    }
)


def save_figure(filename):
    """Apply consistent formatting and save the active figure."""
    plt.tight_layout()
    plt.savefig(
        FIGURE_DIR / filename,
        dpi=180,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close()


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

plt.figure(figsize=(9, 5.5))
bars = plt.barh(role_counts.index, role_counts.values, color=TEAL)

for bar, value in zip(bars, role_counts.values):
    plt.text(
        value + 2,
        bar.get_y() + bar.get_height() / 2,
        f"{value} ({value / total_postings:.1%})",
        va="center",
        color=NAVY,
    )

plt.title("Analytics Postings by Occupation Segment", loc="left")
plt.xlabel("Number of postings")
plt.ylabel("")
plt.xlim(0, role_counts.max() * 1.22)
plt.grid(axis="x", alpha=0.2)
save_figure("job_volume_by_segment.png")

# ------------------------------------------------------------
# 2. Salary distribution
# ------------------------------------------------------------

salary = panel["salary_midpoint"].dropna()
salary_median = salary.median()

plt.figure(figsize=(9, 5.5))
plt.hist(
    salary,
    bins=14,
    color=TEAL,
    edgecolor="white",
)
plt.axvline(
    salary_median,
    color=GOLD,
    linewidth=2.5,
    linestyle="--",
    label=f"Median: ${salary_median:,.0f}",
)

plt.title("Distribution of Advertised Annual Salary Midpoints", loc="left")
plt.xlabel("Annual salary midpoint (USD)")
plt.ylabel("Number of postings")
plt.gca().xaxis.set_major_formatter(
    plt.FuncFormatter(lambda value, _: f"${value / 1000:.0f}K")
)
plt.grid(axis="y", alpha=0.2)
plt.legend(frameon=False)
save_figure("salary_distribution.png")

# ------------------------------------------------------------
# 3. Leading states
# ------------------------------------------------------------

state_counts = (
    panel.loc[panel["state"] != "Unspecified", "state"]
    .value_counts()
    .head(10)
    .sort_values()
)

plt.figure(figsize=(9, 6))
bars = plt.barh(state_counts.index, state_counts.values, color=AQUA)

for bar, value in zip(bars, state_counts.values):
    plt.text(
        value + 0.5,
        bar.get_y() + bar.get_height() / 2,
        str(value),
        va="center",
        color=NAVY,
    )

plt.title("Leading Identified States for Analytics Postings", loc="left")
plt.xlabel("Number of postings")
plt.ylabel("")
plt.xlim(0, state_counts.max() * 1.15)
plt.grid(axis="x", alpha=0.2)
save_figure("leading_states.png")

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

plt.figure(figsize=(8.5, 5.5))
bars = plt.bar(
    work_counts.index,
    work_counts.values,
    color=[TEAL, AQUA, LIGHT_BLUE, GRAY],
)

for bar, value in zip(bars, work_counts.values):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        value + 3,
        f"{value}\n({value / total_postings:.1%})",
        ha="center",
        color=NAVY,
    )

plt.title("Remote, Hybrid, and On-site Classification", loc="left")
plt.xlabel("")
plt.ylabel("Number of postings")
plt.ylim(0, work_counts.max() * 1.18)
plt.grid(axis="y", alpha=0.2)
save_figure("work_arrangement.png")

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

plt.figure(figsize=(9, 6))
bars = plt.barh(employer_counts.index, employer_counts.values, color=TEAL)

for bar, value in zip(bars, employer_counts.values):
    plt.text(
        value + 0.2,
        bar.get_y() + bar.get_height() / 2,
        str(value),
        va="center",
        color=NAVY,
    )

plt.title("Employers with the Most Postings in the Panel", loc="left")
plt.xlabel("Number of postings")
plt.ylabel("")
plt.xlim(0, employer_counts.max() * 1.15)
plt.grid(axis="x", alpha=0.2)
save_figure("top_employers.png")

# ------------------------------------------------------------
# 6. Median salary by occupation segment
# ------------------------------------------------------------

salary_by_role = (
    panel.groupby("occupation_group")["salary_midpoint"]
    .agg(["count", "median"])
    .query("count >= 10")
    .sort_values("median")
)

salary_role_labels = {
    "Management Analysts": "Management analysts",
    "Database Architects": "Database architects / data engineers",
    "Data Scientists": "Data scientists / data analysts",
}
salary_by_role.index = [
    salary_role_labels.get(value, value)
    for value in salary_by_role.index
]

plt.figure(figsize=(9, 5.5))
bars = plt.barh(
    salary_by_role.index,
    salary_by_role["median"],
    color=TEAL,
)

for bar, value, count in zip(
    bars,
    salary_by_role["median"],
    salary_by_role["count"],
):
    plt.text(
        value + 2500,
        bar.get_y() + bar.get_height() / 2,
        f"${value:,.0f} (n={int(count)})",
        va="center",
        color=NAVY,
    )

plt.title("Median Advertised Salary by Occupation Segment", loc="left")
plt.xlabel("Median annual salary midpoint (USD)")
plt.ylabel("")
plt.xlim(0, salary_by_role["median"].max() * 1.30)
plt.gca().xaxis.set_major_formatter(
    plt.FuncFormatter(lambda value, _: f"${value / 1000:.0f}K")
)
plt.grid(axis="x", alpha=0.2)
save_figure("median_salary_by_occupation.png")

# ------------------------------------------------------------
# Data dictionary
# ------------------------------------------------------------

dictionary_rows = [
    ["ID", "Integer", "Unique posting identifier", "Source field; used to assess duplicate records"],
    ["TITLE_CLEAN", "Text", "Cleaned job title", "Used for the analytics-career keyword filter"],
    ["COMPANY_NAME", "Text", "Employer name", "Retained as supplied; labels are not fully standardized"],
    ["COMPANY_IS_STAFFING", "Boolean", "Staffing-company indicator", "Retained from the source extract"],
    ["occupation_group", "Text", "Grouped O*NET occupation", "Valid analytics categories retained; other matched roles grouped as Other"],
    ["posted_date", "Date", "Job-posting date", "Converted to a valid calendar date"],
    ["state", "Text", "Derived U.S. state", "Recovered from available location fields; unresolved values marked Unspecified"],
    ["LOCATION", "Text", "Original location text", "Retained for traceability"],
    ["REMOTE_TYPE_NAME", "Text", "Remote-work classification", "Reported as Remote, Hybrid, On-site, or Unknown"],
    ["MAX_EDULEVELS_NAME", "Text", "Highest education level recorded", "Used as the available qualification measure"],
    ["MIN_EDULEVELS_NAME", "Text", "Minimum education value", "Retained but not used as the primary education measure"],
    ["salary_from_annual", "Decimal", "Annualized lower salary", "Hourly values annualized; zero and implausible values removed"],
    ["salary_to_annual", "Decimal", "Annualized upper salary", "Hourly values annualized; zero and implausible values removed"],
    ["salary_midpoint", "Decimal", "Midpoint of advertised salary range", "Calculated from valid annualized salary bounds"],
    ["ORIGINAL_PAY_PERIOD", "Text", "Original salary pay period", "Retained to document salary conversion"],
    ["SKILLS_NAME", "Text array", "Skills associated with the posting", "Retained with documented source truncation"],
    ["SPECIALIZED_SKILLS_NAME", "Text array", "Specialized skills associated with the posting", "Retained with documented source truncation"],
    ["NAICS_2022_4", "Text", "Four-digit NAICS code", "Filtered to 5415"],
    ["NAICS_2022_6_NAME", "Text", "Industry label", "Used because the four-digit industry-name field is blank"],
]

dictionary = pd.DataFrame(
    dictionary_rows,
    columns=["variable", "data_type", "description", "cleaning_or_use"],
)
dictionary.to_csv(DICTIONARY_PATH, index=False)

print(f"Loaded {total_postings} postings.")
print(f"Created six figures in: {FIGURE_DIR}")
print(f"Created data dictionary: {DICTIONARY_PATH}")
print(f"Postings with usable salary: {len(salary)}")
print(f"Median salary midpoint: ${salary_median:,.2f}")