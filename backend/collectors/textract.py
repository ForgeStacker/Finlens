"""Amazon Textract collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_textract(session, cost_map) -> pd.DataFrame:
    client = session.client("textract", region_name=REGION)
    rows = []

    jobs = safe_call(lambda: client.list_document_text_detection_jobs().get("DocumentTextDetectionJobSummaryList", []), [])
    for job in jobs or []:
        rows.append({
            "JobId": job.get("JobId", ""),
            "JobTag": job.get("JobTag", ""),
            "Status": job.get("JobStatus", ""),
            "CreationTime": str(job.get("CreationTime", "") or ""),
            "CompletionTime": str(job.get("CompletionTime", "") or ""),
            "DocumentLocation": str(job.get("DocumentLocation", {}).get("S3Object", {}).get("Name", "")),
        })

    return pd.DataFrame(rows)
