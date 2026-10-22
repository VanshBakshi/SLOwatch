def evaluate_slo(metrics: dict, target_percent: float = 99.9,
                 p95_latency_target_ms: float = 500.0) -> dict:
    if not 0 < target_percent <= 100:
        raise ValueError("target_percent must be greater than 0 and at most 100.")
    if p95_latency_target_ms <= 0:
        raise ValueError("p95_latency_target_ms must be positive.")

    availability = metrics["availability_percent"]
    allowed_failure_rate = 1 - target_percent / 100
    actual_failure_rate = metrics["failed_requests"] / metrics["total_requests"]
    budget_consumed = (
        actual_failure_rate / allowed_failure_rate * 100
        if allowed_failure_rate > 0 and actual_failure_rate > 0
        else (0.0 if actual_failure_rate == 0 else None)
    )
    latency_ok = metrics["latency_ms"]["p95"] <= p95_latency_target_ms
    availability_ok = availability >= target_percent
    alerts = []
    if not availability_ok:
        alerts.append({
            "type": "AVAILABILITY_SLO_BREACH",
            "severity": "HIGH",
            "message": f"Availability {availability}% is below target {target_percent}%.",
        })
    if not latency_ok:
        alerts.append({
            "type": "LATENCY_SLO_BREACH",
            "severity": "MEDIUM",
            "message": f"p95 latency {metrics['latency_ms']['p95']} ms exceeds target {p95_latency_target_ms} ms.",
        })
    if budget_consumed is not None and budget_consumed >= 50:
        alerts.append({
            "type": "ERROR_BUDGET_WARNING",
            "severity": "HIGH" if budget_consumed >= 100 else "MEDIUM",
            "message": f"{budget_consumed:.1f}% of the error budget has been consumed.",
        })

    return {
        "slo_target_percent": target_percent,
        "slo_met": availability_ok,
        "p95_latency_target_ms": p95_latency_target_ms,
        "latency_slo_met": latency_ok,
        "error_budget": {
            "allowed_failure_percent": round(allowed_failure_rate * 100, 4),
            "actual_failure_percent": metrics["failure_rate_percent"],
            "budget_consumed_percent": round(budget_consumed, 2) if budget_consumed is not None else None,
            "remaining_budget_percent": round(max(0, 100 - budget_consumed), 2) if budget_consumed is not None else None,
        },
        "status": "SLO_BREACHED" if not availability_ok else ("DEGRADED" if not latency_ok or alerts else "HEALTHY"),
        "alerts": alerts,
    }
