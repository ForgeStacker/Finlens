"""AWS Snowball collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_snowball(session, cost_map) -> pd.DataFrame:
    client = session.client("snowball", region_name=REGION)
    rows = []

    paginator = client.get_paginator("list_jobs")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for job in page.get("JobListEntries", []):
            rows.append({
                "JobId": job.get("JobId", ""),
                "JobType": job.get("JobType", ""),
                "JobState": job.get("JobState", ""),
                "SnowballType": job.get("SnowballType", ""),
                "IsMaster": job.get("IsMaster", ""),
                "Description": job.get("Description", ""),
                "CreationDate": str(job.get("CreationDate", "") or ""),
            })

    return pd.DataFrame(rows)
