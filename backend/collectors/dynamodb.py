"""Amazon DynamoDB collectors."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from aws_utils import safe_call
from config import REGION


def _get_cloudwatch_avg_metric(cloudwatch, table_name: str, metric_name: str, days: int = 30) -> float | None:
    """Get average CloudWatch metric for DynamoDB table."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)
    
    response = safe_call(
        lambda: cloudwatch.get_metric_statistics(
            Namespace="AWS/DynamoDB",
            MetricName=metric_name,
            Dimensions=[{"Name": "TableName", "Value": table_name}],
            Statistics=["Average"],
            Period=3600,  # 1 hour
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    if not datapoints:
        return None
    
    values = []
    for dp in datapoints:
        try:
            values.append(float(dp.get("Average", 0.0)))
        except Exception:
            continue
    
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _get_cloudwatch_sum_metric(cloudwatch, table_name: str, metric_name: str, days: int = 30) -> float | None:
    """Get sum of CloudWatch metric for DynamoDB table."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)
    
    response = safe_call(
        lambda: cloudwatch.get_metric_statistics(
            Namespace="AWS/DynamoDB",
            MetricName=metric_name,
            Dimensions=[{"Name": "TableName", "Value": table_name}],
            Statistics=["Sum"],
            Period=3600,  # 1 hour
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    if not datapoints:
        return None
    
    total = 0.0
    for dp in datapoints:
        try:
            total += float(dp.get("Sum", 0.0))
        except Exception:
            continue
    
    return round(total, 2) if total > 0 else None


def collect_dynamodb(session, cost_map):
    dynamodb = session.client("dynamodb", region_name=REGION)
    cloudwatch = session.client("cloudwatch", region_name=REGION)
    application_autoscaling = session.client("application-autoscaling", region_name=REGION)
    
    rows = []
    
    # List all tables
    table_names = safe_call(lambda: dynamodb.list_tables().get("TableNames", []), [])
    
    for table_name in table_names or []:
        # Get table details
        table_info = safe_call(
            lambda: dynamodb.describe_table(TableName=table_name).get("Table", {}),
            {}
        )
        
        if not table_info:
            continue
        
        # Basic table information
        table_status = table_info.get("TableStatus", "")
        table_arn = table_info.get("TableArn", "")
        creation_date = table_info.get("CreationDateTime", "")
        if isinstance(creation_date, datetime):
            creation_date = creation_date.strftime("%Y-%m-%d")
        
        # Billing mode
        billing_mode_summary = table_info.get("BillingModeSummary", {})
        billing_mode = billing_mode_summary.get("BillingMode", "PROVISIONED")
        
        # Provisioned throughput
        provisioned_throughput = table_info.get("ProvisionedThroughput", {})
        read_capacity = provisioned_throughput.get("ReadCapacityUnits", "")
        write_capacity = provisioned_throughput.get("WriteCapacityUnits", "")
        
        # For on-demand tables
        if billing_mode == "PAY_PER_REQUEST":
            read_capacity = "On-Demand"
            write_capacity = "On-Demand"
        
        # Table size and item count
        table_size_bytes = table_info.get("TableSizeBytes", 0)
        table_size_gb = round(table_size_bytes / (1024**3), 2) if table_size_bytes else 0
        item_count = table_info.get("ItemCount", 0)
        
        # Encryption
        sse_description = table_info.get("SSEDescription", {})
        encryption_status = sse_description.get("Status", "DISABLED")
        encryption_type = sse_description.get("SSEType", "")
        kms_key_arn = sse_description.get("KMSMasterKeyArn", "")
        
        if encryption_status == "ENABLED":
            if encryption_type == "KMS":
                encryption_info = "KMS"
            else:
                encryption_info = "AWS Owned"
        else:
            encryption_info = "Disabled"
        
        # Point-in-time recovery
        pitr_info = safe_call(
            lambda: dynamodb.describe_continuous_backups(TableName=table_name).get("ContinuousBackupsDescription", {}),
            {}
        )
        pitr_status = pitr_info.get("PointInTimeRecoveryDescription", {}).get("PointInTimeRecoveryStatus", "DISABLED")
        
        # Global Secondary Indexes
        gsi_list = table_info.get("GlobalSecondaryIndexes", [])
        gsi_count = len(gsi_list) if gsi_list else 0
        
        # Local Secondary Indexes
        lsi_list = table_info.get("LocalSecondaryIndexes", [])
        lsi_count = len(lsi_list) if lsi_list else 0
        
        # Stream settings
        stream_spec = table_info.get("StreamSpecification", {})
        stream_enabled = stream_spec.get("StreamEnabled", False)
        stream_view_type = stream_spec.get("StreamViewType", "") if stream_enabled else ""
        
        # Time to Live
        ttl_info = safe_call(
            lambda: dynamodb.describe_time_to_live(TableName=table_name).get("TimeToLiveDescription", {}),
            {}
        )
        ttl_status = ttl_info.get("TimeToLiveStatus", "DISABLED")
        
        # Tags
        tags_info = safe_call(
            lambda: dynamodb.list_tags_of_resource(ResourceArn=table_arn).get("Tags", []),
            []
        )
        tags = {tag.get("Key"): tag.get("Value") for tag in tags_info} if tags_info else {}
        
        # Auto Scaling check
        autoscaling_enabled = False
        try:
            scalable_targets = application_autoscaling.describe_scalable_targets(
                ServiceNamespace="dynamodb",
                ResourceIds=[f"table/{table_name}"]
            ).get("ScalableTargets", [])
            autoscaling_enabled = len(scalable_targets) > 0
        except Exception:
            pass
        
        # CloudWatch metrics (last 30 days)
        consumed_read_capacity = _get_cloudwatch_sum_metric(cloudwatch, table_name, "ConsumedReadCapacityUnits")
        consumed_write_capacity = _get_cloudwatch_sum_metric(cloudwatch, table_name, "ConsumedWriteCapacityUnits")
        user_errors = _get_cloudwatch_sum_metric(cloudwatch, table_name, "UserErrors")
        system_errors = _get_cloudwatch_sum_metric(cloudwatch, table_name, "SystemErrors")
        
        # Calculate optimization status
        optimization_status = ""
        if billing_mode == "PROVISIONED" and consumed_read_capacity is not None and read_capacity not in ["On-Demand", ""]:
            try:
                read_utilization = (consumed_read_capacity / (float(read_capacity) * 30 * 24 * 3600)) * 100
                if read_utilization < 10:
                    optimization_status = "Low Read Utilization"
            except Exception:
                pass
        
        if item_count == 0 and table_status == "ACTIVE":
            optimization_status = "Empty Table"
        
        # Get cost from cost_map
        monthly_cost = cost_map.get(table_name, 0.0) if cost_map else 0.0
        
        rows.append({
            "TableName": table_name,
            "TableArn": table_arn,
            "Status": table_status,
            "CreationDate": creation_date,
            "BillingMode": billing_mode,
            "ReadCapacityUnits": read_capacity,
            "WriteCapacityUnits": write_capacity,
            "TableSizeGB": table_size_gb,
            "ItemCount": item_count,
            "Encryption": encryption_info,
            "PointInTimeRecovery": "Enabled" if pitr_status == "ENABLED" else "Disabled",
            "GlobalSecondaryIndexes": gsi_count,
            "LocalSecondaryIndexes": lsi_count,
            "StreamEnabled": "Yes" if stream_enabled else "No",
            "StreamViewType": stream_view_type,
            "TTL": "Enabled" if ttl_status == "ENABLED" else "Disabled",
            "AutoScaling": "Enabled" if autoscaling_enabled else "Disabled",
            "ConsumedReadCapacity30d": consumed_read_capacity if consumed_read_capacity else "",
            "ConsumedWriteCapacity30d": consumed_write_capacity if consumed_write_capacity else "",
            "UserErrors30d": user_errors if user_errors else "",
            "SystemErrors30d": system_errors if system_errors else "",
            "OptimizationStatus": optimization_status,
            "MonthlyCost": monthly_cost,
            "EstimatedSavings": 0.0,  # Can be enhanced with savings logic
        })
    
    return pd.DataFrame(rows)
