"""AWS Cost Explorer summary collector."""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_costexplorer(session, cost_map) -> pd.DataFrame:
    client = session.client("ce", region_name="us-east-1")
    rows = []

    today = date.today()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()

    resp = safe_call(
        lambda: client.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost", "UsageQuantity"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        ),
        {},
    )
    for period in (resp or {}).get("ResultsByTime", []):
        for grp in period.get("Groups", []):
            service = grp["Keys"][0]
            cost = grp["Metrics"]["UnblendedCost"]["Amount"]
            unit = grp["Metrics"]["UnblendedCost"]["Unit"]
            usage = grp["Metrics"]["UsageQuantity"]["Amount"]
            if float(cost) <= 0:
                continue
            rows.append({
                "Service": service,
                "Month": period.get("TimePeriod", {}).get("Start", ""),
                "CostUSD": round(float(cost), 4),
                "Unit": unit,
                "UsageQuantity": round(float(usage), 4),
            })

    return pd.DataFrame(rows)
