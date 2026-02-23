"""CloudWatch-related collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_cloudwatch(session, cost_map):
    cw = session.client("cloudwatch", region_name=REGION)
    rows = []
    alarms = safe_call(lambda: cw.describe_alarms().get("MetricAlarms", []), [])
    for a in alarms or []:
        rows.append({
            "AlarmName": a.get("AlarmName"),
            "MetricName": a.get("MetricName"),
            "Namespace": a.get("Namespace"),
            # Only one alarmgroup per row, no block
            "alarmgroup": a.get("AlarmName"),
            "conditions": a.get("AlarmDescription", ""),
            "statistics": a.get("Statistic", ""),
            "period": a.get("Period", ""),
            "threshold": int(a.get("Threshold")) if a.get("Threshold") is not None else "",
            "identifier": ", ".join([d.get("Value", str(d)) for d in a.get("Dimensions", [])]),
            "action": ", ".join(a.get("AlarmActions", []))
        })
    return pd.DataFrame(rows)


def collect_cloudwatchevent(session, cost_map):
    events = session.client("events", region_name=REGION)
    rows = []
    rules = safe_call(lambda: events.list_rules().get("Rules", []), [])
    for r in rules or []:
        rows.append({
            "RuleName": r.get("Name"),
            "State": r.get("State"),
            "Description": r.get("Description", ""),
            "ScheduleExpression": r.get("ScheduleExpression", "")
        })
    return pd.DataFrame(rows)
