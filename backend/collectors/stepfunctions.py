"""AWS Step Functions collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_stepfunctions(session, cost_map) -> pd.DataFrame:
    client = session.client("stepfunctions", region_name=REGION)
    rows = []

    paginator = client.get_paginator("list_state_machines")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for sm in page.get("stateMachines", []):
            arn = sm.get("stateMachineArn", "")
            detail = safe_call(lambda a=arn: client.describe_state_machine(stateMachineArn=a), {})
            rows.append({
                "StateMachineName": sm.get("name", ""),
                "StateMachineArn": arn,
                "Type": sm.get("type", ""),
                "Status": detail.get("status", ""),
                "RoleArn": detail.get("roleArn", ""),
                "LoggingLevel": detail.get("loggingConfiguration", {}).get("level", ""),
                "TracingEnabled": detail.get("tracingConfiguration", {}).get("enabled", ""),
                "CreationDate": str(sm.get("creationDate", "") or ""),
            })

    return pd.DataFrame(rows)
