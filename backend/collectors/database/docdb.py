"""
DocumentDB Collector for FinLens
Collects comprehensive DocumentDB clusters, instances, and configuration data
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class DocumentDBCollector(BaseCollector):
    """Collector for DocumentDB data"""
    
    category = "database"
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "docdb"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for DocumentDB data"""
        try:
            self.logger.info(f"[DOCDB_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Initialize session manually
            import boto3
            self.session = boto3.Session(
                profile_name=self.profile_name,
                region_name=self.region_name
            )
            docdb_client = self.session.client('docdb', region_name=self.region_name)
            self.logger.info("DocumentDB client initialized successfully")
            
            self.logger.info("Collecting docdb data...")
            data = {
                "db_clusters": self._collect_db_clusters(docdb_client),
                "db_instances": self._collect_db_instances(docdb_client),
                "db_cluster_snapshots": self._collect_db_cluster_snapshots(docdb_client),
                "db_subnet_groups": self._collect_db_subnet_groups(docdb_client),
                "db_parameter_groups": self._collect_db_parameter_groups(docdb_client),
                "db_cluster_parameter_groups": self._collect_db_cluster_parameter_groups(docdb_client),
                "event_subscriptions": self._collect_event_subscriptions(docdb_client),
                "pending_maintenance_actions": self._collect_pending_maintenance_actions(docdb_client),
                "certificates": self._collect_certificates(docdb_client),
                "global_clusters": self._collect_global_clusters(docdb_client)
            }
            
            # Count total resources
            total_resources = len(data["db_clusters"]) + len(data["db_instances"])
            
            self.logger.info(f"Collected {total_resources} DocumentDB resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting DocumentDB data: {str(e)}")
            return {}
    
    def _collect_db_clusters(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB clusters"""
        try:
            clusters = []
            
            response = client.describe_db_clusters()
            for cluster in response.get('DBClusters', []):
                cluster_data = {
                    "availability_zones": cluster.get("AvailabilityZones", []),
                    "backup_retention_period": cluster.get("BackupRetentionPeriod"),
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
                    "preferred_backup_window": cluster.get("PreferredBackupWindow"),
                    "preferred_maintenance_window": cluster.get("PreferredMaintenanceWindow"),
                    "read_replica_identifiers": cluster.get("ReadReplicaIdentifiers", []),
                    "db_cluster_members": cluster.get("DBClusterMembers", []),
                    "vpc_security_groups": cluster.get("VpcSecurityGroups", []),
                    "hosted_zone_id": cluster.get("HostedZoneId"),
                    "storage_encrypted": cluster.get("StorageEncrypted"),
                    "kms_key_id": cluster.get("KmsKeyId"),
                    "db_cluster_resource_id": cluster.get("DbClusterResourceId"),
                    "db_cluster_arn": cluster.get("DBClusterArn"),
                    "associated_roles": cluster.get("AssociatedRoles", []),
                    "cluster_create_time": cluster.get("ClusterCreateTime").isoformat() if cluster.get("ClusterCreateTime") else None,
                    "enabled_cloudwatch_logs_exports": cluster.get("EnabledCloudwatchLogsExports", []),
                    "deletion_protection": cluster.get("DeletionProtection"),
                    "clone_group_id": cluster.get("CloneGroupId"),
                    "backup_policy": cluster.get("BackupPolicy", {}),
                    "restore_to_time": cluster.get("RestoreToTime").isoformat() if cluster.get("RestoreToTime") else None,
                    "restore_type": cluster.get("RestoreType")
                }
                clusters.append(cluster_data)
            
            return clusters
        except Exception as e:
            self.logger.warning(f"Error collecting DocumentDB clusters: {e}")
            return []
    
    def _collect_db_instances(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB instances"""
        try:
            instances = []
            
            response = client.describe_db_instances()
            for instance in response.get('DBInstances', []):
                instance_data = {
                    "db_instance_identifier": instance.get("DBInstanceIdentifier"),
                    "db_instance_class": instance.get("DBInstanceClass"),
                    "engine": instance.get("Engine"),
                    "db_instance_status": instance.get("DBInstanceStatus"),
                    "endpoint": instance.get("Endpoint"),
                    "instance_create_time": instance.get("InstanceCreateTime").isoformat() if instance.get("InstanceCreateTime") else None,
                    "preferred_backup_window": instance.get("PreferredBackupWindow"),
                    "backup_retention_period": instance.get("BackupRetentionPeriod"),
                    "vpc_security_groups": instance.get("VpcSecurityGroups", []),
                    "availability_zone": instance.get("AvailabilityZone"),
                    "db_subnet_group": instance.get("DBSubnetGroup"),
                    "preferred_maintenance_window": instance.get("PreferredMaintenanceWindow"),
                    "pending_modified_values": instance.get("PendingModifiedValues", {}),
                    "latest_restorable_time": instance.get("LatestRestorableTime").isoformat() if instance.get("LatestRestorableTime") else None,
                    "engine_version": instance.get("EngineVersion"),
                    "auto_minor_version_upgrade": instance.get("AutoMinorVersionUpgrade"),
                    "publicly_accessible": instance.get("PubliclyAccessible"),
                    "status_infos": instance.get("StatusInfos", []),
                    "db_cluster_identifier": instance.get("DBClusterIdentifier"),
                    "storage_encrypted": instance.get("StorageEncrypted"),
                    "kms_key_id": instance.get("KmsKeyId"),
                    "dbi_resource_id": instance.get("DbiResourceId"),
                    "ca_certificate_identifier": instance.get("CACertificateIdentifier"),
                    "copy_tags_to_snapshot": instance.get("CopyTagsToSnapshot"),
                    "promotion_tier": instance.get("PromotionTier"),
                    "db_instance_arn": instance.get("DBInstanceArn"),
                    "enabled_cloudwatch_logs_exports": instance.get("EnabledCloudwatchLogsExports", []),
                    "certificate_details": instance.get("CertificateDetails", {}),
                    "performance_insights_enabled": instance.get("PerformanceInsightsEnabled"),
                    "performance_insights_kms_key_id": instance.get("PerformanceInsightsKMSKeyId")
                }
                instances.append(instance_data)
            
            return instances
        except Exception as e:
            self.logger.warning(f"Error collecting DocumentDB instances: {e}")
            return []
    
    def _collect_db_cluster_snapshots(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB cluster snapshots"""
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
                    "status": snapshot.get("Status"),
                    "port": snapshot.get("Port"),
                    "vpc_id": snapshot.get("VpcId"),
                    "cluster_create_time": snapshot.get("ClusterCreateTime").isoformat() if snapshot.get("ClusterCreateTime") else None,
                    "master_username": snapshot.get("MasterUsername"),
                    "engine_version": snapshot.get("EngineVersion"),
                    "snapshot_type": snapshot.get("SnapshotType"),
                    "percent_progress": snapshot.get("PercentProgress"),
                    "storage_encrypted": snapshot.get("StorageEncrypted"),
                    "kms_key_id": snapshot.get("KmsKeyId"),
                    "db_cluster_snapshot_arn": snapshot.get("DBClusterSnapshotArn"),
                    "source_db_cluster_snapshot_arn": snapshot.get("SourceDBClusterSnapshotArn"),
                    "storage_type": snapshot.get("StorageType")
                }
                snapshots.append(snapshot_data)
            
            return snapshots
        except Exception as e:
            self.logger.warning(f"Error collecting DocumentDB cluster snapshots: {e}")
            return []
    
    def _collect_db_subnet_groups(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB subnet groups"""
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
            self.logger.warning(f"Error collecting DocumentDB subnet groups: {e}")
            return []
    
    def _collect_db_parameter_groups(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB parameter groups"""
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
            self.logger.warning(f"Error collecting DocumentDB parameter groups: {e}")
            return []
    
    def _collect_db_cluster_parameter_groups(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB cluster parameter groups"""
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
            self.logger.warning(f"Error collecting DocumentDB cluster parameter groups: {e}")
            return []
    
    def _collect_event_subscriptions(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB event subscriptions"""
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
            self.logger.warning(f"Error collecting DocumentDB event subscriptions: {e}")
            return []
    
    def _collect_pending_maintenance_actions(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB pending maintenance actions"""
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
            self.logger.warning(f"Error collecting DocumentDB pending maintenance actions: {e}")
            return []
    
    def _collect_certificates(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB certificates"""
        try:
            certificates = []
            
            response = client.describe_certificates()
            for cert in response.get('Certificates', []):
                cert_data = {
                    "certificate_identifier": cert.get("CertificateIdentifier"),
                    "certificate_type": cert.get("CertificateType"),
                    "thumbprint": cert.get("Thumbprint"),
                    "valid_from": cert.get("ValidFrom").isoformat() if cert.get("ValidFrom") else None,
                    "valid_till": cert.get("ValidTill").isoformat() if cert.get("ValidTill") else None,
                    "certificate_arn": cert.get("CertificateArn")
                }
                certificates.append(cert_data)
            
            return certificates
        except Exception as e:
            self.logger.warning(f"Error collecting DocumentDB certificates: {e}")
            return []
    
    def _collect_global_clusters(self, client) -> List[Dict[str, Any]]:
        """Collect DocumentDB global clusters"""
        try:
            global_clusters = []
            
            response = client.describe_global_clusters()
            for cluster in response.get('GlobalClusters', []):
                cluster_data = {
                    "global_cluster_identifier": cluster.get("GlobalClusterIdentifier"),
                    "global_cluster_resource_id": cluster.get("GlobalClusterResourceId"),
                    "global_cluster_arn": cluster.get("GlobalClusterArn"),
                    "status": cluster.get("Status"),
                    "engine": cluster.get("Engine"),
                    "engine_version": cluster.get("EngineVersion"),
                    "database_name": cluster.get("DatabaseName"),
                    "storage_encrypted": cluster.get("StorageEncrypted"),
                    "deletion_protection": cluster.get("DeletionProtection"),
                    "global_cluster_members": cluster.get("GlobalClusterMembers", [])
                }
                global_clusters.append(cluster_data)
            
            return global_clusters
        except Exception as e:
            self.logger.warning(f"Error collecting DocumentDB global clusters: {e}")
            return []