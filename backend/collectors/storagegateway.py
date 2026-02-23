"""AWS Storage Gateway collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_storagegateway(session, cost_map) -> pd.DataFrame:
    client = session.client("storagegateway", region_name=REGION)
    rows = []

    gateways = safe_call(lambda: client.list_gateways().get("Gateways", []), [])
    for gw in gateways or []:
        gw_arn = gw.get("GatewayARN", "")
        detail = safe_call(
            lambda a=gw_arn: client.describe_gateway_information(GatewayARN=a), {}
        )
        tags = {t["Key"]: t["Value"] for t in (detail.get("Tags") or [])}
        rows.append({
            "GatewayId": gw.get("GatewayId", ""),
            "GatewayARN": gw_arn,
            "GatewayName": gw.get("GatewayName", ""),
            "GatewayType": gw.get("GatewayType", ""),
            "GatewayState": detail.get("GatewayState", ""),
            "GatewayTimezone": detail.get("GatewayTimezone", ""),
            "Ec2InstanceId": detail.get("Ec2InstanceId", ""),
            "Ec2InstanceRegion": detail.get("Ec2InstanceRegion", ""),
            "HostEnvironment": detail.get("HostEnvironment", ""),
            "LastSoftwareUpdate": detail.get("LastSoftwareUpdate", ""),
            "SoftwareUpdatesEndDate": detail.get("SoftwareUpdatesEndDate", ""),
            "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
        })

    return pd.DataFrame(rows)
