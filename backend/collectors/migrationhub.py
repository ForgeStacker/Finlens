"""AWS Migration Hub collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_migrationhub(session, cost_map) -> pd.DataFrame:
    # Migration Hub is only available in us-east-1 and eu-central-1
    client = session.client("mgh", region_name="us-east-1")
    rows = []

    # Migration tasks
    paginator = client.get_paginator("list_migration_tasks")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for task in page.get("MigrationTaskSummaryList", []):
            rows.append({
                "ProgressUpdateStream": task.get("ProgressUpdateStream", ""),
                "MigrationTaskName": task.get("MigrationTaskName", ""),
                "Status": task.get("Status", ""),
                "StatusDetail": task.get("StatusDetail", ""),
                "PercentDone": task.get("PercentDone", ""),
                "UpdateDateTime": str(task.get("UpdateDateTime", "") or ""),
            })

    return pd.DataFrame(rows)
