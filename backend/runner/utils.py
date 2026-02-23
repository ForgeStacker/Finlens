"""Shared helper routines for the runner package."""
from __future__ import annotations

import json
from typing import Any

import pandas as pd


def is_cluster_column(name: Any) -> bool:
    """Return True when a column name refers to cluster metadata."""
    if not name:
        return False
    return "cluster" in str(name).lower()


def format_cell_value(value: Any) -> str:
    """Normalize arbitrary values for human-readable Excel output."""
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        if isinstance(value, bool):
            return "Enabled" if value else "Disabled"
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        if isinstance(value, dict):
            return "\n".join(f"{k}: {value[k]}" for k in value)
        if isinstance(value, str):
            text = value.strip()
            if ", " in text:
                if all(segment.strip().startswith("subnet-") for segment in text.replace(" ", "").split(",")):
                    return "\n".join(segment.strip() for segment in text.split(","))
            if text.startswith("{") or text.startswith("["):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        return "\n".join(str(item) for item in parsed)
                    if isinstance(parsed, dict):
                        return "\n".join(f"{k}: {parsed[k]}" for k in parsed)
                    return json.dumps(parsed, indent=2)
                except Exception:
                    return text.replace("},{", "},\n{")
            return text.replace(", ", "\n")
        return str(value)
    except Exception:
        return str(value)


def normalize_for_csv(service: str, df: pd.DataFrame | None, cost_map: dict[str, Any]) -> list[dict[str, Any]]:
    """Return normalized rows for flat CSV output."""
    rows: list[dict[str, Any]] = []
    if df is None or df.empty:
        return rows
    for _, row in df.iterrows():
        data = row.to_dict()
        resource_id = (
            data.get("ARN")
            or data.get("ClusterARN")
            or data.get("DBInstanceIdentifier")
            or data.get("InstanceId")
            or data.get("LoadBalancerArn")
            or data.get("RepositoryArn")
            or data.get("BucketName")
            or data.get("APIId")
            or data.get("FunctionName")
            or data.get("DBClusterIdentifier")
            or data.get("CacheClusterId")
            or data.get("VpcId")
            or data.get("Id")
            or ""
        )
        name = (
            data.get("Name")
            or data.get("ClusterName")
            or data.get("DBInstanceIdentifier")
            or data.get("InstanceId")
            or data.get("LoadBalancerName")
            or data.get("RepositoryName")
            or data.get("BucketName")
            or data.get("QueueName")
            or data.get("APIName")
            or data.get("FunctionName")
            or data.get("CacheClusterId")
            or data.get("VpcId")
            or ""
        )
        ignore = {
            "ARN",
            "ClusterARN",
            "DBInstanceIdentifier",
            "InstanceId",
            "LoadBalancerArn",
            "RepositoryArn",
            "BucketName",
            "APIId",
            "FunctionName",
            "DBClusterIdentifier",
            "CacheClusterId",
            "VpcId",
            "Name",
            "ClusterName",
            "RepositoryName",
        }
        details: list[str] = []
        for key, value in data.items():
            if key in ignore:
                continue
            try:
                if isinstance(value, (list, tuple, set)):
                    is_na = all(pd.isna(item) for item in value)
                    is_empty = all((item == "" or item is None) for item in value)
                elif hasattr(value, "all") and callable(getattr(value, "all", None)):
                    all_value = value.all()
                    is_na = pd.isna(all_value)
                    is_empty = all_value in ("", None)
                else:
                    is_na = pd.isna(value)
                    is_empty = value in ("", None)
            except Exception:
                is_na = False
                is_empty = False
            if is_na or is_empty:
                continue
            details.append(f"{key}={value}")
        rows.append(
            {
                "Service": service,
                "ResourceType": data.get("ResourceType", ""),
                "ResourceId": resource_id,
                "Name": name,
                "KeyDetails": ", ".join(details),
                "EstimatedCostUSD_30d": data.get("EstimatedCostUSD_30d", 0.0),
            }
        )
    return rows
