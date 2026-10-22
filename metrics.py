from __future__ import annotations
import pandas as pd

SUCCESS_MIN = 200
SUCCESS_MAX = 399

REQUIRED_COLUMNS = {"timestamp", "service", "status_code", "latency_ms"}

def validate_logs(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if df.empty:
        raise ValueError("The CSV contains no request records.")

    clean = df.copy()
    clean["status_code"] = pd.to_numeric(clean["status_code"], errors="coerce")
    clean["latency_ms"] = pd.to_numeric(clean["latency_ms"], errors="coerce")
    clean["timestamp"] = pd.to_datetime(clean["timestamp"], errors="coerce", utc=True)

    if clean[["status_code", "latency_ms", "timestamp"]].isna().any().any():
        raise ValueError("Invalid status_code, latency_ms, or timestamp value found.")
    if (clean["latency_ms"] < 0).any():
        raise ValueError("latency_ms cannot be negative.")
    if clean["service"].astype(str).str.strip().eq("").any():
        raise ValueError("service cannot be blank.")

    clean["service"] = clean["service"].astype(str)
    clean["status_code"] = clean["status_code"].astype(int)
    return clean

def calculate_metrics(df: pd.DataFrame) -> dict:
    df = validate_logs(df)
    total = int(len(df))
    successful = int(df["status_code"].between(SUCCESS_MIN, SUCCESS_MAX).sum())
    failed = total - successful
    failure_rate = failed / total
    latencies = df["latency_ms"]
    return {
        "total_requests": total,
        "successful_requests": successful,
        "failed_requests": failed,
        "availability_percent": round(successful / total * 100, 4),
        "failure_rate_percent": round(failure_rate * 100, 4),
        "latency_ms": {
            "p50": round(float(latencies.quantile(0.50)), 2),
            "p95": round(float(latencies.quantile(0.95)), 2),
            "p99": round(float(latencies.quantile(0.99)), 2),
            "max": round(float(latencies.max()), 2),
        },
        "services": sorted(df["service"].unique().tolist()),
        "window_start": df["timestamp"].min().isoformat(),
        "window_end": df["timestamp"].max().isoformat(),
    }
