"""Amazon SQS collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_sqs(session, cost_map):
    sqs = session.client("sqs", region_name=REGION)
    rows = []
    queue_urls = safe_call(lambda: sqs.list_queues().get("QueueUrls", []), [])
    for url in queue_urls or []:
        attrs = safe_call(lambda: sqs.get_queue_attributes(QueueUrl=url, AttributeNames=["All"]).get("Attributes", {}), {})
        name = url.split("/")[-1]
        fifo = attrs.get("FifoQueue", "false").lower() == "true"
        
        # Message Retention Period
        retention_seconds = attrs.get("MessageRetentionPeriod")
        if retention_seconds:
            days = int(retention_seconds) / 86400
            retention_days = int(days) if float(days).is_integer() else round(days, 2)
        else:
            retention_days = ""
        
        # Maximum Message Size (in bytes, convert to KB for readability)
        max_msg_size = attrs.get("MaximumMessageSize", "")
        if max_msg_size:
            max_msg_size_kb = int(max_msg_size) / 1024
            max_msg_size = int(max_msg_size_kb) if float(max_msg_size_kb).is_integer() else round(max_msg_size_kb, 2)
        
        # Visibility Timeout (in seconds)
        visibility_timeout = attrs.get("VisibilityTimeout", "")
        
        # Delivery Delay (in seconds)
        delay_seconds = attrs.get("DelaySeconds", "")
        
        # Receive Message Wait Time (in seconds)
        receive_wait_time = attrs.get("ReceiveMessageWaitTimeSeconds", "")
        
        rows.append(
            {
                "QueueName": name,
                "Type": "FIFO" if fifo else "Standard",
                "MaximumMessageSize_KB": max_msg_size,
                "MessageRetentionPeriod_Days": retention_days,
                "VisibilityTimeout_Seconds": visibility_timeout,
                "DeliveryDelay_Seconds": delay_seconds,
                "ReceiveMessageWaitTime_Seconds": receive_wait_time,
            }
        )
    return pd.DataFrame(rows)
