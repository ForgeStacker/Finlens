"""Amazon Machine Image (AMI) collectors — owned images only."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_ami(session, cost_map) -> pd.DataFrame:
    client = session.client("ec2", region_name=REGION)
    rows = []

    images = safe_call(
        lambda: client.describe_images(Owners=["self"]).get("Images", []), []
    )
    for img in images or []:
        tags = {t["Key"]: t["Value"] for t in (img.get("Tags") or [])}
        rows.append({
            "ImageId": img.get("ImageId", ""),
            "Name": img.get("Name", ""),
            "Description": img.get("Description", ""),
            "OwnerId": img.get("OwnerId", ""),
            "State": img.get("State", ""),
            "Architecture": img.get("Architecture", ""),
            "Platform": img.get("Platform", "Linux"),
            "VirtualizationType": img.get("VirtualizationType", ""),
            "RootDeviceType": img.get("RootDeviceType", ""),
            "EnaSupport": img.get("EnaSupport", ""),
            "Public": img.get("Public", ""),
            "CreationDate": img.get("CreationDate", ""),
            "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
        })

    return pd.DataFrame(rows)
