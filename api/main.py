"""FastAPI endpoints for SentinelIQ."""
from io import BytesIO
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from sentinel.analysis import analyze_dataframe, json_safe
from sentinel.reporting import build_pdf_report
from sentinel.storage import save_summary

app = FastAPI(
    title="SentinelIQ API",
    description="Dataset profiling, anomaly detection, demo risk scoring, and PDF reporting.",
    version="1.0.0",
)


def read_dataset(filename: str, content: bytes) -> pd.DataFrame:
    try:
        if filename.lower().endswith(".csv"):
            return pd.read_csv(BytesIO(content))
        if filename.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(BytesIO(content))
        raise HTTPException(status_code=415, detail="Upload a CSV or Excel (.xlsx) file.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read dataset: {exc}") from exc


@app.get("/health")
def health():
    return {"status": "ok", "service": "SentinelIQ API"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...), contamination: float = 0.05):
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is larger than 15 MB.")
    df = read_dataset(file.filename or "", content)
    try:
        result = analyze_dataframe(df, contamination)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    profile = result["profile"]
    try:
        save_summary(profile)
    except Exception:
        # Keep analysis available if optional persistence is not configured.
        pass
    return {
        "profile": json_safe(profile),
        "preview": json_safe(result["rows"].head(100).to_dict(orient="records")),
        "note": "Risk scores are demo indicators, not calibrated probabilities.",
    }


@app.post("/report")
async def report(file: UploadFile = File(...), contamination: float = 0.05):
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is larger than 15 MB.")
    df = read_dataset(file.filename or "", content)
    try:
        result = analyze_dataframe(df, contamination)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    pdf = build_pdf_report(result["profile"])
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="sentineliq-report.pdf"'},
    )
