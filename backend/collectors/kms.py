"""AWS KMS collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_kms(session, cost_map):
    kms = session.client("kms", region_name=REGION)
    rows = []
    keys = safe_call(lambda: kms.list_keys().get("Keys", []), [])
    for key in keys or []:
        meta = safe_call(lambda: kms.describe_key(KeyId=key.get("KeyId")).get("KeyMetadata", {}), {})
        rows.append({
            "KeyId": meta.get("KeyId"),
            "State": meta.get("KeyState"),
            "Manager": meta.get("KeyManager"),
        })
    return pd.DataFrame(rows)
