"""Amazon Rekognition collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_rekognition(session, cost_map) -> pd.DataFrame:
    client = session.client("rekognition", region_name=REGION)
    rows = []

    # Collections
    collection_ids = safe_call(
        lambda: client.list_collections().get("CollectionIds", []), []
    )
    for cid in collection_ids or []:
        desc = safe_call(lambda c=cid: client.describe_collection(CollectionId=c), {})
        rows.append({
            "ResourceType": "Collection",
            "ResourceId": cid,
            "ARN": desc.get("CollectionARN", ""),
            "FaceCount": desc.get("FaceCount", ""),
            "FaceModelVersion": desc.get("FaceModelVersion", ""),
            "Status": "Active",
            "CreationTimestamp": str(desc.get("CreationTimestamp", "") or ""),
        })

    # Stream Processors
    processors = safe_call(
        lambda: client.list_stream_processors().get("StreamProcessors", []), []
    )
    for sp in processors or []:
        name = sp.get("Name", "")
        detail = safe_call(lambda n=name: client.describe_stream_processor(Name=n), {})
        rows.append({
            "ResourceType": "StreamProcessor",
            "ResourceId": name,
            "ARN": detail.get("StreamProcessorArn", ""),
            "FaceCount": "",
            "FaceModelVersion": "",
            "Status": sp.get("Status", ""),
            "CreationTimestamp": str(detail.get("CreationTimestamp", "") or ""),
        })

    return pd.DataFrame(rows)
