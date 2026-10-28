import numpy as np
import pandas as pd
import pytest
from sentinel.analysis import analyze_dataframe


def sample_frame(n=60):
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "amount": rng.normal(50, 8, n),
        "duration": rng.normal(12, 2, n),
        "count": rng.integers(1, 8, n),
    })
    df.loc[n - 1, "amount"] = 500
    return df


def test_analysis_adds_expected_columns_and_profile():
    result = analyze_dataframe(sample_frame())
    assert {"anomaly", "anomaly_score", "risk_score", "alert"} <= set(result["rows"].columns)
    assert result["profile"]["rows"] == 60
    assert result["rows"]["risk_score"].between(0, 100).all()


def test_rejects_too_few_rows():
    with pytest.raises(ValueError, match="at least 10"):
        analyze_dataframe(sample_frame(5))


def test_rejects_no_numeric_columns():
    with pytest.raises(ValueError, match="No numeric columns"):
        analyze_dataframe(pd.DataFrame({"name": [f"person{i}" for i in range(12)]}))


def test_rejects_invalid_contamination():
    with pytest.raises(ValueError, match="contamination"):
        analyze_dataframe(sample_frame(), contamination=0.5)
