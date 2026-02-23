"""AWS Secrets Manager collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_secrets(session, cost_map):
    sm = session.client("secretsmanager", region_name=REGION)
    rows = []
    paginator = sm.get_paginator("list_secrets")
    for page in safe_call(lambda: paginator.paginate(), []):
        for secret in page.get("SecretList", []):
            rotation = secret.get("RotationEnabled")
            rotation_status = "Enabled" if rotation is True else "Disabled"
            rows.append(
                {
                    "Name": secret.get("Name"),
                    "Description": secret.get("Description", ""),
                    "RotationEnabled": rotation_status,
                }
            )
    df = pd.DataFrame(rows)
    for column in ["Name", "Description", "RotationEnabled"]:
        if column not in df.columns:
            df[column] = ""
    return df[["Name", "Description", "RotationEnabled"]]
