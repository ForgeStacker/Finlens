"""
Neptune Collector for FinLens
Collects comprehensive Neptune clusters, instances, and configuration data
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class NeptuneCollector(BaseCollector):
    """Collector for Neptune data"""
    
    category = "database"
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "neptune"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for Neptune data"""
        try:
            self.logger.info(f"[NEPTUNE_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Initialize session manually
            import boto3
            self.session = boto3.Session(
                profile_name=self.profile_name,
                region_name=self.region_name
            )
            neptune_client = self.session.client('neptune', region_name=self.region_name)
            self.logger.info("Neptune client initialized successfully")
            
            self.logger.info("Collecting neptune data...")
            data = {
                "db_clusters": self._collect_db_clusters(neptune_client),
                "db_instances": self._collect_db_instances(neptune_client),
                "db_cluster_snapshots": self._collect_db_cluster_snapshots(neptune_client),
                "db_snapshots": self._collect_db_snapshots(neptune_client),
                "db_subnet_groups": self._collect_db_subnet_groups(neptune_client),
                "db_parameter_groups": self._collect_db_parameter_groups(neptune_client),
                "db_cluster_parameter_groups": self._collect_db_cluster_parameter_groups(neptune_client),
                "event_subscriptions": self._collect_event_subscriptions(neptune_client),
                "pending_maintenance_actions": self._collect_pending_maintenance_actions(neptune_client)
            }
            
            # Count total resources
            total_resources = len(data["db_clusters"]) + len(data["db_instances"])
            
            self.logger.info(f"Collected {total_resources} Neptune resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting Neptune data: {str(e)}")
            return {}
    
    def _collect_db_clusters(self, client) -> List[Dict[str, Any]]:
        """Collect Neptune DB clusters"""
        try:
            clusters = []
            
            response = client.describe_db_clusters()
            for cluster in response.get('DBClusters', []):
                cluster_data = {
                    "availability_zones": cluster.get("AvailabilityZones", []),
                    "backup_retention_period": cluster.get("BackupRetentionPeriod"),
                    "character_set_name": cluster.get("CharacterSetName"),
                    "database_name": cluster.get("DatabaseName"),
                    "db_cluster_identifier": cluster.get("DBClusterIdentifier"),
                    "db_cluster_parameter_group": cluster.get("DBClusterParameterGroup"),
                    "db_subnet_group": cluster.get("DBSubnetGroup"),
                    "status": cluster.get("Status"),
                    "percent_progress": cluster.get("PercentProgress"),
                    "earliest_restorable_time": cluster.get("EarliestRestorableTime").isoformat() if cluster.get("EarliestRestorableTime") else None,
                    "endpoint": cluster.get("Endpoint"),
                    "reader_endpoint": cluster.get("ReaderEndpoint"),
                    "multi_az": cluster.get("MultiAZ"),
                    "engine": cluster.get("Engine"),
                    "engine_version": cluster.get("EngineVersion"),
                    "latest_restorable_time": cluster.get("LatestRestorableTime").isoformat() if cluster.get("LatestRestorableTime") else None,
                    "port": cluster.get("Port"),
                    "master_username": cluster.get("MasterUsername"),
                    "db_cluster_option_group_memberships": cluster.get("DBClusterOptionGroupMemberships", []),
                    "preferred_backup_window": cluster.get("PreferredBackupWindow"),
                    "preferred_maintenance_window": cluster.get("PreferredMaintenanceWindow"),
                    "replication_source_identifier": cluster.get("ReplicationSourceIdentifier"),
                    "read_replica_identifiers": cluster.get("ReadReplicaIdentifiers", []),
                    "db_cluster_members": cluster.get("DBClusterMembers", []),
                    "vpc_security_groups": cluster.get("VpcSecurityGroups", []),
                    "hosted_zone_id": cluster.get("HostedZoneId"),
                    "storage_encrypted": cluster.get("StorageEncrypted"),
                    "kms_key_id": cluster.get("KmsKeyId"),
                    "db_cluster_resource_id": cluster.get("DbClusterResourceId"),
                    "db_cluster_arn": cluster.get("DBClusterArn"),
                    "associated_roles": cluster.get("AssociatedRoles", []),
                    "iam_database_authentication_enabled": cluster.get("IAMDatabaseAuthenticationEnabled"),
                    "clone_group_id": cluster.get("CloneGroupId"),
                    "cluster_create_time": cluster.get("ClusterCreateTime").isoformat() if cluster.get("ClusterCreateTime") else None,
                    "copy_tags_to_snapshot": cluster.get("CopyTagsToSnapshot"),
                    "cross_account_clone": cluster.get("CrossAccountClone"),
                    "enabled_cloudwatch_logs_exports": cluster.get("EnabledCloudwatchLogsExports", []),
                    "pending_modified_values": cluster.get("PendingModifiedValues", {}),
                    "deletion_protection": cluster.get("DeletionProtection"),
                    "serverless_v2_scaling_configuration": cluster.get("ServerlessV2ScalingConfiguration", {}),
                    "global_cluster_identifier": cluster.get("GlobalClusterIdentifier")
                }
                clusters.append(cluster_data)
            
            return clusters
        except Exception as e:
            self.logger.warning(f"Error collecting Neptune clusters: {e}")
            return []
    
    def _collect_db_instances(self, client) -> List[Dict[str, Any]]:
        """Collect Neptune DB instances"""
        try:
            instances = []
            
            response = client.describe_db_instances()
            for instance in response.get('DBInstances', []):
                instance_data = {
                    "db_instance_identifier": instance.get("DBInstanceIdentifier"),
                    "db_instance_class": instance.get("DBInstanceClass"),
                    "engine": instance.get("Engine"),
                    "db_instance_status": instance.get("DBInstanceStatus"),
                    "master_username": instance.get("MasterUsername"),
                    "db_name": instance.get("DBName"),
                    "endpoint": instance.get("Endpoint"),
                    "allocated_storage": instance.get("AllocatedStorage"),
                    "instance_create_time": instance.get("InstanceCreateTime").isoformat() if instance.get("InstanceCreateTime") else None,
                    "preferred_backup_window": instance.get("PreferredBackupWindow"),
                    "backup_retention_period": instance.get("BackupRetentionPeriod"),
                    "db_security_groups": instance.get("DBSecurityGroups", []),
                    "vpc_security_groups": instance.get("VpcSecurityGroups", []),
                    "db_parameter_groups": instance.get("DBParameterGroups", []),
                    "availability_zone": instance.get("AvailabilityZone"),
                    "db_subnet_group": instance.get("DBSubnetGroup"),
                    "preferred_maintenance_window": instance.get("PreferredMaintenanceWindow"),
                    "pending_modified_values": instance.get("PendingModifiedValues", {}),
                    "latest_restorable_time": instance.get("LatestRestorableTime").isoformat() if instance.get("LatestRestorableTime") else None,
                    "multi_az": instance.get("MultiAZ"),
                    "engine_version": instance.get("EngineVersion"),
                    "auto_minor_version_upgrade": instance.get("AutoMinorVersionUpgrade"),
                    "read_replica_source_db_instance_identifier": instance.get("ReadReplicaSourceDBInstanceIdentifier"),
                    "read_replica_db_instance_identifiers": instance.get("ReadReplicaDBInstanceIdentifiers", []),
                    "read_replica_db_cluster_identifiers": instance.get("ReadReplicaDBClusterIdentifiers", []),
                    "license_model": instance.get("LicenseModel"),
                    "iops": instance.get("Iops"),
                    "option_group_memberships": instance.get("OptionGroupMemberships", []),
                    "character_set_name": instance.get("CharacterSetName"),
                    "secondary_availability_zone": instance.get("SecondaryAvailabilityZone"),
                    "publicly_accessible": instance.get("PubliclyAccessible"),
                    "status_infos": instance.get("StatusInfos", []),
                    "storage_type": instance.get("StorageType"),
                    "tde_credential_arn": instance.get("TdeCredentialArn"),
                    "db_instance_port": instance.get("DbInstancePort"),
                    "storage_encrypted": instance.get("StorageEncrypted"),
                    "kms_key_id": instance.get("KmsKeyId"),
                    "dbi_resource_id": instance.get("DbiResourceId"),
                    "ca_certificate_identifier": instance.get("CACertificateIdentifier"),
                    "domain_memberships": instance.get("DomainMemberships", []),
                    "copy_tags_to_snapshot": instance.get("CopyTagsToSnapshot"),
                    "monitoring_interval": instance.get("MonitoringInterval"),
                    "enhanced_monitoring_resource_arn": instance.get("EnhancedMonitoringResourceArn"),
                    "monitoring_role_arn": instance.get("MonitoringRoleArn"),
                    "promotion_tier": instance.get("PromotionTier"),
                    "db_instance_arn": instance.get("DBInstanceArn"),
                    "timezone": instance.get("Timezone"),
                    "iam_database_authentication_enabled": instance.get("IAMDatabaseAuthenticationEnabled"),
                    "performance_insights_enabled": instance.get("PerformanceInsightsEnabled"),
                    "performance_insights_kms_key_id": instance.get("PerformanceInsightsKMSKeyId"),
                    "performance_insights_retention_period": instance.get("PerformanceInsightsRetentionPeriod"),
                    "enabled_cloudwatch_logs_exports": instance.get("EnabledCloudwatchLogsExports", []),
                    "deletion_protection": instance.get("DeletionProtection"),
                    "db_cluster_identifier": instance.get("DBClusterIdentifier")
                }
                instances.append(instance_data)
            
            return instances
        except Exception as e:
            self.logger.warning(f"Error collecting Neptune instances: {e}")
            return []
    
    def _collect_db_cluster_snapshots(self, client) -> List[Dict[str, Any]]:
        """Collect Neptune DB cluster snapshots"""
        try:
            snapshots = []
            
            response = client.describe_db_cluster_snapshots()
            for snapshot in response.get('DBClusterSnapshots', []):
                snapshot_data = {
                    "availability_zones": snapshot.get("AvailabilityZones", []),
                    "db_cluster_snapshot_identifier": snapshot.get("DBClusterSnapshotIdentifier"),
                    "db_cluster_identifier": snapshot.get("DBClusterIdentifier"),
                    "snapshot_create_time": snapshot.get("SnapshotCreateTime").isoformat() if snapshot.get("SnapshotCreateTime") else None,
                    "engine": snapshot.get("Engine"),
                    "allocated_storage": snapshot.get("AllocatedStorage"),
                    "status": snapshot.get("Status"),
                    "port": snapshot.get("Port"),
                    "vpc_id": snapshot.get("VpcId"),
                    "cluster_create_time": snapshot.get("ClusterCreateTime").isoformat() if snapshot.get("ClusterCreateTime") else None,
                    "master_username": snapshot.get("MasterUsername"),
                    "engine_version": snapshot.get("EngineVersion"),
                    "license_model": snapshot.get("LicenseModel"),
                    "snapshot_type": snapshot.get("SnapshotType"),
                    "percent_progress": snapshot.get("PercentProgress"),
                    "storage_encrypted": snapshot.get("StorageEncrypted"),
                    "kms_key_id": snapshot.get("KmsKeyId"),
                    "db_cluster_snapshot_arn": snapshot.get("DBClusterSnapshotArn"),
                    "source_db_cluster_snapshot_arn": snapshot.get("SourceDBClusterSnapshotArn"),
                    "iam_database_authentication_enabled": snapshot.get("IAMDatabaseAuthenticationEnabled")
                }
                snapshots.append(snapshot_data)
            
            return snapshots
        except Exception as e:
            self.logger.warning(f"Error collecting Neptune cluster snapshots: {e}")
            return []
    
    def _collect_db_snapshots(self, client) -> List[Dict[str, Any]]:
        """Collect Neptune DB snapshots"""
        try:
            snapshots = []
            
            response = client.describe_db_snapshots()
            for snapshot in response.get('DBSnapshots', []):
                snapshot_data = {
                    "db_snapshot_identifier": snapshot.get("DBSnapshotIdentifier"),
                    "db_instance_identifier": snapshot.get("DBInstanceIdentifier"),
                    "snapshot_create_time": snapshot.get("SnapshotCreateTime").isoformat() if snapshot.get("SnapshotCreateTime") else None,
                    "engine": snapshot.get("Engine"),
                    "allocated_storage": snapshot.get("AllocatedStorage"),
                    "status": snapshot.get("Status"),
                    "port": snapshot.get("Port"),
                    "availability_zone": snapshot.get("AvailabilityZone"),
                    "vpc_id": snapshot.get("VpcId"),
                    "instance_create_time": snapshot.get("InstanceCreateTime").isoformat() if snapshot.get("InstanceCreateTime") else None,
                    "master_username": snapshot.get("MasterUsername"),
                    "engine_version": snapshot.get("EngineVersion"),
                    "license_model": snapshot.get("LicenseModel"),
                    "snapshot_type": snapshot.get("SnapshotType"),
                    "iops": snapshot.get("Iops"),
                    "option_group_name": snapshot.get("OptionGroupName"),
                    "percent_progress": snapshot.get("PercentProgress"),
                    "source_region": snapshot.get("SourceRegion"),
                    "source_db_snapshot_identifier": snapshot.get("SourceDBSnapshotIdentifier"),
                    "storage_type": snapshot.get("StorageType"),
                    "tde_credential_arn": snapshot.get("TdeCredentialArn"),
                    "encrypted": snapshot.get("Encrypted"),
                    "kms_key_id": snapshot.get("KmsKeyId"),
                    "db_snapshot_arn": snapshot.get("DBSnapshotArn"),
                    "timezone": snapshot.get("Timezone"),
                    "iam_database_authentication_enabled": snapshot.get("IAMDatabaseAuthenticationEnabled")
                }
                snapshots.append(snapshot_data)
            
            return snapshots
        except Exception as e:
            self.logger.warning(f"Error collecting Neptune snapshots: {e}")
            return []
    
    def _collect_db_subnet_groups(self, client) -> List[Dict[str, Any]]:
        """Collect Neptune DB subnet groups"""
        try:
            subnet_groups = []
            
            response = client.describe_db_subnet_groups()
            for sg in response.get('DBSubnetGroups', []):
                sg_data = {
                    "db_subnet_group_name": sg.get("DBSubnetGroupName"),
                    "db_subnet_group_description": sg.get("DBSubnetGroupDescription"),
                    "vpc_id": sg.get("VpcId"),
                    "subnet_group_status": sg.get("SubnetGroupStatus"),
                    "subnets": sg.get("Subnets", []),
                    "db_subnet_group_arn": sg.get("DBSubnetGroupArn")
                }
                subnet_groups.append(sg_data)
            
            return subnet_groups
        except Exception as e:
            self.logger.warning(f"Error collecting Neptune subnet groups: {e}")
            return []
    
    def _collect_db_parameter_groups(self, client) -> List[Dict[str, Any]]:
        """Collect Neptune DB parameter groups"""
        try:
            parameter_groups = []
            
            response = client.describe_db_parameter_groups()
            for pg in response.get('DBParameterGroups', []):
                pg_data = {
                    "db_parameter_group_name": pg.get("DBParameterGroupName"),
                    "db_parameter_group_family": pg.get("DBParameterGroupFamily"),
                    "description": pg.get("Description"),
                    "db_parameter_group_arn": pg.get("DBParameterGroupArn")
                }
                parameter_groups.append(pg_data)
            
            return parameter_groups
        except Exception as e:
            self.logger.warning(f"Error collecting Neptune parameter groups: {e}")
            return []
    
    def _collect_db_cluster_parameter_groups(self, client) -> List[Dict[str, Any]]:
        """Collect Neptune DB cluster parameter groups"""
        try:
            cluster_parameter_groups = []
            
            response = client.describe_db_cluster_parameter_groups()
            for pg in response.get('DBClusterParameterGroups', []):
                pg_data = {
                    "db_cluster_parameter_group_name": pg.get("DBClusterParameterGroupName"),
                    "db_parameter_group_family": pg.get("DBParameterGroupFamily"),
                    "description": pg.get("Description"),
                    "db_cluster_parameter_group_arn": pg.get("DBClusterParameterGroupArn")
                }
                cluster_parameter_groups.append(pg_data)
            
            return cluster_parameter_groups
        except Exception as e:
            self.logger.warning(f"Error collecting Neptune cluster parameter groups: {e}")
            return []
    
    def _collect_event_subscriptions(self, client) -> List[Dict[str, Any]]:
        """Collect Neptune event subscriptions"""
        try:
            subscriptions = []
            
            response = client.describe_event_subscriptions()
            for sub in response.get('EventSubscriptionsList', []):
                sub_data = {
                    "customer_aws_id": sub.get("CustomerAwsId"),
                    "cust_subscription_id": sub.get("CustSubscriptionId"),
                    "sns_topic_arn": sub.get("SnsTopicArn"),
                    "status": sub.get("Status"),
                    "subscription_creation_time": sub.get("SubscriptionCreationTime").isoformat() if sub.get("SubscriptionCreationTime") else None,
                    "source_type": sub.get("SourceType"),
                    "source_ids_list": sub.get("SourceIdsList", []),
                    "event_categories_list": sub.get("EventCategoriesList", []),
                    "enabled": sub.get("Enabled"),
                    "event_subscription_arn": sub.get("EventSubscriptionArn")
                }
                subscriptions.append(sub_data)
            
            return subscriptions
        except Exception as e:
            self.logger.warning(f"Error collecting Neptune event subscriptions: {e}")
            return []
    
    def _collect_pending_maintenance_actions(self, client) -> List[Dict[str, Any]]:
        """Collect Neptune pending maintenance actions"""
        try:
            pending_actions = []
            
            response = client.describe_pending_maintenance_actions()
            for action in response.get('PendingMaintenanceActions', []):
                action_data = {
                    "resource_identifier": action.get("ResourceIdentifier"),
                    "pending_maintenance_action_details": action.get("PendingMaintenanceActionDetails", [])
                }
                pending_actions.append(action_data)
            
            return pending_actions
        except Exception as e:
            self.logger.warning(f"Error collecting Neptune pending maintenance actions: {e}")
            return []