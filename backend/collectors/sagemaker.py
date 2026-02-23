"""Amazon SageMaker collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def _list_all(fetch_page, items_key: str) -> list[dict]:
    items: list[dict] = []
    token = None
    while True:
        kwargs = {"MaxResults": 100}
        if token:
            kwargs["NextToken"] = token
        page = safe_call(lambda: fetch_page(**kwargs), {}) or {}
        page_items = page.get(items_key, []) if isinstance(page, dict) else []
        if page_items:
            items.extend(page_items)
        token = page.get("NextToken") if isinstance(page, dict) else None
        if not token:
            break
    return items


def collect_sagemaker(session, cost_map):
    sm = session.client("sagemaker", region_name=REGION)
    rows: list[dict] = []

    # Notebook Instances
    notebooks = _list_all(sm.list_notebook_instances, "NotebookInstances")
    for item in notebooks:
        rows.append(
            {
                "ResourceType": "NotebookInstance",
                "Name": item.get("NotebookInstanceName"),
                "ARN": item.get("NotebookInstanceArn"),
                "Status": item.get("NotebookInstanceStatus"),
                "InstanceType": item.get("InstanceType"),
                "Url": item.get("Url"),
                "CreationTime": item.get("CreationTime"),
                "LastModifiedTime": item.get("LastModifiedTime"),
            }
        )

    # Endpoints
    endpoints = _list_all(sm.list_endpoints, "Endpoints")
    for item in endpoints:
        endpoint_name = item.get("EndpointName")
        endpoint_details = safe_call(
            lambda: sm.describe_endpoint(EndpointName=endpoint_name), {}
        )
        rows.append(
            {
                "ResourceType": "Endpoint",
                "Name": endpoint_name,
                "ARN": item.get("EndpointArn") or endpoint_details.get("EndpointArn"),
                "Status": item.get("EndpointStatus") or endpoint_details.get("EndpointStatus"),
                "EndpointConfig": item.get("EndpointConfigName") or endpoint_details.get("EndpointConfigName"),
                "CreationTime": item.get("CreationTime") or endpoint_details.get("CreationTime"),
                "LastModifiedTime": item.get("LastModifiedTime") or endpoint_details.get("LastModifiedTime"),
            }
        )

    # Models
    models = _list_all(sm.list_models, "Models")
    for item in models:
        rows.append(
            {
                "ResourceType": "Model",
                "Name": item.get("ModelName"),
                "ARN": item.get("ModelArn"),
                "CreationTime": item.get("CreationTime"),
            }
        )

    # Studio Domains
    domains = _list_all(sm.list_domains, "Domains")
    for item in domains:
        rows.append(
            {
                "ResourceType": "StudioDomain",
                "Name": item.get("DomainName") or item.get("DomainId"),
                "ARN": item.get("DomainArn"),
                "Status": item.get("Status"),
                "AuthMode": item.get("AuthMode"),
                "CreationTime": item.get("CreationTime"),
                "LastModifiedTime": item.get("LastModifiedTime"),
            }
        )

    return pd.DataFrame(rows)
