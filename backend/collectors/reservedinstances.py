"""AWS Reserved Instances collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_reservedinstances(session, cost_map) -> pd.DataFrame:
    client = session.client("ec2", region_name=REGION)
    rows = []

    ris = safe_call(
        lambda: client.describe_reserved_instances(
            Filters=[{"Name": "state", "Values": ["active"]}]
        ).get("ReservedInstances", []),
        [],
    )
    for ri in ris or []:
        rows.append({
            "ReservedInstancesId": ri.get("ReservedInstancesId", ""),
            "InstanceType": ri.get("InstanceType", ""),
            "AvailabilityZone": ri.get("AvailabilityZone", ""),
            "Scope": ri.get("Scope", ""),
            "State": ri.get("State", ""),
            "InstanceCount": ri.get("InstanceCount", ""),
            "ProductDescription": ri.get("ProductDescription", ""),
            "OfferingClass": ri.get("OfferingClass", ""),
            "OfferingType": ri.get("OfferingType", ""),
            "Duration": ri.get("Duration", ""),
            "FixedPrice": ri.get("FixedPrice", ""),
            "UsagePrice": ri.get("UsagePrice", ""),
            "Start": str(ri.get("Start", "") or ""),
            "End": str(ri.get("End", "") or ""),
        })

    return pd.DataFrame(rows)
