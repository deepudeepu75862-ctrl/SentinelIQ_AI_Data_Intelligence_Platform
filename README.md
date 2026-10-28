# SentinelIQ — AI-Powered Data Intelligence Platform

SentinelIQ is a portfolio-ready starter application for CSV/Excel analytics, anomaly detection, risk scoring, interactive dashboards, alerts, PDF reporting, a FastAPI service, optional PostgreSQL storage, Docker, tests, and GitHub Actions.

> **Important:** This is a demonstration/decision-support tool, not a validated safety-critical risk model. Its anomaly and risk scores are heuristic/unsupervised indicators; validate on domain-specific data before making real decisions.

## Features
- Upload CSV/XLSX files in Streamlit.
- Automatically profile columns, missing values, descriptive statistics, and correlations.
- Detect unusual numeric rows with Isolation Forest.
- Calculate a transparent demo risk score from anomaly score and robust outlier counts.
- View Plotly charts, KPI cards, and flagged-row alerts.
- Download analyzed rows as CSV and a PDF summary report.
- FastAPI health, analysis, and upload endpoints.
- Optional PostgreSQL persistence for analysis summaries.
- Docker Compose, unit tests, and GitHub Actions CI.

## Quick start (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run dashboard.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

In a second terminal, activate the same environment and run:

```powershell
uvicorn api.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

## Docker

Install Docker Desktop, then from this folder:

```powershell
docker compose up --build
```

Dashboard: `http://localhost:8501`  
API docs: `http://localhost:8000/docs`

PostgreSQL is included in Compose. The app works without a database; set `DATABASE_URL` to enable summary persistence.

## Sample data
Use `data/sample_transactions.csv` in the dashboard to try the pipeline. It is synthetic demo data, not real financial records.

## API examples

Health:
```powershell
curl http://localhost:8000/health
```

Analyze a CSV:
```powershell
curl -X POST "http://localhost:8000/analyze" -F "file=@data/sample_transactions.csv"
```

## Project structure

```text
SentinelIQ_AI_Data_Intelligence_Platform/
├── api/main.py
├── sentinel/analysis.py
├── sentinel/reporting.py
├── sentinel/storage.py
├── dashboard.py
├── data/sample_transactions.csv
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .github/workflows/ci.yml
```

## Model notes
- Isolation Forest is fitted to numeric columns after median imputation and standardization.
- A robust median/MAD-based outlier count is also calculated per row.
- `risk_score` is a transparent demo score from 0–100. It is not a calibrated probability.
- If fewer than 10 usable rows or no numeric columns are available, the pipeline returns a useful validation error.
- Avoid uploading confidential, personally identifiable, regulated, or production data to an unreviewed demo.

## Tests

```powershell
pytest -q
```

## Next steps for a stronger portfolio
1. Add authentication and role-based access.
2. Add dataset-size limits and background jobs.
3. Add model evaluation using labeled domain data.
4. Add audit logging, monitoring, and data retention controls.
5. Deploy to a cloud platform and document the live demo.
