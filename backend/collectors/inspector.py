"""AWS Inspector V2 collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_inspector(session, cost_map) -> pd.DataFrame:
    client = session.client("inspector2", region_name=REGION)
    rows = []

    # Account status
    status = safe_call(lambda: client.batch_get_account_status(accountIds=[]).get("accounts", []), [])
    for acct in status or []:
        resource_state = acct.get("resourceState", {})
        rows.append({
            "AccountId": acct.get("accountId", ""),
            "State": acct.get("state", {}).get("status", ""),
            "EC2Status": resource_state.get("ec2", {}).get("status", ""),
            "ECRStatus": resource_state.get("ecr", {}).get("status", ""),
            "LambdaStatus": resource_state.get("lambda", {}).get("status", ""),
            "ResourceType": "AccountSummary",
            "Severity": "",
            "FindingCount": "",
        })

    # Finding aggregation by severity
    agg = safe_call(
        lambda: client.list_finding_aggregations(
            aggregationType="SEVERITY",
        ).get("responses", []),
        [],
    )
    for resp in agg or []:
        sev_agg = resp.get("severityCounts", {})
        for severity, count in sev_agg.items():
            rows.append({
                "AccountId": "",
                "State": "",
                "EC2Status": "",
                "ECRStatus": "",
                "LambdaStatus": "",
                "ResourceType": "FindingAggregate",
                "Severity": severity,
                "FindingCount": count,
            })

    return pd.DataFrame(rows)
