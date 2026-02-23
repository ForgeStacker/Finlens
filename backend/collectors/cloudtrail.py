"""AWS CloudTrail collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_cloudtrail(session, cost_map) -> pd.DataFrame:
    client = session.client("cloudtrail", region_name=REGION)
    rows = []

    trails = safe_call(lambda: client.describe_trails().get("trailList", []), [])
    for trail in trails or []:
        trail_name = trail.get("Name", "")
        status = safe_call(
            lambda n=trail_name: client.get_trail_status(Name=n), {}
        )
        rows.append({
            "TrailName": trail_name,
            "TrailARN": trail.get("TrailARN", ""),
            "S3BucketName": trail.get("S3BucketName", ""),
            "HomeRegion": trail.get("HomeRegion", ""),
            "IsMultiRegionTrail": trail.get("IsMultiRegionTrail", ""),
            "IsOrganizationTrail": trail.get("IsOrganizationTrail", ""),
            "IsLogging": status.get("IsLogging", ""),
            "LogFileValidationEnabled": trail.get("LogFileValidationEnabled", ""),
            "HasCustomEventSelectors": trail.get("HasCustomEventSelectors", ""),
            "HasInsightSelectors": trail.get("HasInsightSelectors", ""),
            "IncludeGlobalServiceEvents": trail.get("IncludeGlobalServiceEvents", ""),
            "LatestDeliveryTime": str(status.get("LatestDeliveryTime", "") or ""),
            "LatestNotificationTime": str(status.get("LatestNotificationTime", "") or ""),
        })

    return pd.DataFrame(rows)
