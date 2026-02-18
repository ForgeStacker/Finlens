"""
ElastiCache Collector for FinLens
Collects comprehensive ElastiCache clusters, replication groups, and configuration data
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class ElastiCacheCollector(BaseCollector):
    """Collector for ElastiCache data"""
    
    category = "database"
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "elasticache"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for ElastiCache data"""
        try:
            self.logger.info(f"[ELASTICACHE_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Initialize session manually
            import boto3
            self.session = boto3.Session(
                profile_name=self.profile_name,
                region_name=self.region_name
            )
            elasticache_client = self.session.client('elasticache', region_name=self.region_name)
            self.logger.info("ElastiCache client initialized successfully")
            
            self.logger.info("Collecting elasticache data...")
            data = {
                "cache_clusters": self._collect_cache_clusters(elasticache_client),
                "replication_groups": self._collect_replication_groups(elasticache_client),
                "cache_subnet_groups": self._collect_cache_subnet_groups(elasticache_client),
                "cache_parameter_groups": self._collect_cache_parameter_groups(elasticache_client),
                "cache_security_groups": self._collect_cache_security_groups(elasticache_client),
                "snapshots": self._collect_snapshots(elasticache_client),
                "users": self._collect_users(elasticache_client),
                "user_groups": self._collect_user_groups(elasticache_client)
            }
            
            # Count total resources
            total_resources = len(data["cache_clusters"]) + len(data["replication_groups"])
            
            self.logger.info(f"Collected {total_resources} ElastiCache resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting ElastiCache data: {str(e)}")
            return {}
    
    def _collect_cache_clusters(self, client) -> List[Dict[str, Any]]:
        """Collect ElastiCache clusters"""
        try:
            clusters = []
            
            response = client.describe_cache_clusters(ShowCacheNodeInfo=True)
            for cluster in response.get('CacheClusters', []):
                cluster_data = {
                    "cache_cluster_id": cluster.get("CacheClusterId"),
                    "configuration_endpoint": cluster.get("ConfigurationEndpoint"),
                    "client_download_landing_page": cluster.get("ClientDownloadLandingPage"),
                    "cache_node_type": cluster.get("CacheNodeType"),
                    "engine": cluster.get("Engine"),
                    "engine_version": cluster.get("EngineVersion"),
                    "cache_cluster_status": cluster.get("CacheClusterStatus"),
                    "num_cache_nodes": cluster.get("NumCacheNodes"),
                    "preferred_availability_zone": cluster.get("PreferredAvailabilityZone"),
                    "preferred_outpost_arn": cluster.get("PreferredOutpostArn"),
                    "cache_cluster_create_time": cluster.get("CacheClusterCreateTime").isoformat() if cluster.get("CacheClusterCreateTime") else None,
                    "preferred_maintenance_window": cluster.get("PreferredMaintenanceWindow"),
                    "pending_modified_values": cluster.get("PendingModifiedValues", {}),
                    "notification_configuration": cluster.get("NotificationConfiguration", {}),
                    "cache_security_groups": cluster.get("CacheSecurityGroups", []),
                    "cache_parameter_group": cluster.get("CacheParameterGroup", {}),
                    "cache_subnet_group_name": cluster.get("CacheSubnetGroupName"),
                    "cache_nodes": cluster.get("CacheNodes", []),
                    "auto_minor_version_upgrade": cluster.get("AutoMinorVersionUpgrade"),
                    "security_groups": cluster.get("SecurityGroups", []),
                    "replication_group_id": cluster.get("ReplicationGroupId"),
                    "snapshot_retention_limit": cluster.get("SnapshotRetentionLimit"),
                    "snapshot_window": cluster.get("SnapshotWindow"),
                    "auth_token_enabled": cluster.get("AuthTokenEnabled"),
                    "auth_token_last_modified_date": cluster.get("AuthTokenLastModifiedDate").isoformat() if cluster.get("AuthTokenLastModifiedDate") else None,
                    "transit_encryption_enabled": cluster.get("TransitEncryptionEnabled"),
                    "at_rest_encryption_enabled": cluster.get("AtRestEncryptionEnabled"),
                    "arn": cluster.get("ARN"),
                    "replication_group_log_delivery_enabled": cluster.get("ReplicationGroupLogDeliveryEnabled"),
                    "log_delivery_configurations": cluster.get("LogDeliveryConfigurations", []),
                    "network_type": cluster.get("NetworkType"),
                    "ip_discovery": cluster.get("IpDiscovery"),
                    "transit_encryption_mode": cluster.get("TransitEncryptionMode")
                }
                clusters.append(cluster_data)
            
            return clusters
        except Exception as e:
            self.logger.warning(f"Error collecting ElastiCache clusters: {e}")
            return []
    
    def _collect_replication_groups(self, client) -> List[Dict[str, Any]]:
        """Collect ElastiCache replication groups"""
        try:
            replication_groups = []
            
            response = client.describe_replication_groups()
            for rg in response.get('ReplicationGroups', []):
                rg_data = {
                    "replication_group_id": rg.get("ReplicationGroupId"),
                    "description": rg.get("Description"),
                    "global_replication_group_info": rg.get("GlobalReplicationGroupInfo", {}),
                    "status": rg.get("Status"),
                    "pending_modified_values": rg.get("PendingModifiedValues", {}),
                    "member_clusters": rg.get("MemberClusters", []),
                    "node_groups": rg.get("NodeGroups", []),
                    "snapshotting_cluster_id": rg.get("SnapshottingClusterId"),
                    "automatic_failover": rg.get("AutomaticFailover"),
                    "multi_az": rg.get("MultiAZ"),
                    "configuration_endpoint": rg.get("ConfigurationEndpoint"),
                    "snapshot_retention_limit": rg.get("SnapshotRetentionLimit"),
                    "snapshot_window": rg.get("SnapshotWindow"),
                    "cluster_enabled": rg.get("ClusterEnabled"),
                    "cache_node_type": rg.get("CacheNodeType"),
                    "auth_token_enabled": rg.get("AuthTokenEnabled"),
                    "auth_token_last_modified_date": rg.get("AuthTokenLastModifiedDate").isoformat() if rg.get("AuthTokenLastModifiedDate") else None,
                    "transit_encryption_enabled": rg.get("TransitEncryptionEnabled"),
                    "at_rest_encryption_enabled": rg.get("AtRestEncryptionEnabled"),
                    "member_clusters_outpost_arns": rg.get("MemberClustersOutpostArns", []),
                    "kms_key_id": rg.get("KmsKeyId"),
                    "arn": rg.get("ARN"),
                    "user_group_ids": rg.get("UserGroupIds", []),
                    "log_delivery_configurations": rg.get("LogDeliveryConfigurations", []),
                    "replication_group_create_time": rg.get("ReplicationGroupCreateTime").isoformat() if rg.get("ReplicationGroupCreateTime") else None,
                    "data_tiering": rg.get("DataTiering"),
                    "auto_minor_version_upgrade": rg.get("AutoMinorVersionUpgrade"),
                    "network_type": rg.get("NetworkType"),
                    "ip_discovery": rg.get("IpDiscovery"),
                    "transit_encryption_mode": rg.get("TransitEncryptionMode"),
                    "cluster_mode": rg.get("ClusterMode")
                }
                replication_groups.append(rg_data)
            
            return replication_groups
        except Exception as e:
            self.logger.warning(f"Error collecting ElastiCache replication groups: {e}")
            return []
    
    def _collect_cache_subnet_groups(self, client) -> List[Dict[str, Any]]:
        """Collect ElastiCache subnet groups"""
        try:
            subnet_groups = []
            
            response = client.describe_cache_subnet_groups()
            for sg in response.get('CacheSubnetGroups', []):
                sg_data = {
                    "cache_subnet_group_name": sg.get("CacheSubnetGroupName"),
                    "cache_subnet_group_description": sg.get("CacheSubnetGroupDescription"),
                    "vpc_id": sg.get("VpcId"),
                    "subnets": sg.get("Subnets", []),
                    "arn": sg.get("ARN"),
                    "supported_network_types": sg.get("SupportedNetworkTypes", [])
                }
                subnet_groups.append(sg_data)
            
            return subnet_groups
        except Exception as e:
            self.logger.warning(f"Error collecting ElastiCache subnet groups: {e}")
            return []
    
    def _collect_cache_parameter_groups(self, client) -> List[Dict[str, Any]]:
        """Collect ElastiCache parameter groups"""
        try:
            parameter_groups = []
            
            response = client.describe_cache_parameter_groups()
            for pg in response.get('CacheParameterGroups', []):
                pg_data = {
                    "cache_parameter_group_name": pg.get("CacheParameterGroupName"),
                    "cache_parameter_group_family": pg.get("CacheParameterGroupFamily"),
                    "description": pg.get("Description"),
                    "is_global": pg.get("IsGlobal"),
                    "arn": pg.get("ARN")
                }
                parameter_groups.append(pg_data)
            
            return parameter_groups
        except Exception as e:
            self.logger.warning(f"Error collecting ElastiCache parameter groups: {e}")
            return []
    
    def _collect_cache_security_groups(self, client) -> List[Dict[str, Any]]:
        """Collect ElastiCache security groups"""
        try:
            security_groups = []
            
            response = client.describe_cache_security_groups()
            for sg in response.get('CacheSecurityGroups', []):
                sg_data = {
                    "owner_id": sg.get("OwnerId"),
                    "cache_security_group_name": sg.get("CacheSecurityGroupName"),
                    "description": sg.get("Description"),
                    "ec2_security_groups": sg.get("EC2SecurityGroups", []),
                    "arn": sg.get("ARN")
                }
                security_groups.append(sg_data)
            
            return security_groups
        except Exception as e:
            self.logger.warning(f"Error collecting ElastiCache security groups: {e}")
            return []
    
    def _collect_snapshots(self, client) -> List[Dict[str, Any]]:
        """Collect ElastiCache snapshots"""
        try:
            snapshots = []
            
            response = client.describe_snapshots()
            for snapshot in response.get('Snapshots', []):
                snapshot_data = {
                    "snapshot_name": snapshot.get("SnapshotName"),
                    "replication_group_id": snapshot.get("ReplicationGroupId"),
                    "replication_group_description": snapshot.get("ReplicationGroupDescription"),
                    "cache_cluster_id": snapshot.get("CacheClusterId"),
                    "snapshot_status": snapshot.get("SnapshotStatus"),
                    "snapshot_source": snapshot.get("SnapshotSource"),
                    "cache_node_type": snapshot.get("CacheNodeType"),
                    "engine": snapshot.get("Engine"),
                    "engine_version": snapshot.get("EngineVersion"),
                    "num_cache_nodes": snapshot.get("NumCacheNodes"),
                    "preferred_availability_zone": snapshot.get("PreferredAvailabilityZone"),
                    "preferred_outpost_arn": snapshot.get("PreferredOutpostArn"),
                    "cache_cluster_create_time": snapshot.get("CacheClusterCreateTime").isoformat() if snapshot.get("CacheClusterCreateTime") else None,
                    "preferred_maintenance_window": snapshot.get("PreferredMaintenanceWindow"),
                    "topic_arn": snapshot.get("TopicArn"),
                    "port": snapshot.get("Port"),
                    "cache_parameter_group_name": snapshot.get("CacheParameterGroupName"),
                    "cache_subnet_group_name": snapshot.get("CacheSubnetGroupName"),
                    "vpc_id": snapshot.get("VpcId"),
                    "auto_minor_version_upgrade": snapshot.get("AutoMinorVersionUpgrade"),
                    "snapshot_retention_limit": snapshot.get("SnapshotRetentionLimit"),
                    "snapshot_window": snapshot.get("SnapshotWindow"),
                    "num_node_groups": snapshot.get("NumNodeGroups"),
                    "automatic_failover": snapshot.get("AutomaticFailover"),
                    "node_snapshots": snapshot.get("NodeSnapshots", []),
                    "kms_key_id": snapshot.get("KmsKeyId"),
                    "arn": snapshot.get("ARN"),
                    "data_tiering": snapshot.get("DataTiering")
                }
                snapshots.append(snapshot_data)
            
            return snapshots
        except Exception as e:
            self.logger.warning(f"Error collecting ElastiCache snapshots: {e}")
            return []
    
    def _collect_users(self, client) -> List[Dict[str, Any]]:
        """Collect ElastiCache users"""
        try:
            users = []
            
            response = client.describe_users()
            for user in response.get('Users', []):
                user_data = {
                    "user_id": user.get("UserId"),
                    "user_name": user.get("UserName"),
                    "status": user.get("Status"),
                    "engine": user.get("Engine"),
                    "minimum_engine_version": user.get("MinimumEngineVersion"),
                    "access_string": user.get("AccessString"),
                    "user_group_ids": user.get("UserGroupIds", []),
                    "authentication": user.get("Authentication", {}),
                    "arn": user.get("ARN")
                }
                users.append(user_data)
            
            return users
        except Exception as e:
            self.logger.warning(f"Error collecting ElastiCache users: {e}")
            return []
    
    def _collect_user_groups(self, client) -> List[Dict[str, Any]]:
        """Collect ElastiCache user groups"""
        try:
            user_groups = []
            
            response = client.describe_user_groups()
            for ug in response.get('UserGroups', []):
                ug_data = {
                    "user_group_id": ug.get("UserGroupId"),
                    "status": ug.get("Status"),
                    "engine": ug.get("Engine"),
                    "user_ids": ug.get("UserIds", []),
                    "minimum_engine_version": ug.get("MinimumEngineVersion"),
                    "pending_changes": ug.get("PendingChanges", {}),
                    "replication_groups": ug.get("ReplicationGroups", []),
                    "serverless_caches": ug.get("ServerlessCaches", []),
                    "arn": ug.get("ARN")
                }
                user_groups.append(ug_data)
            
            return user_groups
        except Exception as e:
            self.logger.warning(f"Error collecting ElastiCache user groups: {e}")
            return []