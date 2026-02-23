"""AWS CloudFormation collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_cloudformation(session, cost_map) -> pd.DataFrame:
    client = session.client("cloudformation", region_name=REGION)
    rows = []

    paginator = client.get_paginator("describe_stacks")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for stack in page.get("Stacks", []):
            tags = {t["Key"]: t["Value"] for t in (stack.get("Tags") or [])}
            outputs = ", ".join(
                f"{o.get('OutputKey')}={o.get('OutputValue')}"
                for o in (stack.get("Outputs") or [])
            )
            rows.append({
                "StackName": stack.get("StackName", ""),
                "StackId": stack.get("StackId", ""),
                "StackStatus": stack.get("StackStatus", ""),
                "StatusReason": stack.get("StackStatusReason", ""),
                "Description": stack.get("Description", ""),
                "ParentId": stack.get("ParentId", ""),
                "RootId": stack.get("RootId", ""),
                "DriftStatus": stack.get("DriftInformation", {}).get("StackDriftStatus", ""),
                "DriftCheckTime": str(stack.get("DriftInformation", {}).get("LastCheckTimestamp", "") or ""),
                "DeletionProtection": stack.get("DeletionProtectionEnabled", ""),
                "TerminationProtection": stack.get("EnableTerminationProtection", ""),
                "Capabilities": ", ".join(stack.get("Capabilities", [])),
                "Outputs": outputs,
                "CreationTime": str(stack.get("CreationTime", "") or ""),
                "LastUpdatedTime": str(stack.get("LastUpdatedTime", "") or ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
            })

    return pd.DataFrame(rows)
