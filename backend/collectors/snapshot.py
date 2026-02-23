"""EBS Snapshot collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_snapshots(session, cost_map) -> pd.DataFrame:
    client = session.client("ec2", region_name=REGION)
    rows = []

    paginator = client.get_paginator("describe_snapshots")
    for page in safe_call(lambda: list(paginator.paginate(OwnerIds=["self"])), []) or []:
        for snap in page.get("Snapshots", []):
            tags = {t["Key"]: t["Value"] for t in (snap.get("Tags") or [])}
            rows.append({
                "SnapshotId": snap.get("SnapshotId", ""),
                "Name": tags.get("Name", ""),
                "VolumeId": snap.get("VolumeId", ""),
                "VolumeSize(GiB)": snap.get("VolumeSize", ""),
                "State": snap.get("State", ""),
                "Encrypted": snap.get("Encrypted", ""),
                "KmsKeyId": snap.get("KmsKeyId", ""),
                "OwnerId": snap.get("OwnerId", ""),
                "Description": snap.get("Description", ""),
                "Progress": snap.get("Progress", ""),
                "StorageTier": snap.get("StorageTier", ""),
                "RestoreExpiryTime": str(snap.get("RestoreExpiryTime", "") or ""),
                "StartTime": str(snap.get("StartTime", "") or ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
            })

    return pd.DataFrame(rows)
