"""AWS Control Tower collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_controltower(session, cost_map) -> pd.DataFrame:
    client = session.client("controltower", region_name=REGION)
    rows = []

    # List landing zones
    landing_zones = safe_call(
        lambda: client.list_landing_zones().get("landingZones", []), []
    )
    for lz in landing_zones or []:
        lz_arn = lz.get("arn", "")
        detail = safe_call(
            lambda a=lz_arn: client.get_landing_zone(landingZoneIdentifier=a).get("landingZone", {}), {}
        )
        rows.append({
            "ResourceType": "LandingZone",
            "ARN": lz_arn,
            "Name": detail.get("manifest", {}).get("governedRegions", [""])[0] if detail else "",
            "Status": detail.get("status", ""),
            "LatestAvailableVersion": detail.get("latestAvailableVersion", ""),
            "DriftStatus": detail.get("driftStatus", {}).get("status", ""),
            "DeployedVersion": detail.get("version", ""),
        })

    # List enabled controls
    paginator = client.get_paginator("list_enabled_controls")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for ctrl in page.get("enabledControls", []):
            rows.append({
                "ResourceType": "EnabledControl",
                "ARN": ctrl.get("arn", ""),
                "Name": ctrl.get("controlIdentifier", ""),
                "Status": ctrl.get("statusSummary", {}).get("status", ""),
                "LatestAvailableVersion": "",
                "DriftStatus": ctrl.get("driftStatusSummary", {}).get("driftStatus", ""),
                "DeployedVersion": "",
            })

    return pd.DataFrame(rows)
