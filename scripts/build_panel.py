"""Build the analytical panel for NAICS 5415 analytics roles.

Reads the MET CareerCompass 2026 v2 extract, filters it to one industry code
and one career pathway, keeps the 12 months ending at the latest posting,
applies the cleaning rules documented in data_cleaning.qmd, and writes:

    data/processed/career_market_panel.csv   the analytical panel
    data/processed/panel_build_stats.json    counts recorded during the build
"""

import glob
import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, lower, to_date, trim, when

from clean_location import add_state
from clean_salary import add_salary

RAW_GLOB = "data/MET_CareerCompass_2026_v2/*.parquet"
OUT_PATH = "data/processed/career_market_panel.csv"
STATS_PATH = "data/processed/panel_build_stats.json"
TMP_DIR = "data/processed/_panel_tmp"

INDUSTRY_CODE = "5415"
INDUSTRY_LABEL = "Computer Systems Design and Related Services"
WINDOW_DAYS = 365

# Role family: titles that name an analytics role directly.
ROLE_INCLUDE = (
    "(?i)data analyst|data scien|business intelligence|bi analyst|"
    "data engineer|analytics engineer|business analyst|reporting analyst"
)

# Adjacent roles that share the word "analyst" but sit outside the pathway.
ROLE_EXCLUDE = (
    "(?i)security|qa |quality assurance|support|trade|"
    "exploitation|acceptance testing|network"
)

# The naive filter we rejected, recorded for comparison on the page.
BROAD_ANALYST = "(?i)analyst|analytics|data scien|business intelligence|data engineer"

# ONET categories that describe analytics roles. Everything else is grouped
# as Other; role_family, taken from the title, is the preferred grouping.
ONET_KEEP = [
    "Data Scientists",
    "Database Architects",
    "Management Analysts",
    "Business Intelligence Analysts",
]

KEEP_COLUMNS = [
    "ID",
    "TITLE_CLEAN",
    "COMPANY_NAME",
    "COMPANY_IS_STAFFING",
    "occupation_group",
    "role_family",
    "posted_date",
    "state",
    "LOCATION",
    "REMOTE_TYPE_NAME",
    "MAX_EDULEVELS_NAME",
    "MIN_EDULEVELS_NAME",
    "min_years_experience",
    "max_years_experience",
    "salary_from_annual",
    "salary_to_annual",
    "salary_midpoint",
    "ORIGINAL_PAY_PERIOD",
    "SKILLS_NAME",
    "SPECIALIZED_SKILLS_NAME",
    "NAICS_2022_4",
    "NAICS_2022_6_NAME",
]

spark = (
    SparkSession.builder.appName("Group2BuildPanel")
    .config("spark.ui.showConsoleProgress", "false")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

stats = {
    "source": "MET_CareerCompass_2026_v2",
    "industry_code": INDUSTRY_CODE,
    "industry_label": INDUSTRY_LABEL,
}

files = sorted(glob.glob(RAW_GLOB))
df = spark.read.parquet(*files)
stats["source_files"] = len(files)
stats["source_columns"] = len(df.columns)
stats["raw_postings"] = df.count()
print("STEP 0 - raw postings:", stats["raw_postings"])

# Step 1: industry filter
industry = df.filter(col("NAICS_2022_4").cast("string") == INDUSTRY_CODE)
stats["industry_postings"] = industry.count()
stats["broad_analyst_matches"] = industry.filter(col("TITLE_CLEAN").rlike(BROAD_ANALYST)).count()
print("STEP 1 - after NAICS", INDUSTRY_CODE, "filter:", stats["industry_postings"])

# Step 2: role-family filter
roles = industry.filter(col("TITLE_CLEAN").rlike(ROLE_INCLUDE))
stats["after_role_include"] = roles.count()
roles = roles.filter(~col("TITLE_CLEAN").rlike(ROLE_EXCLUDE))
stats["after_role_exclude"] = roles.count()
print("STEP 2 - after role filter:", stats["after_role_include"], "->", stats["after_role_exclude"])

# Step 3: date window. v2 spans 2014 to 2026, so we keep the 12 months ending
# at the latest posting. Postings without a date cannot be placed in the window.
panel = roles.withColumn("posted_date", to_date(col("POSTED"), "yyyy-MM-dd"))
stats["undated"] = panel.filter(col("posted_date").isNull()).count()
latest = panel.agg({"posted_date": "max"}).collect()[0][0]
window_start = latest - timedelta(days=WINDOW_DAYS)
panel = panel.filter(col("posted_date") >= lit(window_start))
stats["window_start"] = str(window_start)
stats["window_end"] = str(latest)
stats["after_window"] = panel.count()
stats["before_window"] = stats["after_role_exclude"] - stats["undated"] - stats["after_window"]
print("STEP 3 - window", window_start, "to", latest, "->", stats["after_window"])

# Raw-field facts that the cleaned panel no longer shows.
def filled(name):
    return panel.filter(trim(col(name).cast("string")) != "").count()

def has_items(name):
    return panel.filter((trim(col(name)) != "") & (trim(col(name)) != "[]")).count()

stats["field_coverage"] = {
    name: filled(name)
    for name in ["STATE_NAME", "STATE", "COUNTY_NAME", "MSA_NAME", "SALARY_FROM", "MIN_YEARS_EXPERIENCE"]
}
stats["skill_field_coverage"] = {
    name: has_items(name)
    for name in ["SKILLS_NAME", "SPECIALIZED_SKILLS_NAME", "COMMON_SKILLS_NAME", "SOFTWARE_SKILLS_NAME"]
}
raw_years = when(trim(col("MIN_YEARS_EXPERIENCE")) != "", col("MIN_YEARS_EXPERIENCE").cast("double"))
stats["experience_zero"] = panel.filter(raw_years == 0).count()
stats["experience_over_20"] = panel.filter(raw_years > 20).count()

# Step 4: cleaning
panel = add_state(panel)
panel = add_salary(panel)
panel = panel.withColumn(
    "occupation_group",
    when(col("ONET_NAME").isin(ONET_KEEP), col("ONET_NAME")).otherwise("Other"),
)

# Work arrangement: v2 spells on-site two ways and leaves many rows blank.
panel = panel.withColumn(
    "REMOTE_TYPE_NAME",
    when(col("REMOTE_TYPE_NAME").isNull() | (trim(col("REMOTE_TYPE_NAME")) == ""), "Unknown")
    .when(lower(col("REMOTE_TYPE_NAME")).isin("onsite", "on-site"), "On-site")
    .otherwise(col("REMOTE_TYPE_NAME")),
)

# Role family from the job title, which is what the role filter selects on.
title = lower(col("TITLE_CLEAN"))
panel = panel.withColumn(
    "role_family",
    when(title.rlike("data scien"), "Data Scientist")
    .when(title.rlike("data engineer|analytics engineer"), "Data Engineer")
    .when(title.rlike("business intelligence|bi analyst"), "Business Intelligence")
    .when(title.rlike("data analyst|reporting analyst"), "Data Analyst")
    .when(title.rlike("business analyst"), "Business Analyst")
    .otherwise("Other"),
)

# Experience: 0 appears on many senior titles, so it is read as "not stated"
# rather than "no experience required". Values above 20 years are implausible.
for raw, clean in [("MIN_YEARS_EXPERIENCE", "min_years_experience"),
                   ("MAX_YEARS_EXPERIENCE", "max_years_experience")]:
    years = when(trim(col(raw)) != "", col(raw).cast("double"))
    panel = panel.withColumn(clean, when((years >= 1) & (years <= 20), years))
print("STEP 4 - cleaned columns added")

# Step 5: export, sorted by ID so rebuilds produce stable output.
final = panel.select(*KEEP_COLUMNS)
stats["final_postings"] = final.count()
(
    final.coalesce(1)
    .sortWithinPartitions("ID")
    .write.mode("overwrite")
    .option("header", True)
    .option("escape", '"')
    .csv(TMP_DIR)
)
spark.stop()

# Spark writes a folder of part files; keep the single part as OUT_PATH.
tmp = Path(TMP_DIR)
next(tmp.glob("part-*.csv")).replace(Path(OUT_PATH))
for leftover in tmp.iterdir():
    leftover.unlink()
tmp.rmdir()

Path(STATS_PATH).write_text(json.dumps(stats, indent=2) + "\n")
print("STEP 5 - wrote", OUT_PATH, "and", STATS_PATH)
print("FINAL ROWS:", stats["final_postings"])
