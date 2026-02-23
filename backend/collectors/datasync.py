"""AWS DataSync collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_datasync(session, cost_map) -> pd.DataFrame:
    client = session.client("datasync", region_name=REGION)
    rows = []

    tasks = safe_call(lambda: client.list_tasks().get("Tasks", []), [])
    for task in tasks or []:
        task_arn = task.get("TaskArn", "")
        detail = safe_call(lambda a=task_arn: client.describe_task(TaskArn=a), {})
        rows.append({
            "TaskArn": task_arn,
            "Name": task.get("Name", ""),
            "Status": task.get("Status", ""),
            "SourceLocationArn": detail.get("SourceLocationArn", ""),
            "DestinationLocationArn": detail.get("DestinationLocationArn", ""),
            "CloudWatchLogGroupArn": detail.get("CloudWatchLogGroupArn", ""),
            "Options": str(detail.get("Options", {}) or {}),
            "CurrentTaskExecutionArn": detail.get("CurrentTaskExecutionArn", ""),
            "CreationTime": str(detail.get("CreationTime", "") or ""),
        })

    return pd.DataFrame(rows)
