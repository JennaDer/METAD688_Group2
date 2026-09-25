"""Salary cleaning helpers for the Step 2 panel.

SALARY_FROM and SALARY_TO are stored as strings and are blank on most rows.
Some rows carry 0.00 where the source held a structured MonetaryAmount object
the provider could not flatten. Postings quote pay by the hour, day, week,
month, or year, so every figure is converted to an annual equivalent before
analysis. Figures below a plausible annual floor are treated as missing.
"""

from pyspark.sql.functions import col, trim, when, lower, lit

# Annual multipliers, assuming full-time work.
PERIOD_TO_ANNUAL = {
    "hourly": 2080,   # 40 hours x 52 weeks
    "daily": 260,     # 5 days x 52 weeks
    "weekly": 52,
    "monthly": 12,
    "annual": 1,
}

MIN_PLAUSIBLE_ANNUAL = 20000


def add_salary(dataframe):
    """Return the dataframe with cleaned annual salary columns added."""

    out = (
        dataframe
        .withColumn("_from", when(trim(col("SALARY_FROM").cast("string")) != "", col("SALARY_FROM").cast("double")))
        .withColumn("_to", when(trim(col("SALARY_TO").cast("string")) != "", col("SALARY_TO").cast("double")))
    )

    # A missing pay period is treated as annual, the most common case.
    period = lower(trim(col("ORIGINAL_PAY_PERIOD")))
    multiplier = lit(1.0)
    for name, factor in PERIOD_TO_ANNUAL.items():
        multiplier = when(period == name, lit(float(factor))).otherwise(multiplier)

    out = (
        out
        .withColumn("salary_from_annual", col("_from") * multiplier)
        .withColumn("salary_to_annual", col("_to") * multiplier)
    )

    # Drop placeholder zeros and implausibly low figures.
    valid = col("salary_from_annual").isNotNull() & (col("salary_from_annual") >= MIN_PLAUSIBLE_ANNUAL)
    out = (
        out
        .withColumn("salary_from_annual", when(valid, col("salary_from_annual")))
        .withColumn("salary_to_annual", when(valid, col("salary_to_annual")))
    )

    # Midpoint of the advertised range, falling back to the lower bound.
    out = out.withColumn(
        "salary_midpoint",
        when(
            col("salary_from_annual").isNotNull() & col("salary_to_annual").isNotNull(),
            (col("salary_from_annual") + col("salary_to_annual")) / 2,
        ).otherwise(col("salary_from_annual")),
    )

    return out.drop("_from", "_to")
