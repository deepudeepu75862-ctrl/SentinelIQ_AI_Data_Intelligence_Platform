"""Dataset profiling, anomaly detection, and transparent demo risk scoring."""
from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def analyze_dataframe(df: pd.DataFrame, contamination: float = 0.05) -> dict[str, Any]:
    """Analyze a dataframe and return JSON-serializable results plus enriched rows."""
    if df.empty:
        raise ValueError("The uploaded dataset is empty.")
    if len(df) < 10:
        raise ValueError("Please provide at least 10 rows for anomaly detection.")
    if not 0.01 <= contamination <= 0.25:
        raise ValueError("contamination must be between 0.01 and 0.25.")

    clean = df.copy()
    clean.columns = [str(c) for c in clean.columns]
    numeric = clean.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan)
    if numeric.shape[1] == 0:
        raise ValueError("No numeric columns found. Include at least one numeric column.")

    # Drop numeric columns that are entirely missing; remaining missing values are imputed.
    numeric = numeric.dropna(axis=1, how="all")
    if numeric.shape[1] == 0:
        raise ValueError("Numeric columns contain no usable values.")
    pipeline = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        IsolationForest(
            n_estimators=150,
            contamination=contamination,
            random_state=42,
        ),
    )
    labels = pipeline.fit_predict(numeric)
    forest = pipeline.named_steps["isolationforest"]
    # Higher decision_function values are more normal; invert and scale to 0..100.
    raw_anomaly = -forest.decision_function(
        pipeline.named_steps["standardscaler"].transform(
            pipeline.named_steps["simpleimputer"].transform(numeric)
        )
    )
    low, high = float(np.min(raw_anomaly)), float(np.max(raw_anomaly))
    if high - low < 1e-12:
        anomaly_score = np.zeros(len(numeric))
    else:
        anomaly_score = (raw_anomaly - low) / (high - low) * 100.0

    # Robust outlier flags via median absolute deviation, with a safe fallback for constant columns.
    imputed = pd.DataFrame(
        pipeline.named_steps["simpleimputer"].transform(numeric),
        columns=numeric.columns,
        index=numeric.index,
    )
    med = imputed.median()
    mad = (imputed - med).abs().median().replace(0, np.nan)
    robust_z = (0.6745 * (imputed - med).abs().div(mad)).replace([np.inf, -np.inf], np.nan).fillna(0)
    outlier_count = (robust_z > 3.5).sum(axis=1).to_numpy()
    outlier_component = np.minimum(outlier_count / max(1, numeric.shape[1]), 1.0) * 100
    risk = np.clip(0.75 * anomaly_score + 0.25 * outlier_component, 0, 100)

    enriched = clean.copy()
    enriched["anomaly"] = np.where(labels == -1, "Flagged", "Normal")
    enriched["anomaly_score"] = np.round(anomaly_score, 2)
    enriched["risk_score"] = np.round(risk, 2)
    enriched["alert"] = np.where(risk >= 70, "HIGH", np.where(risk >= 45, "MEDIUM", "LOW"))

    profile = {
        "rows": int(len(clean)),
        "columns": int(len(clean.columns)),
        "numeric_columns": [str(c) for c in numeric.columns],
        "missing_cells": int(clean.isna().sum().sum()),
        "duplicate_rows": int(clean.duplicated().sum()),
        "column_types": {str(k): str(v) for k, v in clean.dtypes.items()},
        "missing_by_column": {str(k): int(v) for k, v in clean.isna().sum().items()},
        "statistics": clean.describe(include="all").replace({np.nan: None}).to_dict(),
        "flagged_rows": int((labels == -1).sum()),
        "high_alerts": int((risk >= 70).sum()),
        "mean_risk_score": round(float(np.mean(risk)), 2),
    }
    return {"profile": profile, "rows": enriched, "numeric_columns": list(numeric.columns)}


def json_safe(value: Any) -> Any:
    """Recursively convert common NumPy/Pandas values to JSON-safe values."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value):
        return None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
