"""VPC Peering Connection collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_vpcpeering(session, cost_map) -> pd.DataFrame:
    client = session.client("ec2", region_name=REGION)
    rows = []

    paginator = client.get_paginator("describe_vpc_peering_connections")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for conn in page.get("VpcPeeringConnections", []):
            tags = {t["Key"]: t["Value"] for t in (conn.get("Tags") or [])}
            req = conn.get("RequesterVpcInfo", {})
            acc = conn.get("AccepterVpcInfo", {})
            rows.append({
                "VpcPeeringConnectionId": conn.get("VpcPeeringConnectionId", ""),
                "Status": conn.get("Status", {}).get("Code", ""),
                "StatusMessage": conn.get("Status", {}).get("Message", ""),
                "RequesterVpcId": req.get("VpcId", ""),
                "RequesterOwnerId": req.get("OwnerId", ""),
                "RequesterRegion": req.get("Region", ""),
                "RequesterCidrBlock": req.get("CidrBlock", ""),
                "AccepterVpcId": acc.get("VpcId", ""),
                "AccepterOwnerId": acc.get("OwnerId", ""),
                "AccepterRegion": acc.get("Region", ""),
                "AccepterCidrBlock": acc.get("CidrBlock", ""),
                "ExpirationTime": str(conn.get("ExpirationTime", "") or ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
            })

    return pd.DataFrame(rows)
