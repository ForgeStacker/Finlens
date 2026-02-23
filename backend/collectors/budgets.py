"""AWS Budgets collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_budgets(session, cost_map) -> pd.DataFrame:
    sts = session.client("sts")
    account_id = safe_call(lambda: sts.get_caller_identity().get("Account", ""), "")
    if not account_id:
        return pd.DataFrame()

    client = session.client("budgets", region_name="us-east-1")
    rows = []

    budgets = safe_call(
        lambda: client.describe_budgets(AccountId=account_id).get("Budgets", []), []
    )
    for b in budgets or []:
        limit = b.get("BudgetLimit", {})
        actual = b.get("CalculatedSpend", {}).get("ActualSpend", {})
        forecasted = b.get("CalculatedSpend", {}).get("ForecastedSpend", {})
        time_period = b.get("TimePeriod", {})
        rows.append({
            "BudgetName": b.get("BudgetName", ""),
            "BudgetType": b.get("BudgetType", ""),
            "TimeUnit": b.get("TimeUnit", ""),
            "LimitAmount": limit.get("Amount", ""),
            "LimitUnit": limit.get("Unit", ""),
            "ActualSpend": actual.get("Amount", ""),
            "ForecastedSpend": forecasted.get("Amount", ""),
            "StartDate": str(time_period.get("Start", "") or ""),
            "EndDate": str(time_period.get("End", "") or ""),
        })

    return pd.DataFrame(rows)
