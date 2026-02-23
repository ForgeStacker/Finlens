"""Amazon S3 collectors."""
from __future__ import annotations

import datetime

import pandas as pd

from aws_utils import format_bytes_to_gb, safe_call
from config import REGION


def collect_s3(session, cost_map):
    cw = session.client("cloudwatch", region_name=REGION)
    s3 = session.client("s3", region_name=REGION)
    rows = []
    buckets = safe_call(lambda: s3.list_buckets().get("Buckets", []), [])
    for bucket in buckets or []:
        name = bucket.get("Name")
        size_bytes = None
        obj_count = None
        try:
            size_metrics = cw.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {"Name": "BucketName", "Value": name},
                    {"Name": "StorageType", "Value": "StandardStorage"},
                ],
                StartTime=datetime.datetime.utcnow() - datetime.timedelta(days=14),
                EndTime=datetime.datetime.utcnow(),
                Period=86400,
                Statistics=["Average"],
            )
            datapoints = size_metrics.get("Datapoints", [])
            if datapoints:
                size_bytes = sorted(datapoints, key=lambda x: x["Timestamp"], reverse=True)[0]["Average"]
        except Exception as exc:
            print(f"  ⚠ S3 CloudWatch size metric error for {name}: {exc}")
        try:
            obj_metrics = cw.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="NumberOfObjects",
                Dimensions=[
                    {"Name": "BucketName", "Value": name},
                    {"Name": "StorageType", "Value": "AllStorageTypes"},
                ],
                StartTime=datetime.datetime.utcnow() - datetime.timedelta(days=14),
                EndTime=datetime.datetime.utcnow(),
                Period=86400,
                Statistics=["Average"],
            )
            datapoints = obj_metrics.get("Datapoints", [])
            if datapoints:
                obj_count = int(round(sorted(datapoints, key=lambda x: x["Timestamp"], reverse=True)[0]["Average"]))
        except Exception as exc:
            print(f"  ⚠ S3 CloudWatch object count metric error for {name}: {exc}")
        try:
            versioning = s3.get_bucket_versioning(Bucket=name)
            versioning_status = versioning.get("Status", "Disabled")
        except Exception as exc:
            print(f"  ⚠ S3 versioning access error for {name}: {exc}")
            versioning_status = "Error"

        public_block_config = safe_call(
            lambda: s3.get_public_access_block(Bucket=name).get("PublicAccessBlockConfiguration"),
            None,
        )
        if public_block_config is None:
            block_all_public_access = "Unknown"
        else:
            flags = [
                public_block_config.get("BlockPublicAcls", False),
                public_block_config.get("IgnorePublicAcls", False),
                public_block_config.get("BlockPublicPolicy", False),
                public_block_config.get("RestrictPublicBuckets", False),
            ]
            block_all_public_access = "ON" if all(flags) else "OFF"
        rows.append(
            {
                "BucketName": name,
                "SizeGB": format_bytes_to_gb(size_bytes) if size_bytes is not None else None,
                "ObjectCount": obj_count,
                "Versioning": versioning_status,
                "BlockAllPublicAccess": block_all_public_access,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty and "ObjectCount" in df.columns:
        df["ObjectCount"] = df["ObjectCount"].apply(lambda value: int(value) if pd.notnull(value) else "")
    return df
