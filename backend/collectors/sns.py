"""Amazon SNS collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_sns(session, cost_map):
    sns = session.client("sns", region_name=REGION)
    rows = []
    topics = safe_call(lambda: sns.list_topics().get("Topics", []), [])
    for topic in topics or []:
        arn = topic.get("TopicArn")
        name = arn.split(":")[-1] if arn else ""
        attrs = safe_call(lambda a=arn: sns.get_topic_attributes(TopicArn=a).get("Attributes", {}), {}) if arn else {}
        display_name = attrs.get("DisplayName", "")
        topic_type = "FIFO" if name.lower().endswith(".fifo") else "Standard"
        subscriptions = safe_call(lambda: sns.list_subscriptions_by_topic(TopicArn=arn).get("Subscriptions", []), [])
        subscription_entries = []
        for subscription in subscriptions or []:
            endpoint = subscription.get("Endpoint")
            protocol = subscription.get("Protocol") or ""
            if endpoint:
                entry = f"{protocol}: {endpoint}" if protocol else endpoint
                subscription_entries.append(entry)
        rows.append(
            {
                "Name": name,
                "DisplayName": display_name,
                "Type": topic_type,
                "Subscriptions": "\n".join(subscription_entries),
            }
        )
    return pd.DataFrame(rows)
