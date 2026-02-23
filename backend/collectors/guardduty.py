"""AWS GuardDuty collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_guardduty(session, cost_map) -> pd.DataFrame:
    client = session.client("guardduty", region_name=REGION)
    rows = []

    detector_ids = safe_call(lambda: client.list_detectors().get("DetectorIds", []), [])
    for detector_id in detector_ids or []:
        detail = safe_call(lambda did=detector_id: client.get_detector(DetectorId=did), {})
        finding_stats = safe_call(
            lambda did=detector_id: client.get_findings_statistics(
                DetectorId=did, FindingStatisticTypes=["COUNT_BY_SEVERITY"]
            ).get("FindingStatistics", {}).get("CountBySeverity", {}),
            {},
        )
        members = safe_call(
            lambda did=detector_id: client.list_members(DetectorId=did).get("Members", []), []
        )
        rows.append({
            "DetectorId": detector_id,
            "Status": detail.get("Status", ""),
            "FindingPublishingFrequency": detail.get("FindingPublishingFrequency", ""),
            "ServiceRole": detail.get("ServiceRole", ""),
            "MemberCount": len(members),
            "FindingsBySeverity": str(finding_stats),
            "UpdatedAt": str(detail.get("UpdatedAt", "") or ""),
            "CreatedAt": str(detail.get("CreatedAt", "") or ""),
        })

    return pd.DataFrame(rows)
