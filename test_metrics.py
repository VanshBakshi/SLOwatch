import pandas as pd
import pytest
from app.metrics import calculate_metrics, validate_logs

def sample():
    return pd.DataFrame({
        "timestamp": ["2026-10-21T10:00:00Z"] * 4,
        "service": ["checkout"] * 4,
        "status_code": [200, 201, 500, 503],
        "latency_ms": [100, 200, 300, 400],
    })

def test_metrics_counts_and_availability():
    result = calculate_metrics(sample())
    assert result["total_requests"] == 4
    assert result["failed_requests"] == 2
    assert result["availability_percent"] == 50.0
    assert result["latency_ms"]["p50"] == 250.0

def test_missing_column_rejected():
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_logs(pd.DataFrame({"service": ["checkout"]}))

def test_empty_dataset_rejected():
    with pytest.raises(ValueError, match="no request records"):
        validate_logs(pd.DataFrame(columns=["timestamp", "service", "status_code", "latency_ms"]))
