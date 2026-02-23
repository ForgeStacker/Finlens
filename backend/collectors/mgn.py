"""AWS Application Migration Service (MGN) collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_mgn(session, cost_map) -> pd.DataFrame:
    client = session.client("mgn", region_name=REGION)
    rows = []

    paginator = client.get_paginator("describe_source_servers")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for server in page.get("items", []):
            lm = server.get("lifeCycle", {})
            data_rep = server.get("dataReplicationInfo", {})
            rows.append({
                "SourceServerID": server.get("sourceServerID", ""),
                "ARN": server.get("arn", ""),
                "State": lm.get("state", ""),
                "LastTest": str(lm.get("lastTest", {}).get("finalized", {}).get("apiCallDateTime", "") or ""),
                "LastCutover": str(lm.get("lastCutover", {}).get("finalized", {}).get("apiCallDateTime", "") or ""),
                "ReplicationState": data_rep.get("dataReplicationState", ""),
                "LagDuration": data_rep.get("lagDuration", ""),
                "EtaDateTime": str(data_rep.get("etaDateTime", "") or ""),
                "Hostname": server.get("sourceProperties", {}).get("networkInterfaces", [{}])[0].get("ipAddresses", [""])[0] if server.get("sourceProperties", {}).get("networkInterfaces") else "",
                "IsArchived": server.get("isArchived", ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in (server.get("tags") or {}).items()),
            })

    return pd.DataFrame(rows)
