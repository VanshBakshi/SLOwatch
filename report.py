import json
from datetime import datetime, timezone
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"

def save_report(report: dict) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPORTS_DIR / f"slowatch_report_{timestamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (REPORTS_DIR / "latest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return str(path)
