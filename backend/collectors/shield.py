"""AWS Shield collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_shield(session, cost_map) -> pd.DataFrame:
    # Shield is global (us-east-1)
    client = session.client("shield", region_name="us-east-1")
    rows = []

    # Check subscription
    subscription = safe_call(lambda: client.describe_subscription().get("Subscription", {}), {})
    if subscription:
        rows.append({
            "ResourceType": "Subscription",
            "ResourceArn": "global",
            "ResourceName": "Shield Subscription",
            "ProtectionId": "",
            "SubscriptionState": subscription.get("SubscriptionState", ""),
            "StartTime": str(subscription.get("StartTime", "") or ""),
            "EndTime": str(subscription.get("EndTime", "") or ""),
            "AutoRenew": subscription.get("AutoRenew", ""),
            "ProactiveSupportStatus": subscription.get("ProactiveEngagementStatus", ""),
        })

    # Protections
    paginator = client.get_paginator("list_protections")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for prot in page.get("Protections", []):
            rows.append({
                "ResourceType": "Protection",
                "ResourceArn": prot.get("ResourceArn", ""),
                "ResourceName": prot.get("Name", ""),
                "ProtectionId": prot.get("Id", ""),
                "SubscriptionState": "",
                "StartTime": "",
                "EndTime": "",
                "AutoRenew": "",
                "ProactiveSupportStatus": "",
            })

    return pd.DataFrame(rows)
