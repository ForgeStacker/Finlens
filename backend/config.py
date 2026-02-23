"""Project-wide constants and shared configuration values."""
from __future__ import annotations

import os
from typing import Any, Callable, List

import boto3

REGION = "ap-south-1"

# Project root = parent of this file's directory (backend/ -> project root)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_BASE_DIR = os.path.join(_PROJECT_ROOT, "Data")

# Legacy aliases kept for any third-party scripts that still import them.
EXCEL_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, "Excel")
CSV_OUTPUT_DIR = os.path.join(OUTPUT_BASE_DIR, "CSV")
COMBINED_EXCEL_PATH = os.path.join(OUTPUT_BASE_DIR, "AWS_SERVICES.xlsx")


def get_account_region_dir(account_name: str, region: str) -> str:
    """Return (and create) the canonical output directory for an account+region.

    Path: ``Data/{account_name}/{region}/``
    """
    from aws_utils import sanitize_filename  # local import to avoid circular
    safe_account = sanitize_filename(account_name.replace(" ", "_"))[:80]
    safe_region = sanitize_filename(region)
    path = os.path.join(OUTPUT_BASE_DIR, safe_account, safe_region)
    os.makedirs(path, exist_ok=True)
    return path

PROFILE_SERVICES: List[str] = [
    "RDS",
    "CloudWatchAlarm",
    "CloudWatchLogs",
    "CloudWatchEvent",
    "Lambda",
    "API Gateway",
    "EC2",
    "IAM",
    "ElastiCache",
    "EKS",
    "ELB",
    "VPC",
    "SQS",
    "Glue",
    "S3",
    "SecretsManager",
    "KMS",
    "ECR",
    "Route53",
    "SNS",
    "DMS",
    "WAF",
    "Kinesis",
    "Kafka",
    "MSK",
    "DynamoDB",
    "SageMaker",
]


def safe_call(fn: Callable[[], Any], default: Any = None) -> Any:
    try:
        return fn()
    except Exception as exc:  # pragma: no cover - diagnostic helper
        print(f"  ⚠ Warning: {type(exc).__name__}: {exc}")
        return default


def get_available_profiles() -> List[str]:
    try:
        session = boto3.Session()
        return session.available_profiles or []
    except Exception:
        return []


def get_account_display_name(profile: str, session=None) -> str:
    try:
        session = session or boto3.Session(profile_name=profile, region_name=REGION)
        iam = session.client("iam")
        aliases: List[str] = safe_call(lambda: iam.list_account_aliases().get("AccountAliases", []), []) or []
        if aliases:
            return aliases[0]
    except Exception:
        pass
    return profile
