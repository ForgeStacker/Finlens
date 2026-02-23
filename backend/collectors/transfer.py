"""AWS Transfer Family collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_transfer(session, cost_map) -> pd.DataFrame:
    client = session.client("transfer", region_name=REGION)
    rows = []

    paginator = client.get_paginator("list_servers")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for server in page.get("Servers", []):
            server_id = server.get("ServerId", "")
            detail = safe_call(
                lambda sid=server_id: client.describe_server(ServerId=sid).get("Server", {}), {}
            )
            tags = {t["Key"]: t["Value"] for t in (detail.get("Tags") or [])}
            rows.append({
                "ServerId": server_id,
                "Arn": server.get("Arn", ""),
                "Domain": server.get("Domain", ""),
                "State": server.get("State", ""),
                "EndpointType": detail.get("EndpointType", ""),
                "Protocols": ", ".join(detail.get("Protocols", [])),
                "IdentityProviderType": detail.get("IdentityProviderType", ""),
                "LoggingRole": detail.get("LoggingRole", ""),
                "UserCount": server.get("UserCount", ""),
                "CreatedDateTime": str(server.get("CreatedDateTime", "") or ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
            })

    return pd.DataFrame(rows)
