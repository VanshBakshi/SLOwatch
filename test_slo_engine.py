from app.slo_engine import evaluate_slo

def metrics(availability=99.0, failed=10, total=1000, p95=600):
    return {
        "availability_percent": availability,
        "failed_requests": failed,
        "total_requests": total,
        "failure_rate_percent": failed / total * 100,
        "latency_ms": {"p95": p95},
    }

def test_availability_breach_detected():
    result = evaluate_slo(metrics())
    assert result["slo_met"] is False
    assert result["status"] == "SLO_BREACHED"
    assert result["error_budget"]["budget_consumed_percent"] == 1000.0

def test_healthy_service():
    result = evaluate_slo(metrics(availability=99.99, failed=1, total=10000, p95=120))
    assert result["slo_met"] is True
    assert result["latency_slo_met"] is True
    assert result["status"] == "HEALTHY"

def test_invalid_slo_rejected():
    import pytest
    with pytest.raises(ValueError):
        evaluate_slo(metrics(), target_percent=0)
