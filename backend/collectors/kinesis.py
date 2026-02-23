"""Amazon Kinesis collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_kinesis(session, cost_map):
    client = session.client("kinesis", region_name=REGION)
    rows = []
    streams = safe_call(lambda: client.list_streams().get("StreamNames", []), [])
    for stream_name in streams or []:
        desc = safe_call(lambda: client.describe_stream(StreamName=stream_name).get("StreamDescription", {}), {})
        stream_mode_details = desc.get("StreamModeDetails", {})
        rows.append({
            "StreamName": stream_name,
            "Status": desc.get("StreamStatus"),
            "DataRetentionPeriodHours": desc.get("RetentionPeriodHours"),
            "CapacityMode": stream_mode_details.get("StreamMode"),
            "MaximumRecordSize": "1 MB",
        })
    return pd.DataFrame(rows)
