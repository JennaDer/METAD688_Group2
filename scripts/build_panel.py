"""Build the Step 2 analytical panel for NAICS 5415 analytics roles.

Filters the CareerCompass extract to one industry code and one career
pathway, applies the cleaning rules documented in data_preparation.qmd,
and writes a single analytical CSV.
"""

import sys
from pathlib import Path
import glob

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, when, trim

from clean_location import add_state
from clean_salary import add_salary

RAW_GLOB = "data/MET_CareerCompass_2026/*.parquet"
OUT_PATH = "data/processed/career_market_panel.csv"

INDUSTRY_CODE = "5415"
INDUSTRY_LABEL = "Computer Systems Design and Related Services"

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

# ONET categories that are genuine analytics roles in this panel. Everything
# else is a classifier error on a title our filter already validated.
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
    "posted_date",
    "state",
    "LOCATION",
    "REMOTE_TYPE_NAME",
    "MAX_EDULEVELS_NAME",
    "MIN_EDULEVELS_NAME",
    "salary_from_annual",
    "salary_to_annual",
    "salary_midpoint",
    "ORIGINAL_PAY_PERIOD",
    "SKILLS_NAME",
    "SPECIALIZED_SKILLS_NAME",
    "NAICS_2022_4",
    "NAICS_2022_6_NAME",
]

spark = SparkSession.builder.appName("Group2BuildPanel").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

df = spark.read.parquet(*glob.glob(RAW_GLOB))
print("STEP 0 - raw postings:", df.count())

# Step 1: industry filter
industry = df.filter(col("NAICS_2022_4").cast("string") == INDUSTRY_CODE)
print("STEP 1 - after NAICS", INDUSTRY_CODE, "filter:", industry.count())

# Step 2: role-family filter
roles = industry.filter(col("TITLE_CLEAN").rlike(ROLE_INCLUDE))
print("STEP 2a - after role include:", roles.count())

roles = roles.filter(~col("TITLE_CLEAN").rlike(ROLE_EXCLUDE))
print("STEP 2b - after role exclude:", roles.count())

# Step 3: date window (the extract spans one quarter; we keep its range)
panel = roles.withColumn("posted_date", to_date(col("POSTED"), "yyyy-MM-dd"))
panel = panel.filter(col("posted_date").isNotNull())
print("STEP 3 - after valid posted date:", panel.count())

# Step 4: cleaning
panel = add_state(panel)
panel = add_salary(panel)
panel = panel.withColumn(
    "occupation_group",
    when(col("ONET_NAME").isin(ONET_KEEP), col("ONET_NAME")).otherwise("Other"),
)
print("STEP 4 - cleaned columns added")

# Step 5: export
final = panel.select(*KEEP_COLUMNS)
final.coalesce(1).write.mode("overwrite").option("header", True).option(
    "escape", '"'
).csv("data/processed/_panel_tmp")
rows = final.count()

spark.stop()

# Spark writes a directory of part files; move the single part to OUT_PATH.
tmp = Path("data/processed/_panel_tmp")
part = next(tmp.glob("part-*.csv"))
part.replace(Path(OUT_PATH))
for leftover in tmp.iterdir():
    leftover.unlink()
tmp.rmdir()

print("STEP 5 - written to", OUT_PATH)
print("FINAL ROWS:", rows)
