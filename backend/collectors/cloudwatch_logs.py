"""CloudWatch Log Groups collector."""
from __future__ import annotations
import pandas as pd
from config import REGION
from aws_utils import safe_call

def collect_cloudwatch_logs(session, cost_map):
    logs = session.client("logs", region_name=REGION)
    log_groups = safe_call(lambda: logs.describe_log_groups()["logGroups"], [])
    rows = []
    for lg in log_groups:
        retention = lg.get("retentionInDays")
        if retention is None:
            retention_display = "Never expire"
        else:
            retention_display = str(retention)
        stored_bytes = lg.get("storedBytes", 0)
        storage_mb = round(stored_bytes / (1024 * 1024), 2) if stored_bytes else 0.0
        rows.append({
            "LogGroupName": lg.get("logGroupName"),
            "Retention": retention_display,
            "Storage Mb": storage_mb,
        })
    return pd.DataFrame(rows)
