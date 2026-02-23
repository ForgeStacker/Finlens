"""ElastiCache collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import get_instance_type_specs, safe_call
from config import REGION


def collect_elasticache(session, cost_map):
    def format_retention_period(days):
        try:
            days = int(days)
        except Exception:
            return str(days)
        if days == 1:
            return "1 day"
        elif days == 30:
            return "30 days"
        elif days == 365:
            return "1 year"
        elif days > 1:
            return f"{days} days"
        else:
            return "0 days"

    ec = session.client("elasticache", region_name=REGION)
    ec2 = session.client("ec2", region_name=REGION)
    rows = []
    rep_groups = safe_call(lambda: ec.describe_replication_groups().get("ReplicationGroups", []), [])
    rep_group_map = {g["ReplicationGroupId"]: g for g in rep_groups}
    cache_clusters = safe_call(lambda: ec.describe_cache_clusters(ShowCacheNodeInfo=True).get("CacheClusters", []), [])
    clusters_by_group = {}
    for cache_cluster in cache_clusters:
        group_id = cache_cluster.get("ReplicationGroupId")
        if group_id:
            clusters_by_group.setdefault(group_id, []).append(cache_cluster)

    elasticache_type_map = {
        "cache.t4g.micro":  {"vcpus": 2, "memory_mb": 1042},
        "cache.t4g.small":  {"vcpus": 2, "memory_mb": 2137},
        "cache.t4g.medium": {"vcpus": 2, "memory_mb": 3226},
        "cache.t3.micro":  {"vcpus": 2, "memory_mb": 1042},
        "cache.t3.small":  {"vcpus": 2, "memory_mb": 2137},
        "cache.t3.medium": {"vcpus": 2, "memory_mb": 3226},
        "cache.m6g.large": {"vcpus": 2, "memory_mb": 15488},
        "cache.m6g.xlarge": {"vcpus": 4, "memory_mb": 30976},
        "cache.m6g.2xlarge": {"vcpus": 8, "memory_mb": 61952},
        "cache.m6g.4xlarge": {"vcpus": 16, "memory_mb": 123904},
        "cache.m6g.8xlarge": {"vcpus": 32, "memory_mb": 247808},
        "cache.r6g.large": {"vcpus": 2, "memory_mb": 41984},
        "cache.r6g.xlarge": {"vcpus": 4, "memory_mb": 83968},
        "cache.r6g.2xlarge": {"vcpus": 8, "memory_mb": 167936},
        "cache.r6g.4xlarge": {"vcpus": 16, "memory_mb": 335872},
        "cache.r6g.8xlarge": {"vcpus": 32, "memory_mb": 671744},
    }

    for group_id, rep in rep_group_map.items():
        group_clusters = clusters_by_group.get(group_id, [])
        node_type = group_clusters[0].get("CacheNodeType") if group_clusters else rep.get("CacheNodeType", "N/A")
        specs = elasticache_type_map.get(node_type) or get_instance_type_specs(ec2, node_type)
        vcpus = specs.get("vcpus") if specs and specs.get("vcpus") is not None else "N/A"
        memory_mb = specs.get("memory_mb") if specs and specs.get("memory_mb") is not None else "N/A"
        engine_version = rep.get("EngineVersion")
        if not engine_version and group_clusters:
            engine_version = group_clusters[0].get("EngineVersion", "")
        all_nodes = []
        for cache_cluster in group_clusters:
            cluster_id = cache_cluster.get('CacheClusterId')
            param_group = cache_cluster.get("CacheParameterGroup", {}).get("CacheParameterGroupName", "")
            sec_groups = ", ".join([sg.get("SecurityGroupId", "") for sg in cache_cluster.get("SecurityGroups", [])])
            for node in cache_cluster.get("CacheNodes", []):
                node_id = node.get("CacheNodeId")
                all_nodes.append({
                    "NodeId": f"{cluster_id}:{node_id}",
                    "NodeType": cache_cluster.get("CacheNodeType"),
                    "MemoryMB": memory_mb,
                    "vCPU": vcpus,
                    "Status": node.get("CacheNodeStatus"),
                    "ParameterGroup": param_group,
                    "SecurityGroup": sec_groups
                })
        backup_data = rep.get("SnapshotRetentionLimit", "")
        subnet = ", ".join(rep.get("SubnetGroupName", ""))
        security_groups = ", ".join([sg.get("SecurityGroupId", "") for sg in rep.get("SecurityGroups", [])])
        shards = len(rep.get("NodeGroups", []))
        number_of_nodes = sum([len(ng.get("NodeGroupMembers", [])) for ng in rep.get("NodeGroups", [])])
        parameter_group = rep.get("CacheParameterGroup", {}).get("CacheParameterGroupName", "")
        cluster_mode = rep.get("ClusterMode", "")
        multi_az = rep.get("MultiAZ", "")
        auto_failover = rep.get("AutomaticFailover", "")
        configuration = rep.get("ConfigurationEndpoint", {}).get("Address", "")
        rows.append({
            "CacheClusterId": group_id,
            "Engine": rep.get("Engine"),
            "EngineVersion": engine_version or "",
            "MultiAZ": multi_az,
            "Shards": shards,
            "AutoFailover": auto_failover,
            "NumberOfNodes": number_of_nodes,
            "ParameterGroup": parameter_group,
            "SecurityGroup": security_groups,
            "MemoryMB": memory_mb,
            "vCPU": vcpus,
            "AutomaticBackup": ("Disabled" if rep.get("SnapshotRetentionLimit", 0) == 0 else "Enabled"),
            "BackupRetentionPeriod": format_retention_period(rep.get("SnapshotRetentionLimit", "")),
            "BackupWindow": rep.get("SnapshotWindow", "")
        })
        for node in all_nodes:
            rows.append({
                "CacheClusterId": "",
                "Engine": "",
                "EngineVersion": "",
                "MultiAZ": "",
                "NodeType": node["NodeType"],
                "Shards": "",
                "AutoFailover": "",
                "NumberOfNodes": "",
                "ParameterGroup": node.get("ParameterGroup", ""),
                "SecurityGroup": node.get("SecurityGroup", ""),
                "MemoryMB": node["MemoryMB"],
                "vCPU": node["vCPU"],
                "Status": node["Status"],
                "AutomaticBackup": "",
                "BackupRetentionPeriod": "",
                "BackupWindow": ""
            })
    try:
        valkey = session.client("elasticache", region_name=REGION)
        valkey_caches = safe_call(lambda: valkey.describe_serverless_caches().get("ServerlessCaches", []), [])
        for v in valkey_caches:
            rows.append({
                "CacheClusterId": v.get("ServerlessCacheName", ""),
                "Engine": v.get("Engine", ""),
                "EngineVersion": v.get("FullEngineVersion", ""),
                "MultiAZ": "N/A",
                "NodeType": "serverless",
                "Shards": "N/A",
                "AutoFailover": "N/A",
                "NumberOfNodes": "N/A",
                "ParameterGroup": "N/A",
                "SecurityGroup": ", ".join(v.get("SecurityGroupIds", [])),
                "MemoryMB": "N/A",
                "vCPU": "N/A",
                "Status": v.get("Status", ""),
                "AutomaticBackup": ("Disabled" if v.get("SnapshotRetentionLimit", 0) == 0 else "Enabled"),
                "BackupRetentionPeriod": format_retention_period(v.get("SnapshotRetentionLimit", "")),
                "BackupWindow": v.get("DailySnapshotTime", ""),
            })
    except Exception as e:
        print(f"[DEBUG][ElastiCache] Error fetching Valkey serverless caches: {e}")
    return pd.DataFrame(rows)
