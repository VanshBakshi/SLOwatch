from __future__ import annotations
import io
import json
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, Query
from fastapi.responses import JSONResponse

from app.metrics import calculate_metrics, validate_logs
from app.slo_engine import evaluate_slo
from app.report import save_report, REPORTS_DIR

app = FastAPI(
    title="SLOWatch",
    description="Service reliability, SLO, latency, and error-budget monitoring API.",
    version="1.0.0",
)

LATEST: dict = {}
LATEST_BY_SERVICE: dict = {}

@app.get("/")
def root():
    return {"name": "SLOWatch", "status": "running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "SLOWatch"}

@app.post("/logs/analyze")
async def analyze_logs(
    file: UploadFile = File(...),
    slo_target_percent: float = Query(99.9, gt=0, le=100),
    p95_latency_target_ms: float = Query(500.0, gt=0),
):
    global LATEST
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file.")
    try:
        raw = await file.read()
        df = pd.read_csv(io.BytesIO(raw))
        df = validate_logs(df)
        overall = calculate_metrics(df)
        service_results = {}
        for service, group in df.groupby("service"):
            metrics = calculate_metrics(group)
            slo = evaluate_slo(metrics, slo_target_percent, p95_latency_target_ms)
            service_results[service] = {"metrics": metrics, **slo}
        overall_slo = evaluate_slo(overall, slo_target_percent, p95_latency_target_ms)
        report = {
            "service": overall["services"][0] if len(overall["services"]) == 1 else "multiple",
            "metrics": overall,
            **overall_slo,
            "service_results": service_results,
        }
        report_path = save_report(report)
        report["report_path"] = report_path
        LATEST = report
        LATEST_BY_SERVICE.update(service_results)
        return report
    except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to analyze file: {exc}")

@app.get("/slo/{service}")
def get_slo(service: str):
    if service not in LATEST_BY_SERVICE:
        raise HTTPException(status_code=404, detail="No analysis found for this service. Upload logs first.")
    return {"service": service, **LATEST_BY_SERVICE[service]}

@app.get("/budget/{service}")
def get_budget(service: str):
    if service not in LATEST_BY_SERVICE:
        raise HTTPException(status_code=404, detail="No analysis found for this service. Upload logs first.")
    result = LATEST_BY_SERVICE[service]
    return {"service": service, **result["error_budget"]}

@app.get("/alerts")
def get_alerts():
    if not LATEST:
        return {"alerts": [], "message": "Upload a CSV file to generate alerts."}
    alerts = []
    for service, result in LATEST.get("service_results", {}).items():
        for alert in result.get("alerts", []):
            alerts.append({"service": service, **alert})
    return {"count": len(alerts), "alerts": alerts}

@app.get("/reports/latest")
def latest_report():
    path = REPORTS_DIR / "latest.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No report available yet. Upload logs first.")
    return JSONResponse(content=json.loads(path.read_text(encoding="utf-8")))
