#!/usr/bin/env python3
"""
FastAPI server to serve AWS inventory data dynamically.
Reads CSV files from Data/CSV/ and serves as JSON API.
"""

import os
import csv
import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    import boto3  # Optional, used for Cost Explorer based monthly cost
except Exception:
    boto3 = None

# Import the collector registry to dynamically discover services
from collectors import COLLECTOR_FUNCTIONS

app = FastAPI(
    title="AWS Inventory API",
    description="API for Maruti Suzuki AWS Multi-Account Resource Inventory",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "Data"              # Data/{account}/{region}/{Service}.csv
# Legacy aliases (kept for backward compat with any tooling that may reference them)
CSV_DIR = DATA_DIR / "CSV"
EXCEL_DIR = DATA_DIR / "Excel"

# Map each canonical service name to its UI category
SERVICE_CATEGORY_MAP: Dict[str, str] = {
    # Compute
    "EC2": "compute", "AMI": "compute", "ECS": "compute",
    "ElasticBeanstalk": "compute", "Lambda": "compute", "ASG": "compute", "EKS": "compute",
    # Database
    "RDS": "database", "DynamoDB": "database", "ElastiCache": "database",
    "DocumentDB": "database", "Neptune": "database", "Redshift": "database",
    # Storage
    "S3": "storage", "EBS": "storage", "EFS": "storage",
    "Snapshots": "storage", "ECR": "storage", "StorageGateway": "storage",
    # Networking
    "VPC": "networking", "ELB": "networking", "Route53": "networking",
    "CloudFront": "networking", "ElasticIP": "networking", "VPCPeering": "networking",
    # Integration
    "SQS": "integration", "SNS": "integration", "API Gateway": "integration",
    "StepFunctions": "integration", "SES": "integration",
    "Kinesis": "integration", "MSK": "integration", "Kafka": "integration",
    # Security
    "IAM": "security", "KMS": "security", "SecretsManager": "security",
    "ACM": "security", "WAF": "security", "Shield": "security",
    "GuardDuty": "security", "Inspector": "security", "Organizations": "security",
    # Monitoring
    "CloudWatchAlarm": "monitoring", "CloudWatchLogs": "monitoring", "CloudWatchEvent": "monitoring",
    # Analytics
    "Glue": "analytics", "Athena": "analytics", "EMR": "analytics",
    "OpenSearch": "analytics", "QuickSight": "analytics",
    # DevOps
    "CloudFormation": "devops_tools", "CodeBuild": "devops_tools",
    "CodeCommit": "devops_tools", "CodeDeploy": "devops_tools", "CodePipeline": "devops_tools",
    # Management & Governance
    "CloudTrail": "management_governance", "AWSConfig": "management_governance",
    "SSM": "management_governance", "ControlTower": "management_governance",
    "ServiceCatalog": "management_governance",
    # Migration
    "DataSync": "migration_transfer", "MGN": "migration_transfer",
    "MigrationHub": "migration_transfer", "Snowball": "migration_transfer",
    "Transfer": "migration_transfer", "DMS": "migration_transfer", "DatabaseMigrationService": "migration_transfer",
    # Cost Management
    "Budgets": "cost_management", "ComputeOptimizer": "cost_management",
    "CostExplorer": "cost_management", "CUR": "cost_management",
    "ReservedInstances": "cost_management", "SavingsPlans": "cost_management",
    # AI/ML
    "SageMaker": "ai_ml", "Comprehend": "ai_ml", "Lex": "ai_ml",
    "Polly": "ai_ml", "Rekognition": "ai_ml", "Textract": "ai_ml",
}

# Service name mapping
SERVICE_NAME_MAP = {
    "API Gateway": "apigateway",
    "CloudFront": "cloudfront",
    "CloudWatchAlarm": "cloudwatch",
    "CloudWatchLogs": "cloudwatch-logs",
    "CloudWatchEvent": "eventbridge",
    "DMS": "dms",
    "DocumentDB": "documentdb",
    "DynamoDB": "dynamodb",
    "EC2": "ec2",
    "ECR": "ecr",
    "EKS": "eks",
    "ELB": "elb",
    "ElastiCache": "elasticache",
    "Glue": "glue",
    "IAM": "iam",
    "Kinesis": "kinesis",
    "KMS": "kms",
    "Lambda": "lambda",
    "Kafka": "msk",
    "MSK": "msk",
    "RDS": "rds",
    "Route53": "route53",
    "S3": "s3",
    "SageMaker": "sagemaker",
    "SecretsManager": "secrets",
    "SNS": "sns",
    "SQS": "sqs",
    "VPC": "vpc",
    "WAF": "waf",
}

# Optional live-cost mapping (AWS Cost Explorer service names -> frontend service ids)
CE_SERVICE_NAME_TO_ID = {
    "AWS Lambda": "lambda",
    "Amazon Relational Database Service": "rds",
    "Amazon Elastic Compute Cloud - Compute": "ec2",
    "EC2 - Other": "ec2",
    "Amazon Virtual Private Cloud": "vpc",
    "Amazon Simple Storage Service": "s3",
    "Amazon CloudFront": "cloudfront",
    "Amazon CloudWatch": "cloudwatch",
    "AmazonCloudWatch": "cloudwatch",
    "CloudWatch Events": "eventbridge",
    "Amazon API Gateway": "apigateway",
    "Amazon Elastic Kubernetes Service": "eks",
    "Amazon Elastic Container Service for Kubernetes": "eks",
    "Elastic Load Balancing": "elb",
    "Amazon ElastiCache": "elasticache",
    "AWS Glue": "glue",
    "AWS Identity and Access Management": "iam",
    "AWS Key Management Service": "kms",
    "Amazon Kinesis": "kinesis",
    "Amazon DynamoDB": "dynamodb",
    "Amazon Route 53": "route53",
    "Amazon SageMaker": "sagemaker",
    "AWS Secrets Manager": "secrets",
    "Amazon Simple Notification Service": "sns",
    "Amazon Simple Queue Service": "sqs",
    "Amazon Elastic Container Registry (ECR)": "ecr",
    "Amazon EC2 Container Registry (ECR)": "ecr",
    "AWS WAF": "waf",
}

COST_CACHE_TTL_SECONDS = 10 * 60
_COST_CACHE: Dict[str, Dict[str, Any]] = {}

FX_CACHE_TTL_SECONDS = 30 * 60
_FX_CACHE: Dict[str, Any] = {"timestamp": 0, "rate": None, "source": ""}


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0

    text = text.replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0

    try:
        return float(match.group(0))
    except Exception:
        return 0.0


def _extract_monthly_cost(record: Dict[str, Any]) -> float:
    """Extract monthly cost from one resource record if present."""
    if not record:
        return 0.0

    normalized_record = {_normalize_key(k): v for k, v in record.items()}

    preferred_keys = [
        "currentmonthlycostusd",
        "monthlycostusd",
        "monthlycost",
        "estimatedmonthlycostusd",
        "estimatedmonthlycost",
        "unblendedcostusd",
        "unblendedcost",
    ]

    for key in preferred_keys:
        if key in normalized_record:
            return _to_float(normalized_record[key])

    # Fallback: any column containing both monthly and cost, excluding optimized/savings
    for key, value in normalized_record.items():
        if "monthly" in key and "cost" in key and "optimized" not in key and "saving" not in key:
            return _to_float(value)

    return 0.0


def _has_monthly_cost_field(record: Dict[str, Any]) -> bool:
    """Return True when a record has a recognizable monthly cost column."""
    if not record:
        return False

    normalized_keys = {_normalize_key(k) for k in record.keys()}
    preferred_keys = {
        "currentmonthlycostusd",
        "monthlycostusd",
        "monthlycost",
        "estimatedmonthlycostusd",
        "estimatedmonthlycost",
        "unblendedcostusd",
        "unblendedcost",
    }

    if normalized_keys.intersection(preferred_keys):
        return True

    for key in normalized_keys:
        if "monthly" in key and "cost" in key and "optimized" not in key and "saving" not in key:
            return True

    return False


def _map_ce_service_to_id(ce_service_name: str) -> Optional[str]:
    direct = CE_SERVICE_NAME_TO_ID.get(ce_service_name)
    if direct:
        return direct

    norm_target = _normalize_key(ce_service_name)

    # Handle common CE variants dynamically (e.g., EC2-Other, EC2-Instances)
    if "elasticcomputecloud" in norm_target or norm_target.startswith("ec2"):
        return "ec2"

    # Build dynamic aliases from known local service names/ids
    dynamic_aliases: Dict[str, set[str]] = defaultdict(set)
    for local_name, local_id in SERVICE_NAME_MAP.items():
        dynamic_aliases[local_id].add(_normalize_key(local_name))
        dynamic_aliases[local_id].add(_normalize_key(local_id))
        dynamic_aliases[local_id].add(_normalize_key(local_id.replace("-", " ")))

    # Trim AWS/Amazon prefix for better fuzzy matching
    norm_target_compact = _normalize_key(
        re.sub(r"^(amazon|aws)\s+", "", ce_service_name.strip(), flags=re.IGNORECASE)
    )

    for local_id, aliases in dynamic_aliases.items():
        for alias in aliases:
            if not alias:
                continue
            if alias in norm_target or norm_target in alias:
                return local_id
            if alias in norm_target_compact or norm_target_compact in alias:
                return local_id

    for name, service_id in CE_SERVICE_NAME_TO_ID.items():
        norm_name = _normalize_key(name)
        if norm_name in norm_target or norm_target in norm_name:
            return service_id
    return None


def _get_live_monthly_costs(profile: str) -> Dict[str, Any]:
    """Fetch month-to-date costs from AWS Cost Explorer for a profile (best effort)."""
    empty = {
        "total": 0.0,
        "byService": {},
        "previousTotal": 0.0,
        "monthlyChangePercent": None,
        "monthlyChangeDirection": "flat",
        "trendWindowDays": 0,
    }

    now = time.time()
    cached = _COST_CACHE.get(profile)
    if cached and (now - cached.get("timestamp", 0)) < COST_CACHE_TTL_SECONDS:
        return cached.get("data", empty)

    if boto3 is None:
        return empty

    try:
        session = boto3.Session(profile_name=profile)
        ce = session.client("ce", region_name="us-east-1")

        today = date.today()
        current_month_start = today.replace(day=1)
        current_month_end_exclusive = today + timedelta(days=1)
        elapsed_days = max((current_month_end_exclusive - current_month_start).days, 1)

        previous_month_last_day = current_month_start - timedelta(days=1)
        previous_month_start = previous_month_last_day.replace(day=1)
        previous_month_end_candidate = previous_month_start + timedelta(days=elapsed_days)
        previous_month_end_exclusive = min(previous_month_end_candidate, current_month_start)

        start = current_month_start.isoformat()
        # End is exclusive for CE API, so use tomorrow to include current day MTD
        end = current_month_end_exclusive.isoformat()

        resp = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        by_service: Dict[str, float] = {}
        total = 0.0

        for bucket in resp.get("ResultsByTime", []) or []:
            for group in bucket.get("Groups", []) or []:
                keys = group.get("Keys", []) or []
                service_name = keys[0] if keys else ""
                amount_str = (
                    group.get("Metrics", {})
                    .get("UnblendedCost", {})
                    .get("Amount", "0")
                )
                amount = _to_float(amount_str)

                if amount <= 0:
                    continue

                total += amount
                service_id = _map_ce_service_to_id(service_name)
                if service_id:
                    by_service[service_id] = by_service.get(service_id, 0.0) + amount

        def _get_period_total(start_date: date, end_date: date) -> float:
            period_resp = ce.get_cost_and_usage(
                TimePeriod={"Start": start_date.isoformat(), "End": end_date.isoformat()},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
            )

            period_total = 0.0
            for bucket in period_resp.get("ResultsByTime", []) or []:
                amount_str = (
                    (bucket.get("Total") or {})
                    .get("UnblendedCost", {})
                    .get("Amount", "0")
                )
                period_total += _to_float(amount_str)
            return round(period_total, 2)

        current_total = _get_period_total(current_month_start, current_month_end_exclusive)
        previous_total = _get_period_total(previous_month_start, previous_month_end_exclusive)

        monthly_change_percent = None
        monthly_change_direction = "flat"
        if previous_total > 0:
            delta = ((current_total - previous_total) / previous_total) * 100
            monthly_change_percent = round(abs(delta), 2)
            if delta > 0.05:
                monthly_change_direction = "up"
            elif delta < -0.05:
                monthly_change_direction = "down"

        data = {
            "total": round(total, 2),
            "byService": {k: round(v, 2) for k, v in by_service.items()},
            "previousTotal": round(previous_total, 2),
            "monthlyChangePercent": monthly_change_percent,
            "monthlyChangeDirection": monthly_change_direction,
            "trendWindowDays": elapsed_days,
        }
        _COST_CACHE[profile] = {"timestamp": now, "data": data}
        return data
    except Exception as exc:
        print(f"Cost Explorer lookup failed for profile {profile}: {exc}")
        return empty


def _get_usd_inr_rate() -> Dict[str, Any]:
    """Fetch current USD->INR rate with short-lived cache."""
    now = time.time()
    if _FX_CACHE.get("rate") and (now - float(_FX_CACHE.get("timestamp", 0))) < FX_CACHE_TTL_SECONDS:
        return {
            "base": "USD",
            "target": "INR",
            "rate": float(_FX_CACHE["rate"]),
            "cached": True,
            "source": _FX_CACHE.get("source", "open.er-api.com"),
        }

    url = "https://open.er-api.com/v6/latest/USD"
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))

        rates = payload.get("rates", {}) if isinstance(payload, dict) else {}
        inr_rate = rates.get("INR")
        if inr_rate is None:
            raise ValueError("INR rate not present in response")

        rate_value = float(inr_rate)
        _FX_CACHE["timestamp"] = now
        _FX_CACHE["rate"] = rate_value
        _FX_CACHE["source"] = "open.er-api.com"

        return {
            "base": "USD",
            "target": "INR",
            "rate": rate_value,
            "cached": False,
            "source": "open.er-api.com",
        }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        if _FX_CACHE.get("rate"):
            return {
                "base": "USD",
                "target": "INR",
                "rate": float(_FX_CACHE["rate"]),
                "cached": True,
                "source": _FX_CACHE.get("source", "open.er-api.com"),
                "warning": f"Using cached rate due to fetch error: {exc}",
            }
        raise HTTPException(status_code=503, detail=f"Unable to fetch exchange rate: {exc}")


def _find_service_display_name(stem: str) -> str:
    """Map a CSV filename stem (e.g. 'API_Gateway') back to a canonical service display name."""
    normalized = stem.replace("_", " ").strip()
    # Exact match (case-insensitive)
    for name in SERVICE_NAME_MAP.keys():
        if normalized.lower() == name.lower():
            return name
    # Partial match
    for name in SERVICE_NAME_MAP.keys():
        if normalized.lower() in name.lower() or name.lower() in normalized.lower():
            return name
    return normalized


def read_account_data(account: str) -> Dict[str, Any]:
    """Read all service CSV files for *account* from ``Data/{account}/{region}/{Service}.csv``.

    Returns the same shape as the old ``parse_csv_to_json`` output so all
    existing endpoints are backward-compatible:

    .. code-block:: python

        {
          "ec2": {
            "serviceName": "EC2",
            "serviceId": "ec2",
            "resourceCount": 12,
            "resources": [{...}, ...],
            "monthlyCost": 45.6,   # optional
          },
          ...
        }
    """
    try:
        import pandas as pd
    except ImportError:
        pd = None  # type: ignore

    account_dir = DATA_DIR / account
    if not account_dir.exists():
        return {}

    services_data: Dict[str, Any] = {}

    for region_dir in sorted(account_dir.iterdir()):
        if not region_dir.is_dir():
            continue
        region = region_dir.name

        for csv_file in sorted(region_dir.glob("*.csv")):
            stem = csv_file.stem  # e.g. "EC2", "API_Gateway"
            service_name = _find_service_display_name(stem)
            service_id = SERVICE_NAME_MAP.get(service_name, stem.lower().replace("_", "-"))

            try:
                if pd is not None:
                    df = pd.read_csv(csv_file, dtype=str)
                    df = df.fillna("")
                    records: List[Dict[str, Any]] = df.to_dict(orient="records")
                else:
                    with open(csv_file, "r", encoding="utf-8", newline="") as f:
                        reader = csv.DictReader(f)
                        records = [{k: (v or "") for k, v in row.items()} for row in reader]

                if not records:
                    continue

                # Stamp region if not already a column
                for rec in records:
                    if "Region" not in rec:
                        rec["Region"] = region

                if service_id not in services_data:
                    services_data[service_id] = {
                        "serviceName": service_name,
                        "serviceId": service_id,
                        "resourceCount": 0,
                        "resources": [],
                    }

                services_data[service_id]["resources"].extend(records)
                services_data[service_id]["resourceCount"] += len(records)

                if any(_has_monthly_cost_field(r) for r in records):
                    extra_cost = round(sum(_extract_monthly_cost(r) for r in records), 2)
                    existing = float(services_data[service_id].get("monthlyCost") or 0)
                    services_data[service_id]["monthlyCost"] = round(existing + extra_cost, 2)

            except Exception as exc:
                print(f"Error reading {csv_file}: {exc}")

    return services_data


# ---------------------------------------------------------------------------
# Legacy helper kept for potential external callers
# ---------------------------------------------------------------------------

def parse_csv_to_json(csv_path: Path) -> Dict[str, Any]:
    """Legacy: read old-style stacked multi-service CSV.  Falls back to read_account_data."""
    # Try new-style directory structure first by inferring account from path
    account = csv_path.stem  # e.g. /some/path/my_account.csv -> "my_account"
    data = read_account_data(account)
    if data:
        return data
    # Fall back: read as plain per-service CSV
    try:
        services_data: Dict[str, Any] = {}
        service_name = csv_path.stem
        service_id = SERVICE_NAME_MAP.get(service_name, service_name.lower())
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            records = [{k: (v or "") for k, v in row.items()} for row in reader]
        if records:
            services_data[service_id] = {
                "serviceName": service_name,
                "serviceId": service_id,
                "resourceCount": len(records),
                "resources": records,
            }
        return services_data
    except Exception as e:
        print(f"Error reading CSV {csv_path}: {e}")
        return {}


def get_account_regions(account: str) -> List[str]:
    """Return the list of region subdirectory names under Data/{account}/."""
    account_dir = DATA_DIR / account
    if not account_dir.exists():
        return []
    return sorted(d.name for d in account_dir.iterdir() if d.is_dir())


# Legacy name kept for backward compat
def extract_profile_region(csv_file: Path) -> str:  # noqa: ARG001
    """Deprecated: infer region from account directory structure."""
    account = csv_file.stem
    regions = get_account_regions(account)
    if not regions:
        return "unknown"
    if len(regions) == 1:
        return regions[0]
    return "multi-region"


@app.get("/api/discovery")
async def get_discovery():
    """Return the full account → region → category → [services] structure.

    Shape expected by the frontend dataService:
    {
      "accounts": ["account1", ...],
      "regions": {"account1": ["ap-south-1", ...], ...},
      "services": {"account1": {"compute": ["ec2", "eks"], "storage": ["s3"], ...}, ...}
    }
    """
    if not DATA_DIR.exists():
        return {"accounts": [], "regions": {}, "services": {}}

    accounts: List[str] = []
    regions: Dict[str, List[str]] = {}
    services: Dict[str, Dict[str, List[str]]] = {}

    # Build a lowercase-stem → canonical service name lookup
    stem_to_service: Dict[str, str] = {}
    for svc_name in SERVICE_CATEGORY_MAP:
        stem_to_service[svc_name.lower().replace(" ", "_")] = svc_name
        stem_to_service[svc_name.lower()] = svc_name
        # Also try underscore-lowered service id from SERVICE_NAME_MAP
        sid = SERVICE_NAME_MAP.get(svc_name, "")
        if sid:
            stem_to_service[sid.lower().replace("-", "_")] = svc_name
            stem_to_service[sid.lower()] = svc_name

    for account_dir in sorted(DATA_DIR.iterdir()):
        if not account_dir.is_dir():
            continue
        account = account_dir.name
        accounts.append(account)
        account_regions: List[str] = []
        category_service_map: Dict[str, List[str]] = {}

        for region_dir in sorted(account_dir.iterdir()):
            if not region_dir.is_dir():
                continue
            region = region_dir.name
            account_regions.append(region)

            for csv_file in sorted(region_dir.glob("*.csv")):
                stem = csv_file.stem  # e.g. "EC2", "API_Gateway"
                # Resolve service name
                canonical = (
                    stem_to_service.get(stem.lower()) or
                    stem_to_service.get(stem.lower().replace(" ", "_")) or
                    _find_service_display_name(stem)
                )
                category = SERVICE_CATEGORY_MAP.get(canonical, "general")
                # Use lowercase service id for frontend compatibility
                service_id = SERVICE_NAME_MAP.get(canonical, stem.lower().replace(" ", "-"))
                if category not in category_service_map:
                    category_service_map[category] = []
                if service_id not in category_service_map[category]:
                    category_service_map[category].append(service_id)

        regions[account] = account_regions
        services[account] = category_service_map

    return {"accounts": accounts, "regions": regions, "services": services}


@app.get("/api/data/{account}/{region}/{service}")
async def get_data_by_region_service(account: str, region: str, service: str):
    """Return service data for a specific account/region/service.

    Looks for ``Data/{account}/{region}/{service}.csv`` (case-insensitive stem).
    Response shape expected by frontend dataService:
    {
      "schema_version": "1.0.0",
      "generated_at": "...",
      "service": {"service_name": ..., "region": ..., "profile": ...},
      "summary": {"resource_count": N, "scan_status": "success"},
      "resources": [{...}, ...]
    }
    """
    try:
        import pandas as pd
    except ImportError:
        pd = None  # type: ignore

    region_dir = DATA_DIR / account / region
    if not region_dir.exists():
        raise HTTPException(status_code=404, detail=f"No data for {account}/{region}")

    # Find CSV file — match by stem, case-insensitively, and also by service_id
    target_stems = {
        service.lower(),
        service.lower().replace("-", "_"),
        service.replace("-", "_").upper(),
    }
    # Also try to map service_id back to collector key (e.g. 'ec2' → 'EC2')
    for svc_name, sid in SERVICE_NAME_MAP.items():
        if sid.lower() == service.lower() or sid.lower().replace("-", "") == service.lower().replace("-", ""):
            target_stems.add(svc_name.lower())
            target_stems.add(svc_name.lower().replace(" ", "_"))

    csv_file: Optional[Path] = None
    for f in region_dir.glob("*.csv"):
        if f.stem.lower() in target_stems or f.stem.lower().replace(" ", "_") in target_stems:
            csv_file = f
            break

    if csv_file is None:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found for {account}/{region}")

    try:
        if pd is not None:
            df = pd.read_csv(csv_file, dtype=str).fillna("")
            # Preserve exact column order from CSV (same as Excel sheet order)
            csv_columns: List[str] = df.columns.tolist()
            records: List[Dict[str, Any]] = df.to_dict(orient="records")
        else:
            with open(csv_file, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                records = [{k: (v or "") for k, v in row.items()} for row in reader]
                csv_columns = list(reader.fieldnames or [])

        # Stamp Region column if absent
        region_stamped = False
        for rec in records:
            if "Region" not in rec:
                rec["Region"] = region
                region_stamped = True
        if region_stamped and "Region" not in csv_columns:
            csv_columns.append("Region")

        return {
            "schema_version": "1.0.0",
            "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "service": {
                "service_name": service,
                "region": region,
                "profile": account,
            },
            "summary": {
                "resource_count": len(records),
                "scan_status": "success",
            },
            "columns": csv_columns,
            "resources": records,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reading data: {exc}")


@app.get("/api/data/{account}/{region}/{category}/{service}")
async def get_data_by_category_service(account: str, region: str, category: str, service: str):
    """Same as above but with category segment in path (ignored, forwarded to region/service lookup)."""
    return await get_data_by_region_service(account, region, service)


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "AWS Inventory API",
        "version": "1.0.0",
        "endpoints": {
            "profiles": "/api/profiles",
            "services": "/api/services",
            "profile_data": "/api/profiles/{profile}",
            "service_data": "/api/profiles/{profile}/services/{service}"
        }
    }


@app.get("/api/profiles")
async def get_profiles():
    """Get list of available AWS accounts (sub-directories of Data/)."""
    if not DATA_DIR.exists():
        raise HTTPException(status_code=404, detail="Data directory not found")

    profiles = []
    for account_dir in sorted(DATA_DIR.iterdir()):
        if not account_dir.is_dir():
            continue
        regions = sorted(d.name for d in account_dir.iterdir() if d.is_dir())
        profiles.append({
            "id": account_dir.name,
            "name": account_dir.name,
            "profile": account_dir.name,
            "region": regions[0] if len(regions) == 1 else ("multi-region" if regions else "unknown"),
            "regions": regions,
        })

    return {"profiles": profiles, "count": len(profiles)}


@app.get("/api/services")
async def get_services():
    """Get list of all available AWS services from collectors."""
    services = []
    
    for service_name, collector_func in COLLECTOR_FUNCTIONS.items():
        service_id = SERVICE_NAME_MAP.get(service_name, service_name.lower().replace(' ', '-'))
        services.append({
            "id": service_id,
            "name": service_name,
            "collectorFunction": collector_func.__name__
        })
    
    return {"services": services, "count": len(services)}


@app.get("/api/exchange-rate/usd-inr")
async def get_usd_inr_exchange_rate():
    """Get current USD->INR exchange rate for currency conversion in UI."""
    return _get_usd_inr_rate()


@app.get("/api/profiles/{profile}")
async def get_profile_data(profile: str):
    """Get all services data for a specific account (aggregated across all regions)."""
    if not (DATA_DIR / profile).exists():
        raise HTTPException(status_code=404, detail=f"Profile '{profile}' not found")

    services_data = read_account_data(profile)
    total_resources = sum(svc["resourceCount"] for svc in services_data.values())

    return {
        "profile": profile,
        "servicesCount": len(services_data),
        "totalResources": total_resources,
        "services": services_data,
    }


@app.get("/api/profiles/{profile}/services/{service}")
async def get_service_data(profile: str, service: str):
    """Get specific service data for an account."""
    if not (DATA_DIR / profile).exists():
        raise HTTPException(status_code=404, detail=f"Profile '{profile}' not found")

    services_data = read_account_data(profile)

    if service not in services_data:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service}' not found in profile '{profile}'",
        )

    return services_data[service]


@app.get("/api/profiles/{profile}/overview")
async def get_profile_overview(profile: str):
    """Get overview/summary for an account with resource counts per service."""
    if not (DATA_DIR / profile).exists():
        raise HTTPException(status_code=404, detail=f"Profile '{profile}' not found")

    services_data = read_account_data(profile)
    
    overview = []
    for service_id, service_data in services_data.items():
        item = {
            "id": service_id,
            "name": service_data['serviceName'],
            "resourceCount": service_data['resourceCount'],
            "healthStatus": "healthy",  # You can add logic to determine health
        }

        if service_data.get('monthlyCost') is not None:
            base_cost = _to_float(service_data.get('monthlyCost'))
            item["monthlyCost"] = round(base_cost, 2)

        overview.append(item)

    # Best-effort live MTD costs from AWS Cost Explorer (same source family as AWS console)
    live_costs = _get_live_monthly_costs(profile)
    live_total = live_costs.get("total", 0.0)
    live_by_service = live_costs.get("byService", {})

    for item in overview:
        sid = item.get("id")
        if sid in live_by_service:
            live_cost = _to_float(live_by_service[sid])
            if live_cost > 0:
                item["monthlyCost"] = round(live_cost, 2)

    total_monthly_cost = live_total if live_total > 0 else round(sum(float(s.get("monthlyCost", 0) or 0) for s in overview), 2)
    previous_month_cost = _to_float(live_costs.get("previousTotal"))
    monthly_change_percent = live_costs.get("monthlyChangePercent")
    monthly_change_direction = live_costs.get("monthlyChangeDirection") or "flat"
    trend_window_days = int(_to_float(live_costs.get("trendWindowDays")))
    
    return {
        "profile": profile,
        "services": overview,
        "totalServices": len(overview),
        "totalResources": sum(svc['resourceCount'] for svc in overview),
        "totalMonthlyCost": total_monthly_cost,
        "previousMonthlyCost": previous_month_cost,
        "monthlyChangePercent": monthly_change_percent,
        "monthlyChangeDirection": monthly_change_direction,
        "trendWindowDays": trend_window_days,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
