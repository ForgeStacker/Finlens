"""Shared helpers for AWS sessions, error handling, and formatting."""
from __future__ import annotations

import datetime
import json
import os
from typing import Any, Callable, Iterable, Optional

import boto3
from botocore.exceptions import ClientError, ProfileNotFound

from config import REGION, safe_call


def ensure_output_dirs(*paths: str) -> None:
    for path in paths:
        os.makedirs(path, exist_ok=True)


def sanitize_filename(name: Optional[str]) -> str:
    if not name:
        return "sheet"
    invalid_chars = '<>:"/\\|?*'
    sanitized = "".join("_" if c in invalid_chars else c for c in name).strip()
    return sanitized or "sheet"


def get_session(profile: str):
    try:
        return boto3.Session(profile_name=profile, region_name=REGION)
    except ProfileNotFound:
        return None


def get_instance_type_specs(ec2_client, instance_type: str) -> dict[str, Optional[float]]:
    cache_file = os.path.join(os.path.dirname(__file__), "instance_types.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            for item in data.get("InstanceTypes", []):
                if item.get("InstanceType") == instance_type:
                    return {
                        "vcpus": item.get("VCpuInfo", {}).get("DefaultVCpus"),
                        "memory_mb": item.get("MemoryInfo", {}).get("SizeInMiB"),
                    }
        except Exception:
            pass
    try:
        resp = ec2_client.describe_instance_types(InstanceTypes=[instance_type])
        details = resp.get("InstanceTypes", [None])[0] or {}
        return {
            "vcpus": details.get("VCpuInfo", {}).get("DefaultVCpus"),
            "memory_mb": details.get("MemoryInfo", {}).get("SizeInMiB"),
        }
    except Exception:
        return {"vcpus": None, "memory_mb": None}


def sum_s3_bucket_size(s3_client, bucket_name: str) -> tuple[int, int]:
    total_bytes = 0
    total_count = 0
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        for page_index, page in enumerate(paginator.paginate(Bucket=bucket_name)):
            if page_index >= 10:
                break
            for obj in page.get("Contents", []) or []:
                total_bytes += obj.get("Size", 0)
                total_count += 1
    except ClientError as exc:
        print(f"  ⚠ S3 access error for {bucket_name}: {exc}")
    except Exception as exc:
        print(f"  ⚠ Unexpected S3 error for {bucket_name}: {exc}")
    return total_bytes, total_count


def format_bytes_to_gb(bytes_val: Optional[int]) -> str:
    if bytes_val is None:
        return ""
    return str(round(bytes_val / (1024.0**3), 3))


def get_disk_size_for_nodegroup(nodegroup: dict, _ec2_client=None) -> Optional[int]:
    return nodegroup.get("diskSize")
