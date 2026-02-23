"""AWS Glue collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_glue(session, cost_map):
    glue = session.client("glue", region_name=REGION)
    rows = []
    jobs = safe_call(lambda: glue.get_jobs().get("Jobs", []), [])
    for job in jobs or []:
        rows.append({
            "Name": job.get("Name"),
            "Role": job.get("Role"),
            "Type": job.get("Command", {}).get("Name"),
            "Status": job.get("ExecutionProperty", {}).get("MaxConcurrentRuns"),
            "WorkerType": job.get("WorkerType"),
            "NumberOfWorkers": job.get("NumberOfWorkers"),
            "GlueVersion": job.get("GlueVersion"),
            "MaxRetries": job.get("MaxRetries"),
            "Timeout": job.get("Timeout"),
            "CreatedOn": str(job.get("CreatedOn")),
            "LastModifiedOn": str(job.get("LastModifiedOn")),
            "Description": job.get("Description", "")
        })
    return pd.DataFrame(rows)
