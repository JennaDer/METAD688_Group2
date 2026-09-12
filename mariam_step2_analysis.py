from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import glob

spark = SparkSession.builder.appName("MariamStep2Analysis").getOrCreate()

files = glob.glob("data/MET_CareerCompass_2026/*.parquet")
df = spark.read.parquet(*files)

analytics = df.filter(
    (col("NAICS_2022_4").cast("string") == "3254") &
    col("TITLE_CLEAN").rlike(
        "(?i)analyst|analytics|data|insight|statistic|biostat|financial analysis|business intelligence"
    )
).dropDuplicates()

print("Filtered analytics postings:", analytics.count())

print("\nSTATE COUNTS")
analytics.groupBy("STATE_NAME").count().orderBy(col("count").desc()).show()

print("\nREMOTE WORK COUNTS")
analytics.groupBy("REMOTE_TYPE_NAME").count().orderBy(col("count").desc()).show()

print("\nPOSTINGS")
analytics.select(
    "TITLE_CLEAN",
    "COMPANY_NAME",
    "CITY_NAME",
    "STATE_NAME",
    "LOCATION",
    "REMOTE_TYPE_NAME"
).orderBy("STATE_NAME", "CITY_NAME", "TITLE_CLEAN").show(100, truncate=False)

spark.stop()
