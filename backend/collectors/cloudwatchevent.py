"""Amazon EventBridge (CloudWatch Events) collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_cloudwatchevent(session, cost_map):
    events = session.client("events", region_name=REGION)
    rows = []
    rules = safe_call(lambda: events.list_rules().get("Rules", []), [])
    for rule in rules or []:
        rows.append({
            "RuleName": rule.get("Name"),
            "State": rule.get("State"),
            "Description": rule.get("Description", ""),
            "ScheduleExpression": rule.get("ScheduleExpression", ""),
        })
    return pd.DataFrame(rows)
