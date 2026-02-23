"""Amazon RDS collectors."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from aws_utils import get_instance_type_specs, safe_call
from config import REGION


def _avg_cloudwatch_metric(cloudwatch_client, metric_name: str, db_instance_id: str, start_time: datetime, end_time: datetime, period_seconds: int = 3600) -> float | None:
    response = safe_call(
        lambda: cloudwatch_client.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName=metric_name,
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_instance_id}],
            Statistics=["Average"],
            Period=period_seconds,
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    values = []
    for dp in datapoints:
        try:
            values.append(float(dp.get("Average", 0.0)))
        except Exception:
            continue
    if not values:
        return None
    return sum(values) / len(values)


def _avg_cloudwatch_metric_by_dimension(
    cloudwatch_client,
    metric_name: str,
    dimension_name: str,
    dimension_value: str,
    start_time: datetime,
    end_time: datetime,
    period_seconds: int = 3600,
) -> float | None:
    response = safe_call(
        lambda: cloudwatch_client.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName=metric_name,
            Dimensions=[{"Name": dimension_name, "Value": dimension_value}],
            Statistics=["Average"],
            Period=period_seconds,
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    values = []
    for dp in datapoints:
        try:
            values.append(float(dp.get("Average", 0.0)))
        except Exception:
            continue
    if not values:
        return None
    return sum(values) / len(values)


def _avg_db_load(pi_client, dbi_resource_id: str, start_time: datetime, end_time: datetime, period_seconds: int = 3600) -> float | None:
    response = safe_call(
        lambda: pi_client.get_resource_metrics(
            ServiceType="RDS",
            Identifier=dbi_resource_id,
            MetricQueries=[{"Metric": "db.load.avg"}],
            StartTime=start_time,
            EndTime=end_time,
            PeriodInSeconds=period_seconds,
        ),
        {},
    )

    metric_list = response.get("MetricList", []) if isinstance(response, dict) else []
    if not metric_list:
        return None
    datapoints = metric_list[0].get("DataPoints", []) if isinstance(metric_list[0], dict) else []
    values = []
    for dp in datapoints:
        try:
            values.append(float(dp.get("Value", 0.0)))
        except Exception:
            continue
    if not values:
        return None
    return sum(values) / len(values)


def _fetch_rds_cost_per_instance(session) -> dict[str, float]:
    """Fetch per-RDS-instance monthly cost from Cost Explorer (14-day DAILY window scaled to 30 days).

    Returns a dict of {db_identifier: estimated_monthly_cost_usd}.
    Falls back to empty dict on any error (e.g. no CE access).
    """
    from datetime import date, timedelta as td
    try:
        ce = session.client("ce", region_name="us-east-1")
        end_date = date.today()
        start_date = end_date - td(days=14)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str   = end_date.strftime("%Y-%m-%d")

        resp = ce.get_cost_and_usage_with_resources(
            TimePeriod={"Start": start_str, "End": end_str},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            Filter={
                "Dimensions": {
                    "Key": "SERVICE",
                    "Values": ["Amazon Relational Database Service"],
                }
            },
            GroupBy=[{"Type": "DIMENSION", "Key": "RESOURCE_ID"}],
        )

        # Aggregate daily costs per resource
        cost_by_arn: dict[str, float] = {}
        for period in resp.get("ResultsByTime", []):
            for grp in period.get("Groups", []):
                rid  = grp["Keys"][0]
                cost = float(grp["Metrics"]["UnblendedCost"]["Amount"])
                cost_by_arn[rid] = cost_by_arn.get(rid, 0.0) + cost

        # Scale 14-day window → 30-day monthly estimate
        scale = 30.0 / 14.0
        # Extract db-identifier (last ARN segment) and filter to real instances only
        result: dict[str, float] = {}
        for arn, cost in cost_by_arn.items():
            # Skip snapshots and empty IDs
            if ":cluster-snapshot:" in arn or arn in ("NoResourceId", ""):
                continue
            db_id = arn.split(":")[-1]
            if db_id:
                result[db_id] = round(cost * scale, 2)
        return result
    except Exception:
        return {}


def _calculate_rds_savings(current_cost: float, load_vs_vcpu_percent: float | None, optimization_status: str) -> float:
    """Calculate estimated monthly savings based on load vs capacity ratio.

    Formula (Low Load only):
      raw_fraction  = 1 - (load_pct / 100) / 0.70   (0.70 = healthy target utilization)
      savings_frac  = clamp(raw_fraction, 0, 0.50)   (max one instance-tier downsize ≈ 50% compute)
      savings       = current_cost × savings_frac × 0.65  (only ~65% of RDS bill is compute)
    """
    if optimization_status != "Low Load":
        return 0.0
    if not isinstance(load_vs_vcpu_percent, (int, float)) or load_vs_vcpu_percent is None:
        return 0.0
    raw_fraction = 1.0 - (load_vs_vcpu_percent / 100.0) / 0.70
    savings_frac = max(0.0, min(raw_fraction, 0.50))
    return round(current_cost * savings_frac * 0.65, 2)


def collect_rds(session, cost_map):
    rds = session.client("rds", region_name=REGION)
    ec2 = session.client("ec2", region_name=REGION)
    cloudwatch = session.client("cloudwatch", region_name=REGION)
    pi_client = session.client("pi", region_name=REGION)

    # Fetch real per-instance costs from Cost Explorer (Approach B)
    rds_instance_costs = _fetch_rds_cost_per_instance(session)

    rows = []
    dbs = safe_call(lambda: rds.describe_db_instances().get("DBInstances", []), [])
    clusters = safe_call(lambda: rds.describe_db_clusters().get("DBClusters", []), [])

    metrics_end   = datetime.now(timezone.utc)
    metrics_start = metrics_end - timedelta(days=30)
    # CW period: 86400 s (daily) for 30-day window → 30 datapoints, within CW extended-retention rules
    CW_PERIOD = 86400
    # PI period: 3600 s (hourly) — PI stores 1-h resolution for 2 years
    PI_PERIOD = 3600

    cluster_support_map = {}
    cluster_storage_map = {}
    cluster_param_map = {}
    cluster_insights_map = {}
    cluster_instance_role_map = {}

    cluster_rows = {}
    cluster_order = []
    cluster_instance_rows = {}
    standalone_instances = []
    orphan_cluster_instances = {}
    cluster_volume_used_gb: dict[str, float] = {}

    for c in clusters or []:
        cluster_id = c.get("DBClusterIdentifier")
        if not cluster_id:
            continue
        cluster_order.append(cluster_id)
        support = c.get("EngineLifecycleSupport")
        storage_type = c.get("StorageType")
        param_group = c.get("DBClusterParameterGroup")
        if support:
            if "extended-support-enabled" in support:
                cluster_support_map[cluster_id] = "Enabled"
            elif "extended-support-disabled" in support:
                cluster_support_map[cluster_id] = "Disabled"
            else:
                cluster_support_map[cluster_id] = support
        if storage_type:
            cluster_storage_map[cluster_id] = storage_type
        if param_group:
            cluster_param_map[cluster_id] = param_group
        di_mode = c.get("DatabaseInsightsMode")
        if di_mode:
            cluster_insights_map[cluster_id] = di_mode
        for member in c.get("DBClusterMembers", []):
            member_id = member.get("DBInstanceIdentifier")
            if member_id:
                cluster_instance_role_map[member_id] = member.get("IsClusterWriter", False)

        monitoring_type = ""
        di_value = c.get("DatabaseInsightsMode")
        if di_value:
            if isinstance(di_value, str):
                if di_value.lower() == "standard":
                    monitoring_type = "Database Insights - Standard"
                elif di_value.lower() == "advanced":
                    monitoring_type = "Database Insights - Advanced"
                else:
                    monitoring_type = f"Database Insights - {str(di_value).capitalize()}"
            else:
                monitoring_type = f"Database Insights - {str(di_value)}"
        preferred_backup_window = c.get("PreferredBackupWindow") or ""
        if preferred_backup_window and not preferred_backup_window.strip().endswith("UTC"):
            preferred_backup_window = f"{preferred_backup_window} UTC"
        enhanced_monitoring = "Enabled" if c.get("MonitoringInterval", 0) else "Disabled"
        engine = c.get("Engine", "").lower()
        storage_type = c.get("StorageType")
        if engine.startswith("aurora"):
            if storage_type == "aurora-iopt1":
                cluster_storage_config = "Aurora I/O-Optimized"
            else:
                cluster_storage_config = "Aurora Standard"
        else:
            cluster_storage_config = storage_type or ""
        maintenance_window = c.get("PreferredMaintenanceWindow") or ""
        if maintenance_window and not maintenance_window.strip().endswith("UTC"):
            maintenance_window = f"{maintenance_window} UTC"

        volume_bytes_used = _avg_cloudwatch_metric_by_dimension(
            cloudwatch,
            "VolumeBytesUsed",
            "DBClusterIdentifier",
            cluster_id,
            metrics_start,
            metrics_end,
            period_seconds=CW_PERIOD,
        )
        used_storage_gb_cluster = (volume_bytes_used / (1024.0 ** 3)) if isinstance(volume_bytes_used, (int, float)) else None
        if isinstance(used_storage_gb_cluster, (int, float)):
            cluster_volume_used_gb[cluster_id] = used_storage_gb_cluster

        cluster_rows[cluster_id] = {
            "DBInstanceIdentifier": cluster_id,
            "Role": "Regional cluster",
            "Engine": c.get("Engine"),
            "EngineVersion": c.get("EngineVersion"),
            "ExtededSupport": cluster_support_map.get(cluster_id, c.get("EngineLifecycleSupport", "")),
            "ParameterGroup": c.get("DBClusterParameterGroup"),
            "ClusterParameterGroup": c.get("DBClusterParameterGroup"),
            "DeletionProtection": c.get("DeletionProtection"),
            "InstanceClass": "",
            "vCPU": "",
            "MemoryGB": "",
            "MultiAZ": c.get("MultiAZ"),
            "StorageType": c.get("StorageType"),
            "ClusterStorageConfiguration": cluster_storage_config,
            "AllocatedStorageGB": "",
            "Iops": "",
            "Throughput": "",
            "Autoscaling": "",
            "PerformanceInsights": c.get("PerformanceInsightsEnabled"),
            "MonitoringType": monitoring_type,
            "EnhancedMonitoring": enhanced_monitoring,
            "BackupRetentionPeriod": c.get("BackupRetentionPeriod"),
            "PreferredBackupWindow": preferred_backup_window,
            "CopyTagsToSnapshot": "Enabled" if c.get("CopyTagsToSnapshot") else "Disabled",
            "Subnets": "",
            "SubnetGroup": c.get("DBSubnetGroup"),
            "SecurityGroups": "",
            "AutoMinorVersionUpgrade": c.get("AutoMinorVersionUpgrade"),
            "MaxAllocatedStorage": c.get("MaxAllocatedStorage"),
            "MaintenanceWindow": maintenance_window,
            "AvgDBLoad": "",
            "FreeStorageGB": "",
            "UsedStorageGB": round(used_storage_gb_cluster, 2) if isinstance(used_storage_gb_cluster, (int, float)) else "",
            "StorageUtilizationPercent": "",
            "LoadVsVcpuPercent": "",
            "OptimizationStatus": "",
        }

    for db in dbs or []:
        clazz = db.get("DBInstanceClass")
        base_it = clazz[3:] if clazz and clazz.startswith("db.") else clazz
        specs = {}
        if base_it:
            specs = get_instance_type_specs(ec2, base_it) or {"vcpus": "N/A", "memory_mb": "N/A"}
        engine = db.get("Engine", "").lower()
        storage_type = db.get("StorageType")
        if engine.startswith("aurora"):
            if storage_type == "aurora-iopt1":
                cluster_storage_config = "Aurora I/O-Optimized"
            else:
                cluster_storage_config = "Aurora Standard"
        else:
            cluster_storage_config = storage_type or ""

        memory_mb = specs.get("memory_mb") if specs else None
        memory_gb = None
        if isinstance(memory_mb, (int, float)):
            memory_gb = int(round(memory_mb / 1024.0))
        memory_display = memory_gb if memory_gb is not None else (memory_mb if memory_mb not in (None, "N/A") else "")

        subnet_group = db.get("DBSubnetGroup", {}) or {}
        subnet_group_name = subnet_group.get("DBSubnetGroupName")
        subnet_ids = [s.get("SubnetIdentifier") for s in subnet_group.get("Subnets", []) if s.get("SubnetIdentifier")]

        vpc_sec_groups = [sg.get("VpcSecurityGroupId") for sg in db.get("VpcSecurityGroups", []) if sg.get("VpcSecurityGroupId")]

        enhanced_monitoring = "Enabled" if db.get("MonitoringInterval") else "Disabled"

        monitoring_type = ""
        db_cluster_id = db.get("DBClusterIdentifier")
        if db_cluster_id and db_cluster_id in cluster_insights_map:
            di_value = cluster_insights_map[db_cluster_id]
        else:
            di_value = db.get("DatabaseInsightsMode")
        if di_value:
            if isinstance(di_value, str) and di_value.lower() == "standard":
                monitoring_type = "Database Insights - Standard"
            else:
                monitoring_type = f"Database Insights - {str(di_value).capitalize()}"

        ext_support = ""
        cluster_id = db.get("DBClusterIdentifier")
        if cluster_id and cluster_id in cluster_support_map:
            ext_support = cluster_support_map[cluster_id]
        else:
            lifecycle_support = db.get("EngineLifecycleSupport")
            if lifecycle_support:
                if "extended-support-enabled" in lifecycle_support:
                    ext_support = "Enabled"
                elif "extended-support-disabled" in lifecycle_support:
                    ext_support = "Disabled"
                else:
                    ext_support = lifecycle_support
            else:
                ext_support = "Disabled"

        allocated_storage = db.get("AllocatedStorage")
        if db.get("Engine", "").lower().startswith("aurora"):
            allocated_storage = ""

        cluster_param_group = ""
        if cluster_id and cluster_id in cluster_param_map:
            cluster_param_group = cluster_param_map[cluster_id]

        storage_type_display = ""
        if cluster_id and cluster_id in cluster_storage_map:
            cluster_storage = cluster_storage_map[cluster_id]
            storage_type_display = "Aurora I/O-Optimized" if cluster_storage == "aurora-iopt1" else "Aurora Standard"
        else:
            instance_storage = db.get("StorageType")
            if instance_storage:
                storage_type_display = instance_storage

        role = "Instance"
        dbid = db.get("DBInstanceIdentifier")
        if dbid in cluster_instance_role_map:
            is_writer = cluster_instance_role_map[dbid]
            role = "Writer instance" if is_writer else "Reader instance"

        maintenance_window = db.get("PreferredMaintenanceWindow") or ""
        if maintenance_window and not maintenance_window.strip().endswith("UTC"):
            maintenance_window = f"{maintenance_window} UTC"

        dbi_resource_id = db.get("DbiResourceId")
        allocated_storage_gb = float(allocated_storage) if isinstance(allocated_storage, (int, float)) else None

        free_storage_bytes = _avg_cloudwatch_metric(
            cloudwatch,
            "FreeStorageSpace",
            dbid,
            metrics_start,
            metrics_end,
            period_seconds=CW_PERIOD,
        ) if dbid else None
        free_storage_gb = (free_storage_bytes / (1024.0 ** 3)) if isinstance(free_storage_bytes, (int, float)) else None

        used_storage_gb = None
        if isinstance(allocated_storage_gb, (int, float)) and isinstance(free_storage_gb, (int, float)):
            used_storage_gb = max(allocated_storage_gb - free_storage_gb, 0.0)
        elif engine.startswith("aurora") and cluster_id and cluster_id in cluster_volume_used_gb:
            used_storage_gb = cluster_volume_used_gb[cluster_id]

        storage_utilization_percent = None
        if isinstance(allocated_storage_gb, (int, float)) and allocated_storage_gb > 0 and isinstance(used_storage_gb, (int, float)):
            storage_utilization_percent = min((used_storage_gb / allocated_storage_gb) * 100.0, 100.0)

        avg_db_load = None
        if dbi_resource_id and db.get("PerformanceInsightsEnabled"):
            avg_db_load = _avg_db_load(pi_client, dbi_resource_id, metrics_start, metrics_end, period_seconds=PI_PERIOD)

        vcpu_val = specs.get("vcpus") if isinstance(specs, dict) else None
        load_vs_vcpu_percent = None
        if isinstance(vcpu_val, (int, float)) and vcpu_val > 0 and isinstance(avg_db_load, (int, float)):
            load_vs_vcpu_percent = min((avg_db_load / float(vcpu_val)) * 100.0, 100.0)

        optimization_status = "Balanced"
        if not db.get("PerformanceInsightsEnabled"):
            optimization_status = "Performance Insights Disabled"
        elif avg_db_load is None:
            optimization_status = "No Load Data"
        elif load_vs_vcpu_percent is None:
            optimization_status = "No vCPU Data"
        elif load_vs_vcpu_percent >= 85:
            optimization_status = "High Load"
        elif load_vs_vcpu_percent <= 30:
            optimization_status = "Low Load"

        instance_row = {
            "DBInstanceIdentifier": dbid,
            "Role": role,
            "Engine": db.get("Engine"),
            "EngineVersion": db.get("EngineVersion"),
            "ExtededSupport": ext_support,
            "InstanceParameterGroup": ", ".join([p.get("DBParameterGroupName") for p in (db.get("DBParameterGroups") or []) if p.get("DBParameterGroupName")]),
            "ClusterParameterGroup": cluster_param_group,
            "DeletionProtection": db.get("DeletionProtection"),
            "InstanceClass": clazz,
            "vCPU": specs.get("vcpus"),
            "MemoryGB": memory_display,
            "MultiAZ": db.get("MultiAZ"),
            "StorageType": storage_type or ("aurora" if engine.startswith("aurora") else ""),
            "ClusterStorageConfiguration": cluster_storage_config,
            "AllocatedStorageGB": allocated_storage,
            "Iops": int(db.get("Iops")) if db.get("Iops") is not None else "",
            "Throughput": (db.get("StorageThroughput") if db.get("StorageThroughput") not in (None, 0) else ""),
            "StorageAutoscaling": "Enabled" if db.get("MaxAllocatedStorage") else "Disabled",
            "PerformanceInsights": db.get("PerformanceInsightsEnabled"),
            "MonitoringType": monitoring_type,
            "EnhancedMonitoring": enhanced_monitoring,
            "BackupRetentionPeriod": db.get("BackupRetentionPeriod"),
            "PreferredBackupWindow": f"{db.get('PreferredBackupWindow')} UTC" if db.get("PreferredBackupWindow") else "",
            "CopyTagsToSnapshot": "Enabled" if db.get("CopyTagsToSnapshot") else "Disabled",
            "Subnets": ", ".join(subnet_ids),
            "SubnetGroup": subnet_group_name,
            "SecurityGroups": ", ".join(vpc_sec_groups),
            "AutoMinorVersionUpgrade": db.get("AutoMinorVersionUpgrade"),
            "MaxAllocatedStorage": db.get("MaxAllocatedStorage"),
            "MaintenanceWindow": maintenance_window,
            "AvgDBLoad": round(avg_db_load, 3) if isinstance(avg_db_load, (int, float)) else "",
            "FreeStorageGB": round(free_storage_gb, 2) if isinstance(free_storage_gb, (int, float)) else "",
            "UsedStorageGB": round(used_storage_gb, 2) if isinstance(used_storage_gb, (int, float)) else "",
            "StorageUtilizationPercent": round(storage_utilization_percent, 2) if isinstance(storage_utilization_percent, (int, float)) else "",
            "LoadVsVcpuPercent": round(load_vs_vcpu_percent, 2) if isinstance(load_vs_vcpu_percent, (int, float)) else "",
            "OptimizationStatus": optimization_status,
        }

        # ── Cost & Savings (Approach B: real CE per-instance cost) ──────────
        current_monthly_cost = rds_instance_costs.get(dbid, 0.0)
        monthly_savings = _calculate_rds_savings(
            current_monthly_cost,
            load_vs_vcpu_percent if isinstance(load_vs_vcpu_percent, (int, float)) else None,
            optimization_status,
        )
        instance_row["CurrentMonthlyCostUSD"]   = current_monthly_cost
        instance_row["MonthlySavingsUSD"]        = monthly_savings
        instance_row["OptimizedMonthlyCostUSD"]  = round(current_monthly_cost - monthly_savings, 2)

        if cluster_id:
            if cluster_id in cluster_rows:
                cluster_instance_rows.setdefault(cluster_id, []).append(instance_row)
            else:
                orphan_cluster_instances.setdefault(cluster_id, []).append(instance_row)
        else:
            standalone_instances.append(instance_row)

    ordered_rows = []
    for cluster_id in cluster_order:
        cluster_row = cluster_rows.get(cluster_id)
        if cluster_row:
            ordered_rows.append(cluster_row)
        ordered_rows.extend(cluster_instance_rows.get(cluster_id, []))

    # Append any cluster instances whose clusters were not returned earlier
    for orphan_instances in orphan_cluster_instances.values():
        ordered_rows.extend(orphan_instances)

    ordered_rows.extend(standalone_instances)

    rows = ordered_rows

    df = pd.DataFrame(rows)
    desired_order = [
        "DBInstanceIdentifier",
        "Role",
        "Engine",
        "EngineVersion",
        "ExtededSupport",
        "InstanceParameterGroup",
        "ClusterParameterGroup",
        "DeletionProtection",
        "InstanceClass",
        "vCPU",
        "MemoryGB",
        "MultiAZ",
        "StorageType",
        "ClusterStorageConfiguration",
        "AllocatedStorageGB",
        "Iops",
        "Throughput",
        "StorageAutoscaling",
        "MaxAllocatedStorage",
        "MonitoringType",
        "PerformanceInsights",
        "EnhancedMonitoring",
        "AutoMinorVersionUpgrade",
        "MaintenanceWindow",
        "AvgDBLoad",
        "FreeStorageGB",
        "UsedStorageGB",
        "StorageUtilizationPercent",
        "LoadVsVcpuPercent",
        "OptimizationStatus",
        "CurrentMonthlyCostUSD",
        "MonthlySavingsUSD",
        "OptimizedMonthlyCostUSD",
        "BackupRetentionPeriod",
        "CopyTagsToSnapshot",
        "PreferredBackupWindow",
        "Subnets",
        "SubnetGroup",
        "SecurityGroups",
    ]
    for col in desired_order:
        if col not in df.columns:
            df[col] = ""
    df = df[desired_order]
    return df
