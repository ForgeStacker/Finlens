"""Amazon EBS Volume collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_ebs(session, cost_map) -> pd.DataFrame:
    client = session.client("ec2", region_name=REGION)
    rows = []

    paginator = client.get_paginator("describe_volumes")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for vol in page.get("Volumes", []):
            tags = {t["Key"]: t["Value"] for t in (vol.get("Tags") or [])}
            attachments = vol.get("Attachments", [])
            attached_to = ", ".join(a.get("InstanceId", "") for a in attachments)
            attach_state = ", ".join(a.get("State", "") for a in attachments)
            rows.append({
                "VolumeId": vol.get("VolumeId", ""),
                "Name": tags.get("Name", ""),
                "VolumeType": vol.get("VolumeType", ""),
                "Size(GiB)": vol.get("Size", ""),
                "Iops": vol.get("Iops", ""),
                "Throughput": vol.get("Throughput", ""),
                "State": vol.get("State", ""),
                "Encrypted": vol.get("Encrypted", ""),
                "KmsKeyId": vol.get("KmsKeyId", ""),
                "AvailabilityZone": vol.get("AvailabilityZone", ""),
                "MultiAttachEnabled": vol.get("MultiAttachEnabled", ""),
                "AttachedTo": attached_to,
                "AttachmentState": attach_state,
                "SnapshotId": vol.get("SnapshotId", ""),
                "CreateTime": str(vol.get("CreateTime", "") or ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
            })

    return pd.DataFrame(rows)
