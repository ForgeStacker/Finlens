"""Amazon Comprehend collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_comprehend(session, cost_map) -> pd.DataFrame:
    client = session.client("comprehend", region_name=REGION)
    rows = []

    # Document Classifiers
    classifiers = safe_call(
        lambda: client.list_document_classifiers().get("DocumentClassifierPropertiesList", []), []
    )
    for c in classifiers or []:
        rows.append({
            "ResourceType": "DocumentClassifier",
            "ARN": c.get("DocumentClassifierArn", ""),
            "Name": (c.get("DocumentClassifierArn") or "").split("/")[-1],
            "LanguageCode": c.get("LanguageCode", ""),
            "Status": c.get("Status", ""),
            "DocumentType": c.get("DocumentClassifierInputDataConfig", {}).get("DataFormat", ""),
            "SubmitTime": str(c.get("SubmitTime", "") or ""),
            "EndTime": str(c.get("EndTime", "") or ""),
        })

    # Entity Recognizers
    recognizers = safe_call(
        lambda: client.list_entity_recognizers().get("EntityRecognizerPropertiesList", []), []
    )
    for r in recognizers or []:
        rows.append({
            "ResourceType": "EntityRecognizer",
            "ARN": r.get("EntityRecognizerArn", ""),
            "Name": (r.get("EntityRecognizerArn") or "").split("/")[-1],
            "LanguageCode": r.get("LanguageCode", ""),
            "Status": r.get("Status", ""),
            "DocumentType": "",
            "SubmitTime": str(r.get("SubmitTime", "") or ""),
            "EndTime": str(r.get("EndTime", "") or ""),
        })

    # Endpoints
    endpoints = safe_call(
        lambda: client.list_endpoints().get("EndpointPropertiesList", []), []
    )
    for e in endpoints or []:
        rows.append({
            "ResourceType": "Endpoint",
            "ARN": e.get("EndpointArn", ""),
            "Name": (e.get("EndpointArn") or "").split("/")[-1],
            "LanguageCode": "",
            "Status": e.get("Status", ""),
            "DocumentType": "",
            "SubmitTime": str(e.get("CreationTime", "") or ""),
            "EndTime": "",
        })

    return pd.DataFrame(rows)
