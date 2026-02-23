"""Amazon QuickSight collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_quicksight(session, cost_map) -> pd.DataFrame:
    # QuickSight requires an AWS account ID
    sts = session.client("sts")
    account_id = safe_call(lambda: sts.get_caller_identity().get("Account", ""), "")
    if not account_id:
        return pd.DataFrame()

    client = session.client("quicksight", region_name=REGION)
    rows = []

    # Dashboards
    dashboards = safe_call(
        lambda: client.list_dashboards(AwsAccountId=account_id).get("DashboardSummaryList", []), []
    )
    for d in dashboards or []:
        rows.append({
            "ResourceType": "Dashboard",
            "ResourceId": d.get("DashboardId", ""),
            "Name": d.get("Name", ""),
            "ARN": d.get("Arn", ""),
            "PublishedVersion": d.get("PublishedVersionNumber", ""),
            "LastUpdatedTime": str(d.get("LastUpdatedTime", "") or ""),
            "CreatedTime": str(d.get("CreatedTime", "") or ""),
        })

    # Datasets
    datasets = safe_call(
        lambda: client.list_data_sets(AwsAccountId=account_id).get("DataSetSummaries", []), []
    )
    for ds in datasets or []:
        rows.append({
            "ResourceType": "DataSet",
            "ResourceId": ds.get("DataSetId", ""),
            "Name": ds.get("Name", ""),
            "ARN": ds.get("Arn", ""),
            "PublishedVersion": "",
            "LastUpdatedTime": str(ds.get("LastUpdatedTime", "") or ""),
            "CreatedTime": str(ds.get("CreatedTime", "") or ""),
        })

    return pd.DataFrame(rows)
