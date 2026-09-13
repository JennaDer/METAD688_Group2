"""Salary cleaning helpers for the Step 2 panel.

SALARY_FROM and SALARY_TO are stored as strings and are blank on most rows.
A small number carry 0.00 where the source held a structured MonetaryAmount
object the provider could not flatten, and one row carries an implausible
annual figure. Hourly postings are converted to an annual equivalent so the
salary distribution can be read on a single scale.
"""

from pyspark.sql.functions import col, trim, when

HOURS_PER_YEAR = 2080
MIN_PLAUSIBLE_ANNUAL = 20000


def add_salary(dataframe):
    """Return the dataframe with cleaned annual salary columns added."""

    out = (
        dataframe
        .withColumn(
            "_from",
            when(trim(col("SALARY_FROM")) != "", col("SALARY_FROM").cast("double")),
        )
        .withColumn(
            "_to",
            when(trim(col("SALARY_TO")) != "", col("SALARY_TO").cast("double")),
        )
    )

    # Convert hourly postings to an annual equivalent.
    out = (
        out
        .withColumn(
            "salary_from_annual",
            when(col("ORIGINAL_PAY_PERIOD") == "hourly", col("_from") * HOURS_PER_YEAR)
            .otherwise(col("_from")),
        )
        .withColumn(
            "salary_to_annual",
            when(col("ORIGINAL_PAY_PERIOD") == "hourly", col("_to") * HOURS_PER_YEAR)
            .otherwise(col("_to")),
        )
    )

    # Drop placeholder zeros and implausible figures.
    valid = (
        col("salary_from_annual").isNotNull()
        & (col("salary_from_annual") >= MIN_PLAUSIBLE_ANNUAL)
    )

    out = (
        out
        .withColumn(
            "salary_from_annual", when(valid, col("salary_from_annual"))
        )
        .withColumn(
            "salary_to_annual", when(valid, col("salary_to_annual"))
        )
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
