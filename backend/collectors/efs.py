"""Amazon EFS collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_efs(session, cost_map) -> pd.DataFrame:
    client = session.client("efs", region_name=REGION)
    rows = []

    paginator = client.get_paginator("describe_file_systems")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for fs in page.get("FileSystems", []):
            fs_id = fs.get("FileSystemId", "")
            tags = {t["Key"]: t["Value"] for t in (fs.get("Tags") or [])}
            # Mount targets
            mount_targets = safe_call(
                lambda fid=fs_id: client.describe_mount_targets(FileSystemId=fid).get("MountTargets", []), []
            )
            az_list = ", ".join(mt.get("AvailabilityZoneName", "") for mt in (mount_targets or []))
            subnet_list = ", ".join(mt.get("SubnetId", "") for mt in (mount_targets or []))
            rows.append({
                "FileSystemId": fs_id,
                "Name": tags.get("Name", ""),
                "FileSystemArn": fs.get("FileSystemArn", ""),
                "LifeCycleState": fs.get("LifeCycleState", ""),
                "PerformanceMode": fs.get("PerformanceMode", ""),
                "ThroughputMode": fs.get("ThroughputMode", ""),
                "ProvisionedThroughputMibps": fs.get("ProvisionedThroughputInMibps", ""),
                "Encrypted": fs.get("Encrypted", ""),
                "KmsKeyId": fs.get("KmsKeyId", ""),
                "SizeInBytes": fs.get("SizeInBytes", {}).get("Value", ""),
                "NumberOfMountTargets": fs.get("NumberOfMountTargets", ""),
                "AvailabilityZones": az_list,
                "Subnets": subnet_list,
                "CreationTime": str(fs.get("CreationTime", "") or ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
            })

    return pd.DataFrame(rows)
