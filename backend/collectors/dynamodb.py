"""Amazon DynamoDB collectors.

No legacy collector implementation existed; this module returns an empty DataFrame so the
service wiring remains consistent. Add inventory logic here when requirements arise.
"""
from __future__ import annotations

import pandas as pd


def collect_dynamodb(session, cost_map):
    return pd.DataFrame([])
