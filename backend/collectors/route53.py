"""Amazon Route 53 collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call


def collect_route53(session, cost_map):
    r53 = session.client("route53")
    rows = []
    hosted_zones = safe_call(lambda: r53.list_hosted_zones().get("HostedZones", []), [])
    for zone in hosted_zones or []:
        rows.append(
            {
                "HostedZoneId": zone.get("Id"),
                "Name": zone.get("Name"),
                "PrivateZone": zone.get("Config", {}).get("PrivateZone", False),
                "RecordCount": zone.get("ResourceRecordSetCount", 0),
            }
        )
    return pd.DataFrame(rows)
