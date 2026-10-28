"""Optional SQLAlchemy persistence for analysis summaries."""
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, text


def save_summary(profile: dict) -> bool:
    url = os.getenv("DATABASE_URL")
    if not url:
        return False
    engine = create_engine(url, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL,
                rows_count INTEGER NOT NULL,
                columns_count INTEGER NOT NULL,
                flagged_rows INTEGER NOT NULL,
                high_alerts INTEGER NOT NULL,
                mean_risk_score FLOAT NOT NULL
            )
        """))
        conn.execute(text("""
            INSERT INTO analysis_runs
            (created_at, rows_count, columns_count, flagged_rows, high_alerts, mean_risk_score)
            VALUES (:created_at, :rows_count, :columns_count, :flagged_rows, :high_alerts, :mean_risk_score)
        """), {
            "created_at": datetime.now(timezone.utc),
            "rows_count": int(profile["rows"]),
            "columns_count": int(profile["columns"]),
            "flagged_rows": int(profile["flagged_rows"]),
            "high_alerts": int(profile["high_alerts"]),
            "mean_risk_score": float(profile["mean_risk_score"]),
        })
    return True
