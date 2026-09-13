"""Build the Step 2 analytical panel for NAICS 5415 analytics roles."""

import glob
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, min as smin, max as smax

RAW_GLOB = "data/MET_CareerCompass_2026/*.parquet"
INDUSTRY_CODE = "5415"

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

# Step 3: date window
# The dataset itself spans a single quarter, so we keep its natural range
# and record it rather than imposing a narrower window.
panel = roles.withColumn("posted_date", to_date(col("POSTED"), "yyyy-MM-dd"))
panel = panel.filter(col("posted_date").isNotNull())
print("STEP 3 - after valid posted date:", panel.count())

panel.select(
    smin("posted_date").alias("window_start"),
    smax("posted_date").alias("window_end"),
).show()

spark.stop()
