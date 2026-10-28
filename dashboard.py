"""Streamlit dashboard for SentinelIQ."""
from io import BytesIO
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from sentinel.analysis import analyze_dataframe
from sentinel.reporting import build_pdf_report

st.set_page_config(page_title="SentinelIQ", page_icon="🛰️", layout="wide")
st.title("🛰️ SentinelIQ")
st.caption("AI-powered data intelligence • profiling • anomaly detection • demo risk scoring")

with st.sidebar:
    st.header("Analysis settings")
    contamination = st.slider("Expected anomaly fraction", min_value=0.01, max_value=0.25, value=0.05, step=0.01)
    st.caption("This controls Isolation Forest's expected outlier fraction; tune it for your dataset.")
    st.markdown("---")
    st.caption("Demo scores are indicators, not calibrated probabilities.")

uploaded = st.file_uploader("Upload a CSV or Excel dataset", type=["csv", "xlsx", "xls"])
if uploaded is None:
    sample_path = Path("data/sample_transactions.csv")
    if sample_path.exists() and st.button("Analyze included sample dataset"):
        df = pd.read_csv(sample_path)
    else:
        st.info("Upload a dataset or click **Analyze included sample dataset**.")
        st.stop()
else:
    try:
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
    except Exception as exc:
        st.error(f"Could not read the file: {exc}")
        st.stop()

with st.expander("Dataset preview", expanded=False):
    st.dataframe(df.head(25), use_container_width=True)

try:
    result = analyze_dataframe(df, contamination=contamination)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

profile = result["profile"]
enriched = result["rows"]

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Rows", f"{profile['rows']:,}")
k2.metric("Columns", profile["columns"])
k3.metric("Missing cells", f"{profile['missing_cells']:,}")
k4.metric("Flagged anomalies", profile["flagged_rows"])
k5.metric("High alerts", profile["high_alerts"])

left, right = st.columns(2)
with left:
    st.subheader("Alert distribution")
    alert_counts = enriched["alert"].value_counts().rename_axis("Alert").reset_index(name="Rows")
    st.plotly_chart(px.pie(alert_counts, names="Alert", values="Rows", hole=0.45), use_container_width=True)
with right:
    st.subheader("Risk score distribution")
    st.plotly_chart(px.histogram(enriched, x="risk_score", nbins=20, title="Rows by demo risk score"), use_container_width=True)

numeric = result["numeric_columns"]
if len(numeric) >= 2:
    st.subheader("Numeric feature relationship")
    xcol = st.selectbox("X axis", numeric, index=0)
    ycol = st.selectbox("Y axis", numeric, index=min(1, len(numeric)-1))
    st.plotly_chart(px.scatter(enriched, x=xcol, y=ycol, color="alert", hover_data=["risk_score", "anomaly"]), use_container_width=True)

st.subheader("Alerts and analyzed records")
filter_alert = st.multiselect("Show alert levels", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM"])
shown = enriched[enriched["alert"].isin(filter_alert)].sort_values("risk_score", ascending=False)
st.dataframe(shown, use_container_width=True, height=360)

st.subheader("Dataset quality")
quality = pd.DataFrame({
    "Column": list(profile["missing_by_column"].keys()),
    "Missing values": list(profile["missing_by_column"].values()),
})
st.plotly_chart(px.bar(quality, x="Column", y="Missing values", title="Missing values per column"), use_container_width=True)

st.subheader("Downloads")
csv_bytes = enriched.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download analyzed CSV", data=csv_bytes, file_name="sentineliq-analyzed.csv", mime="text/csv")
pdf_bytes = build_pdf_report(profile)
st.download_button("⬇️ Download PDF summary", data=pdf_bytes, file_name="sentineliq-report.pdf", mime="application/pdf")

with st.expander("Profile details"):
    st.json({
        "column_types": profile["column_types"],
        "missing_by_column": profile["missing_by_column"],
        "numeric_columns": profile["numeric_columns"],
        "mean_risk_score": profile["mean_risk_score"],
        "duplicate_rows": profile["duplicate_rows"],
    })

st.caption("Interpret flags in context. Do not use this demo alone for financial, medical, hiring, or other high-impact decisions.")
