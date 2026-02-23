"""AWS Systems Manager (SSM) collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_ssm(session, cost_map) -> pd.DataFrame:
    client = session.client("ssm", region_name=REGION)
    rows = []

    # Managed instances
    paginator_instances = client.get_paginator("describe_instance_information")
    instances = []
    for page in safe_call(lambda: list(paginator_instances.paginate()), []) or []:
        instances.extend(page.get("InstanceInformationList", []))

    for inst in instances:
        rows.append({
            "ResourceType": "ManagedInstance",
            "ResourceId": inst.get("InstanceId", ""),
            "Name": inst.get("ComputerName", ""),
            "PlatformName": inst.get("PlatformName", ""),
            "PlatformVersion": inst.get("PlatformVersion", ""),
            "PlatformType": inst.get("PlatformType", ""),
            "AgentVersion": inst.get("AgentVersion", ""),
            "PingStatus": inst.get("PingStatus", ""),
            "AssociationStatus": inst.get("AssociationStatus", ""),
            "IPAddress": inst.get("IPAddress", ""),
            "LastPingDateTime": str(inst.get("LastPingDateTime", "") or ""),
            "RegistrationDate": str(inst.get("RegistrationDate", "") or ""),
        })

    # Parameter Store — count only (listing values would be too large)
    param_resp = safe_call(
        lambda: client.get_parameters_by_path(Path="/", Recursive=True, MaxResults=10), {}
    )
    param_count = len(param_resp.get("Parameters", [])) if param_resp else 0
    if param_count:
        rows.append({
            "ResourceType": "ParameterStore",
            "ResourceId": "summary",
            "Name": "Parameter count (first 10 shown)",
            "PlatformName": "",
            "PlatformVersion": "",
            "PlatformType": "",
            "AgentVersion": "",
            "PingStatus": "",
            "AssociationStatus": "",
            "IPAddress": "",
            "LastPingDateTime": "",
            "RegistrationDate": f"Count >= {param_count}",
        })

    return pd.DataFrame(rows)
