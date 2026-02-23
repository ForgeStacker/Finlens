"""Amazon Redshift collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_redshift(session, cost_map) -> pd.DataFrame:
    client = session.client("redshift", region_name=REGION)
    rows = []

    paginator = client.get_paginator("describe_clusters")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for cl in page.get("Clusters", []):
            tags = {t["Key"]: t["Value"] for t in (cl.get("Tags") or [])}
            nodes = cl.get("ClusterNodes", [])
            rows.append({
                "ClusterIdentifier": cl.get("ClusterIdentifier", ""),
                "ClusterArn": f"arn:aws:redshift:{REGION}:{cl.get('MasterUsername','')}:cluster:{cl.get('ClusterIdentifier','')}",
                "NodeType": cl.get("NodeType", ""),
                "ClusterStatus": cl.get("ClusterStatus", ""),
                "NumberOfNodes": cl.get("NumberOfNodes", ""),
                "DBName": cl.get("DBName", ""),
                "MasterUsername": cl.get("MasterUsername", ""),
                "Endpoint": cl.get("Endpoint", {}).get("Address", ""),
                "Port": cl.get("Endpoint", {}).get("Port", ""),
                "VpcId": cl.get("VpcId", ""),
                "AvailabilityZone": cl.get("AvailabilityZone", ""),
                "Encrypted": cl.get("Encrypted", ""),
                "PubliclyAccessible": cl.get("PubliclyAccessible", ""),
                "MultiAZ": cl.get("MultiAZ", ""),
                "PreferredMaintenanceWindow": cl.get("PreferredMaintenanceWindow", ""),
                "BackupRetentionPeriod": cl.get("AutomatedSnapshotRetentionPeriod", ""),
                "ClusterCreateTime": str(cl.get("ClusterCreateTime", "") or ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
            })

    return pd.DataFrame(rows)
