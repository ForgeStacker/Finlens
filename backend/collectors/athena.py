"""Amazon Athena collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_athena(session, cost_map) -> pd.DataFrame:
    client = session.client("athena", region_name=REGION)
    rows = []

    workgroups = safe_call(lambda: client.list_work_groups().get("WorkGroups", []), [])
    for wg in workgroups or []:
        name = wg.get("Name", "")
        detail = safe_call(lambda n=name: client.get_work_group(WorkGroup=n).get("WorkGroup", {}), {})
        cfg = detail.get("Configuration", {})
        result_cfg = cfg.get("ResultConfiguration", {})
        rows.append({
            "WorkGroupName": name,
            "State": wg.get("State", ""),
            "Description": wg.get("Description", ""),
            "ResultLocation": result_cfg.get("OutputLocation", ""),
            "EncryptionOption": result_cfg.get("EncryptionConfiguration", {}).get("EncryptionOption", ""),
            "EnforceWorkGroupConfig": cfg.get("EnforceWorkGroupConfiguration", ""),
            "PublishMetrics": cfg.get("PublishCloudWatchMetricsEnabled", ""),
            "BytesScannedCutoff": cfg.get("BytesScannedCutoffPerQuery", ""),
            "CreationTime": str(detail.get("CreationTime", "") or ""),
        })

    return pd.DataFrame(rows)
