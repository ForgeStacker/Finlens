"""Amazon Neptune collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_neptune(session, cost_map) -> pd.DataFrame:
    client = session.client("neptune", region_name=REGION)
    rows = []

    paginator = client.get_paginator("describe_db_clusters")
    for page in safe_call(lambda: list(paginator.paginate(
        Filters=[{"Name": "engine", "Values": ["neptune"]}]
    )), []) or []:
        for cluster in page.get("DBClusters", []):
            members = cluster.get("DBClusterMembers", [])
            instance_ids = ", ".join(m.get("DBInstanceIdentifier", "") for m in members)
            rows.append({
                "DBClusterIdentifier": cluster.get("DBClusterIdentifier", ""),
                "DBClusterArn": cluster.get("DBClusterArn", ""),
                "Status": cluster.get("Status", ""),
                "Engine": cluster.get("Engine", ""),
                "EngineVersion": cluster.get("EngineVersion", ""),
                "DatabaseName": cluster.get("DatabaseName", ""),
                "Endpoint": cluster.get("Endpoint", ""),
                "ReaderEndpoint": cluster.get("ReaderEndpoint", ""),
                "Port": cluster.get("Port", ""),
                "MultiAZ": cluster.get("MultiAZ", ""),
                "AvailabilityZones": ", ".join(cluster.get("AvailabilityZones", [])),
                "VpcId": cluster.get("VpcId", ""),
                "StorageEncrypted": cluster.get("StorageEncrypted", ""),
                "DeletionProtection": cluster.get("DeletionProtection", ""),
                "BackupRetentionPeriod": cluster.get("BackupRetentionPeriod", ""),
                "Instances": instance_ids,
                "ClusterCreateTime": str(cluster.get("ClusterCreateTime", "") or ""),
            })

    return pd.DataFrame(rows)
