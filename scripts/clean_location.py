"""Location cleaning helpers for the analytical panel.

The source LOCATION field is free text with inconsistent structure, and the
structured state fields are incomplete. This module recovers one state label
per posting and marks postings with no identifiable state as Unspecified.

Stages, in order:
    1. Washington DC patterns, checked first so "Washington, District of
       Columbia" and "Pennsylvania Avenue NW, Washington, DC" are not read
       as Washington state or Pennsylvania
    2. A full state name inside LOCATION
    3. A two-letter state code between delimiters in LOCATION
    4. The STATE column
    5. STATE_NAME, when it holds a valid state name or code
    6. A small map of bare city names
Two-letter codes are then normalized to full state names.
"""

from pyspark.sql.functions import col, lit, regexp_extract, trim, upper, when

STATE_NAMES = (
    "Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|"
    "Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|"
    "Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|"
    "Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|"
    "New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|"
    "Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|"
    "Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|"
    "District of Columbia"
)

CODE_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut",
    "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida",
    "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

# Washington DC in its common written forms.
DC_PATTERN = r"(?i)district of columbia|washington,?\s*d\.?\s?c\b"

# Bare city names that appear without a state in LOCATION.
CITY_TO_STATE = {
    "San,? Francisco": "California",
    "Sunnyvale": "California",
    "Santa,? Monica": "California",
    "San Mateo": "California",
    "Austin": "Texas",
    "Chicago": "Illinois",
}


def add_state(dataframe):
    """Return the dataframe with a cleaned `state` column added."""

    out = (
        dataframe
        .withColumn("_by_name", regexp_extract(col("LOCATION"), f"({STATE_NAMES})", 1))
        .withColumn("_by_code", regexp_extract(col("LOCATION"), r",\s*([A-Z]{2})[,;]", 1))
    )

    state_name_valid = (
        col("STATE_NAME").isin(STATE_NAMES.split("|"))
        | upper(trim(col("STATE_NAME"))).isin(list(CODE_TO_NAME))
    )

    raw = (
        when(col("LOCATION").rlike(DC_PATTERN), lit("District of Columbia"))
        .when(trim(col("_by_name")) != "", col("_by_name"))
        .when(trim(col("_by_code")) != "", col("_by_code"))
        .when(trim(col("STATE")) != "", col("STATE"))
        .when(state_name_valid, trim(col("STATE_NAME")))
    )
    for pattern, state in CITY_TO_STATE.items():
        raw = raw.when(col("LOCATION").rlike(f"(?i){pattern}"), state)

    out = out.withColumn("_state_raw", raw.otherwise("Unspecified"))

    # Normalize any two-letter codes to full state names.
    normalized = col("_state_raw")
    for code, name in CODE_TO_NAME.items():
        normalized = when(upper(col("_state_raw")) == code, name).otherwise(normalized)

    out = out.withColumn("state", normalized)
    return out.drop("_by_name", "_by_code", "_state_raw")
