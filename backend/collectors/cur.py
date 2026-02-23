"""AWS Cost and Usage Report (CUR) collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_cur(session, cost_map) -> pd.DataFrame:
    # CUR API is only available in us-east-1
    client = session.client("cur", region_name="us-east-1")
    rows = []

    paginator = client.get_paginator("describe_report_definitions")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for report in page.get("ReportDefinitions", []):
            rows.append({
                "ReportName": report.get("ReportName", ""),
                "TimeUnit": report.get("TimeUnit", ""),
                "Format": report.get("Format", ""),
                "Compression": report.get("Compression", ""),
                "S3Bucket": report.get("S3Bucket", ""),
                "S3Prefix": report.get("S3Prefix", ""),
                "S3Region": report.get("S3Region", ""),
                "RefreshClosedReports": report.get("RefreshClosedReports", ""),
                "ReportVersioning": report.get("ReportVersioning", ""),
                "AdditionalArtifacts": ", ".join(report.get("AdditionalArtifacts", [])),
                "BillingViewArn": report.get("BillingViewArn", ""),
            })

    return pd.DataFrame(rows)
