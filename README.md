# SLOWatch

SLOWatch is a small service-reliability monitoring API built with Python and FastAPI. It analyzes request logs, calculates availability and latency percentiles, evaluates service-level objectives (SLOs), estimates error-budget consumption, and generates alerts and JSON reports.

## Features

- CSV request-log ingestion and validation
- Availability and failure-rate calculations
- p50, p95, p99, and maximum latency
- Configurable availability and p95 latency targets
- Error-budget consumption and remaining-budget estimates
- Per-service status and alert summaries
- Timestamped JSON reports plus `reports/latest.json`
- Automated tests with pytest

## Requirements

Python 3.10+ recommended.

## Windows PowerShell setup

```powershell
cd SLOWatch
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run commands using `.\.venv\Scripts\python.exe` instead.

## Run the API

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to use the interactive API documentation.

## Analyze the sample CSV

In Swagger UI, open `POST /logs/analyze`, choose `data/sample_requests.csv`, and click **Execute**.

Alternatively, using curl:

```bash
curl -X POST "http://127.0.0.1:8000/logs/analyze?slo_target_percent=99.9&p95_latency_target_ms=500" -F "file=@data/sample_requests.csv"
```

Then try:

- `GET /health`
- `GET /slo/checkout`
- `GET /budget/checkout`
- `GET /alerts`
- `GET /reports/latest`

## Run tests

```powershell
python -m pytest -q
```

## Input CSV format

Required columns:

- `timestamp`: parseable date/time; timestamps are normalized to UTC
- `service`: service identifier
- `status_code`: HTTP response code
- `latency_ms`: non-negative response latency in milliseconds

This prototype considers HTTP codes 200–399 successful. Change that rule in `app/metrics.py` if your organization defines success differently.

## How the calculations work

- Availability = successful requests / total requests × 100
- Failure rate = failed requests / total requests × 100
- Error budget consumption = observed failure rate / allowed failure rate × 100
- Allowed failure rate = 1 − (SLO target / 100)
- Latency percentiles are calculated from the observed request latencies using Pandas quantiles.

If the target is 100% availability, the allowed failure budget is zero. In that special case, the report returns `null` for budget consumption when failures occur, because the ratio is undefined.

## Limitations

This is a portfolio MVP, not a production observability platform. Data and latest results are held in process memory; restart clears API state. Reports are local files. The sample does not implement authentication, persistent databases, distributed aggregation, alert delivery, or a rolling time-window burn-rate algorithm. A real deployment should define SLI semantics, evaluation windows, minimum sample sizes, and alert policies with the service owners.

## Suggested next steps

1. Add a rolling-window error-budget burn-rate calculation.
2. Store historical metrics in PostgreSQL or SQLite.
3. Add a Streamlit dashboard.
4. Add CI with GitHub Actions.
5. Add API authentication and deployment configuration.
