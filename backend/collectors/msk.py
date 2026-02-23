"""Amazon MSK collectors."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from aws_utils import safe_call
from config import REGION


def _get_cloudwatch_avg_metric(cloudwatch, cluster_name: str, metric_name: str, days: int = 30) -> float | None:
    """Get average CloudWatch metric for MSK cluster."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)
    
    response = safe_call(
        lambda: cloudwatch.get_metric_statistics(
            Namespace="AWS/Kafka",
            MetricName=metric_name,
            Dimensions=[{"Name": "Cluster Name", "Value": cluster_name}],
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


def collect_msk(session, cost_map):
    kafka = session.client("kafka", region_name=REGION)
    cloudwatch = session.client("cloudwatch", region_name=REGION)
    ec2 = session.client("ec2", region_name=REGION)
    
    rows = []
    clusters = safe_call(lambda: kafka.list_clusters().get("ClusterInfoList", []), [])
    
    for cluster in clusters or []:
        cluster_arn = cluster.get("ClusterArn", "")
        cluster_name = cluster.get("ClusterName", "")
        
        # Get detailed cluster information
        cluster_info = safe_call(
            lambda: kafka.describe_cluster(ClusterArn=cluster_arn).get("ClusterInfo", {}),
            {}
        )
        
        # Extract broker node information
        broker_info = cluster_info.get("BrokerNodeGroupInfo", {})
        instance_type = broker_info.get("InstanceType", "")
        storage_info = broker_info.get("StorageInfo", {})
        ebs_info = storage_info.get("EbsStorageInfo", {})
        
        # Extract security groups
        security_groups = broker_info.get("SecurityGroups", [])
        security_group_str = ", ".join(security_groups) if security_groups else ""
        
        # Extract subnet information
        client_subnets = broker_info.get("ClientSubnets", [])
        subnet_str = ", ".join(client_subnets) if client_subnets else ""
        
        # Encryption settings
        encryption_info = cluster_info.get("EncryptionInfo", {})
        encryption_at_rest = encryption_info.get("EncryptionAtRest", {})
        encryption_in_transit = encryption_info.get("EncryptionInTransit", {})
        
        # Monitoring settings
        logging_info = cluster_info.get("LoggingInfo", {})
        broker_logs = logging_info.get("BrokerLogs", {})
        cloudwatch_logs = broker_logs.get("CloudWatchLogs", {})
        s3_logs = broker_logs.get("S3", {})
        firehose_logs = broker_logs.get("Firehose", {})
        
        monitoring_level = "DEFAULT"
        open_monitoring = cluster_info.get("OpenMonitoring", {})
        if open_monitoring:
            prometheus_info = open_monitoring.get("Prometheus", {})
            jmx_exporter = prometheus_info.get("JmxExporter", {})
            node_exporter = prometheus_info.get("NodeExporter", {})
            if jmx_exporter.get("EnabledInBroker") or node_exporter.get("EnabledInBroker"):
                monitoring_level = "ENHANCED"
        
        enhanced_monitoring = cluster_info.get("EnhancedMonitoring", "DEFAULT")
        
        # CloudWatch metrics
        cpu_user = _get_cloudwatch_avg_metric(cloudwatch, cluster_name, "CpuUser")
        mem_free = _get_cloudwatch_avg_metric(cloudwatch, cluster_name, "MemoryFree")
        kafka_data_logs_disk_used = _get_cloudwatch_avg_metric(cloudwatch, cluster_name, "KafkaDataLogsDiskUsed")
        
        # Calculate optimization status
        optimization_status = ""
        if cpu_user is not None and cpu_user < 20:
            optimization_status = "Low CPU"
        elif kafka_data_logs_disk_used is not None and kafka_data_logs_disk_used < 30:
            optimization_status = "Low Storage Usage"
        
        # Logging status
        logging_enabled = []
        if cloudwatch_logs.get("Enabled"):
            logging_enabled.append("CloudWatch")
        if s3_logs.get("Enabled"):
            logging_enabled.append("S3")
        if firehose_logs.get("Enabled"):
            logging_enabled.append("Firehose")
        logging_status = ", ".join(logging_enabled) if logging_enabled else "Disabled"
        
        # Get cost from cost_map
        monthly_cost = cost_map.get(cluster_name, 0.0) if cost_map else 0.0
        
        rows.append({
            "ClusterName": cluster_name,
            "ClusterArn": cluster_arn,
            "State": cluster.get("State", ""),
            "KafkaVersion": cluster.get("CurrentBrokerSoftwareInfo", {}).get("KafkaVersion", ""),
            "NumberOfBrokerNodes": cluster.get("NumberOfBrokerNodes", ""),
            "InstanceType": instance_type,
            "VolumeSize": ebs_info.get("VolumeSize", ""),
            "ProvisionedThroughput": ebs_info.get("ProvisionedThroughput", {}).get("Enabled", False),
            "ZookeeperConnectString": cluster.get("ZookeeperConnectString", ""),
            "SecurityGroups": security_group_str,
            "Subnets": subnet_str,
            "EncryptionAtRest": "Enabled" if encryption_at_rest.get("DataVolumeKMSKeyId") else "Disabled",
            "EncryptionInTransit": encryption_in_transit.get("ClientBroker", "TLS"),
            "EnhancedMonitoring": enhanced_monitoring,
            "Logging": logging_status,
            "AvgCpuUser": cpu_user if cpu_user is not None else "",
            "AvgMemoryFree": round(mem_free / (1024**3), 2) if mem_free else "",  # Convert to GB
            "AvgDiskUsed": round(kafka_data_logs_disk_used, 2) if kafka_data_logs_disk_used else "",
            "OptimizationStatus": optimization_status,
            "MonthlyCost": monthly_cost,
            "EstimatedSavings": 0.0,  # Can be enhanced with savings logic
        })
    
    return pd.DataFrame(rows)
