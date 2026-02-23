"""AWS Compute Optimizer collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_computeoptimizer(session, cost_map) -> pd.DataFrame:
    client = session.client("compute-optimizer", region_name=REGION)
    rows = []

    # EC2 instance recommendations
    recs = safe_call(
        lambda: client.get_ec2_instance_recommendations().get("instanceRecommendations", []), []
    )
    for r in recs or []:
        finding = r.get("finding", "")
        cur_type = r.get("currentInstanceType", "")
        options = r.get("recommendationOptions", [])
        recommended_type = options[0].get("instanceType", "") if options else ""
        saving = options[0].get("estimatedMonthlySavings", {}).get("value", "") if options else ""
        rows.append({
            "ResourceType": "EC2Instance",
            "InstanceArn": r.get("instanceArn", ""),
            "InstanceName": r.get("instanceName", ""),
            "CurrentInstanceType": cur_type,
            "RecommendedInstanceType": recommended_type,
            "Finding": finding,
            "EstimatedMonthlySavingsUSD": saving,
            "LastRefreshTimestamp": str(r.get("lastRefreshTimestamp", "") or ""),
        })

    # EBS volume recommendations
    ebs_recs = safe_call(
        lambda: client.get_ebs_volume_recommendations().get("volumeRecommendations", []), []
    )
    for r in ebs_recs or []:
        options = r.get("volumeRecommendationOptions", [])
        saving = options[0].get("estimatedMonthlySavings", {}).get("value", "") if options else ""
        rows.append({
            "ResourceType": "EBSVolume",
            "InstanceArn": r.get("volumeArn", ""),
            "InstanceName": "",
            "CurrentInstanceType": r.get("currentConfiguration", {}).get("volumeType", ""),
            "RecommendedInstanceType": options[0].get("configuration", {}).get("volumeType", "") if options else "",
            "Finding": r.get("finding", ""),
            "EstimatedMonthlySavingsUSD": saving,
            "LastRefreshTimestamp": str(r.get("lastRefreshTimestamp", "") or ""),
        })

    return pd.DataFrame(rows)
