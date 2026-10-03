"""Fit and evaluate the Step 4 salary-classification models.

Target: whether a posting's advertised salary midpoint falls above the
median of the postings that report usable pay. Features come from the
role family, work arrangement, state, education level, and the skills
listed on the posting.

Models are selected by cross-validation on the training split, and the
held-out test split is scored exactly once, at the end. Metrics and
coefficients are written to data/processed/ so ml_methods.qmd reads
results instead of refitting, and figures go to figures/ as static PNGs
so the site renders reliably on GitHub Pages.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plot_theme  # noqa: E402  registers and activates the group2 template
from plot_theme import NAVY, TEAL, GOLD, GRAY  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "career_market_panel.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
METRICS_PATH = PROCESSED_DIR / "model_metrics.csv"
COEFFICIENTS_PATH = PROCESSED_DIR / "model_coefficients.csv"

SKILL_THRESHOLD = 0.05   # keep skills listed on at least 5% of the subset
TOP_STATES = 6           # name this many states, collapse the rest
TEST_SIZE = 0.25
SEED = 688               # fixed so the reported numbers reproduce

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def parse_skills(value):
    """Turn a SKILLS_NAME cell into a set of skill names."""
    if not isinstance(value, str) or not value.startswith("["):
        return set()
    return set(json.loads(value))


# ------------------------------------------------------------
# 1. Analytical sample and target
# ------------------------------------------------------------

panel = pd.read_csv(DATA_PATH)
sample = panel[panel["salary_midpoint"].notna()].copy()

median_salary = sample["salary_midpoint"].median()
sample["high_salary"] = (sample["salary_midpoint"] > median_salary).astype(int)

# ------------------------------------------------------------
# 2. Feature matrix
#
# Excluded on coverage grounds: min_years_experience is present on only
# 154 of these postings, and COMPANY_IS_STAFFING has 13 positives, so
# neither carries enough signal to justify the rows or columns it costs.
# occupation_group is excluded because it is title-derived like
# role_family and the two would be collinear.
# ------------------------------------------------------------

skills = sample["SKILLS_NAME"].map(parse_skills)
skill_counts = pd.Series(
    [skill for row in skills for skill in row]
).value_counts()
kept_skills = sorted(
    skill_counts[skill_counts >= SKILL_THRESHOLD * len(sample)].index
)

top_states = (
    sample.loc[sample["state"] != "Unspecified", "state"]
    .value_counts()
    .head(TOP_STATES)
    .index
)
state_grouped = sample["state"].where(
    sample["state"].isin(top_states) | (sample["state"] == "Unspecified"),
    "Other state",
)

categorical = pd.DataFrame(
    {
        "role": sample["role_family"],
        "remote": sample["REMOTE_TYPE_NAME"],
        "state": state_grouped,
        "education": sample["MAX_EDULEVELS_NAME"].fillna("Not specified"),
    }
)

features = pd.get_dummies(categorical, prefix_sep=": ", dtype=float)
for skill in kept_skills:
    features[f"skill: {skill}"] = skills.map(lambda row: float(skill in row))

X = features
y = sample["high_salary"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, stratify=y, random_state=SEED
)

# Role-only matrix, to test whether anything beyond the job title helps.
role_columns = [c for c in X.columns if c.startswith("role: ")]

# ------------------------------------------------------------
# 3. Models
# ------------------------------------------------------------

logistic = make_pipeline(
    StandardScaler(),
    LogisticRegression(C=1.0, max_iter=2000, random_state=SEED),
)
forest = RandomForestClassifier(
    n_estimators=500, min_samples_leaf=3, random_state=SEED, n_jobs=-1
)

specifications = [
    ("Majority-class baseline", DummyClassifier(strategy="most_frequent"), list(X.columns)),
    ("Logistic, role family only", make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, random_state=SEED)), role_columns),
    ("Logistic, all features", logistic, list(X.columns)),
    ("Random forest, all features", forest, list(X.columns)),
]

folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
rows = []

for name, estimator, columns in specifications:
    cv_scores = cross_val_score(
        estimator, X_train[columns], y_train, cv=folds, scoring="accuracy"
    )
    estimator.fit(X_train[columns], y_train)
    predicted = estimator.predict(X_test[columns])
    rows.append(
        {
            "model": name,
            "features": len(columns),
            "cv_accuracy_mean": round(cv_scores.mean(), 4),
            "cv_accuracy_sd": round(cv_scores.std(), 4),
            "test_accuracy": round(accuracy_score(y_test, predicted), 4),
            "test_precision": round(precision_score(y_test, predicted, zero_division=0), 4),
            "test_recall": round(recall_score(y_test, predicted, zero_division=0), 4),
            "test_f1": round(f1_score(y_test, predicted, zero_division=0), 4),
        }
    )

metrics = pd.DataFrame(rows)
metrics.to_csv(METRICS_PATH, index=False)

# ------------------------------------------------------------
# 4. Coefficients and importances
# ------------------------------------------------------------

coefficients = pd.DataFrame(
    {
        "feature": X.columns,
        "logistic_coefficient": logistic.named_steps["logisticregression"].coef_[0],
        "forest_importance": forest.feature_importances_,
    }
)
coefficients["absolute_coefficient"] = coefficients["logistic_coefficient"].abs()
coefficients = coefficients.sort_values("absolute_coefficient", ascending=False)
coefficients.to_csv(COEFFICIENTS_PATH, index=False)

# ------------------------------------------------------------
# 5. Confusion matrix for the logistic model
# ------------------------------------------------------------

predicted_logistic = logistic.predict(X_test)
matrix = confusion_matrix(y_test, predicted_logistic)
labels = ["At or below median", "Above median"]

heatmap = go.Figure(
    go.Heatmap(
        z=matrix,
        x=labels,
        y=labels,
        colorscale=[[0, "#F3F8F9"], [1, NAVY]],
        showscale=False,
        hovertemplate="Actual %{y}, predicted %{x}: %{z}<extra></extra>",
    )
)
for i in range(matrix.shape[0]):
    for j in range(matrix.shape[1]):
        heatmap.add_annotation(
            x=labels[j],
            y=labels[i],
            text=str(matrix[i, j]),
            showarrow=False,
            font=dict(
                size=20,
                color="white" if matrix[i, j] >= matrix.max() / 2 else NAVY,
            ),
        )
heatmap.update_layout(
    title="Logistic model: predicted against actual salary class",
    height=460,
)
heatmap.update_xaxes(title="Predicted", showgrid=False, ticks="")
heatmap.update_yaxes(title="Actual", showgrid=False, ticks="", autorange="reversed")
plot_theme.save(heatmap, "model_confusion_matrix", width=760, height=460)

# ------------------------------------------------------------
# 6. Strongest features
# ------------------------------------------------------------

top = coefficients.head(15).sort_values("logistic_coefficient")
bars = go.Figure(
    go.Bar(
        x=top["logistic_coefficient"],
        y=top["feature"],
        orientation="h",
        marker_color=[TEAL if v > 0 else GOLD for v in top["logistic_coefficient"]],
        hovertemplate="%{y}: %{x:.2f}<extra></extra>",
    )
)
bars.update_layout(
    title="Features most associated with an above-median salary",
    height=620,
    showlegend=False,
)
bars.update_xaxes(title="Logistic coefficient (standardized features)", zeroline=True, zerolinecolor=GRAY)
bars.update_yaxes(showgrid=False, ticks="", title="")
plot_theme.save(bars, "model_top_features", width=900, height=620)

# ------------------------------------------------------------
# 7. Summary
# ------------------------------------------------------------

print(f"Analytical sample: {len(sample)} postings with usable salary.")
print(f"Median midpoint used as the split: ${median_salary:,.0f}")
print(f"Class balance: {int(y.sum())} above median, {int((1 - y).sum())} at or below.")
print(f"Features: {X.shape[1]} ({len(kept_skills)} skills at the {SKILL_THRESHOLD:.0%} threshold).")
print(f"Train / test: {len(X_train)} / {len(X_test)}")
print()
print(metrics.to_string(index=False))
print()
print("Strongest five features by absolute logistic coefficient:")
print(coefficients.head(5)[["feature", "logistic_coefficient", "forest_importance"]].to_string(index=False))
print()
print(f"Wrote {METRICS_PATH.relative_to(ROOT)} and {COEFFICIENTS_PATH.relative_to(ROOT)}")
print("Wrote figures/model_confusion_matrix.png and figures/model_top_features.png")
