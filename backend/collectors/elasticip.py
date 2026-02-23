"""Elastic IP collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_elasticip(session, cost_map) -> pd.DataFrame:
    client = session.client("ec2", region_name=REGION)
    rows = []

    addresses = safe_call(
        lambda: client.describe_addresses().get("Addresses", []), []
    )
    for addr in addresses or []:
        tags = {t["Key"]: t["Value"] for t in (addr.get("Tags") or [])}
        rows.append({
            "PublicIp": addr.get("PublicIp", ""),
            "AllocationId": addr.get("AllocationId", ""),
            "AssociationId": addr.get("AssociationId", ""),
            "InstanceId": addr.get("InstanceId", ""),
            "PrivateIpAddress": addr.get("PrivateIpAddress", ""),
            "NetworkInterfaceId": addr.get("NetworkInterfaceId", ""),
            "NetworkInterfaceOwnerId": addr.get("NetworkInterfaceOwnerId", ""),
            "Domain": addr.get("Domain", ""),
            "PublicIpv4Pool": addr.get("PublicIpv4Pool", ""),
            "NetworkBorderGroup": addr.get("NetworkBorderGroup", ""),
            "CustomerOwnedIp": addr.get("CustomerOwnedIp", ""),
            "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
        })

    return pd.DataFrame(rows)
