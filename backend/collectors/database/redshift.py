"""
Redshift Collector for FinLens
Collects comprehensive Redshift clusters, snapshots, and configuration data
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class RedshiftCollector(BaseCollector):
    """Collector for Redshift data"""
    
    category = "database"
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "redshift"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for Redshift data"""
        try:
            self.logger.info(f"[REDSHIFT_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Initialize session manually
            import boto3
            self.session = boto3.Session(
                profile_name=self.profile_name,
                region_name=self.region_name
            )
            redshift_client = self.session.client('redshift', region_name=self.region_name)
            self.logger.info("Redshift client initialized successfully")
            
            self.logger.info("Collecting redshift data...")
            data = {
                "clusters": self._collect_clusters(redshift_client),
                "snapshots": self._collect_snapshots(redshift_client),
                "cluster_subnet_groups": self._collect_cluster_subnet_groups(redshift_client),
                "cluster_parameter_groups": self._collect_cluster_parameter_groups(redshift_client),
                "cluster_security_groups": self._collect_cluster_security_groups(redshift_client),
                "event_subscriptions": self._collect_event_subscriptions(redshift_client),
                "hsm_configurations": self._collect_hsm_configurations(redshift_client),
                "hsm_client_certificates": self._collect_hsm_client_certificates(redshift_client),
                "scheduled_actions": self._collect_scheduled_actions(redshift_client),
                "usage_limits": self._collect_usage_limits(redshift_client)
            }
            
            # Count total resources
            total_resources = len(data["clusters"]) + len(data["snapshots"])
            
            self.logger.info(f"Collected {total_resources} Redshift resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting Redshift data: {str(e)}")
            return {}
    
    def _collect_clusters(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift clusters"""
        try:
            clusters = []
            
            response = client.describe_clusters()
            for cluster in response.get('Clusters', []):
                cluster_data = {
                    "cluster_identifier": cluster.get("ClusterIdentifier"),
                    "node_type": cluster.get("NodeType"),
                    "cluster_status": cluster.get("ClusterStatus"),
                    "cluster_availability_status": cluster.get("ClusterAvailabilityStatus"),
                    "modify_status": cluster.get("ModifyStatus"),
                    "master_username": cluster.get("MasterUsername"),
                    "db_name": cluster.get("DBName"),
                    "endpoint": cluster.get("Endpoint"),
                    "cluster_create_time": cluster.get("ClusterCreateTime").isoformat() if cluster.get("ClusterCreateTime") else None,
                    "automated_snapshot_retention_period": cluster.get("AutomatedSnapshotRetentionPeriod"),
                    "manual_snapshot_retention_period": cluster.get("ManualSnapshotRetentionPeriod"),
                    "cluster_security_groups": cluster.get("ClusterSecurityGroups", []),
                    "vpc_security_groups": cluster.get("VpcSecurityGroups", []),
                    "cluster_parameter_groups": cluster.get("ClusterParameterGroups", []),
                    "cluster_subnet_group_name": cluster.get("ClusterSubnetGroupName"),
                    "vpc_id": cluster.get("VpcId"),
                    "availability_zone": cluster.get("AvailabilityZone"),
                    "preferred_maintenance_window": cluster.get("PreferredMaintenanceWindow"),
                    "pending_modified_values": cluster.get("PendingModifiedValues", {}),
                    "cluster_version": cluster.get("ClusterVersion"),
                    "allow_version_upgrade": cluster.get("AllowVersionUpgrade"),
                    "number_of_nodes": cluster.get("NumberOfNodes"),
                    "publicly_accessible": cluster.get("PubliclyAccessible"),
                    "encrypted": cluster.get("Encrypted"),
                    "restore_status": cluster.get("RestoreStatus", {}),
                    "data_transfer_progress": cluster.get("DataTransferProgress", {}),
                    "hsm_status": cluster.get("HsmStatus", {}),
                    "cluster_snapshot_copy_status": cluster.get("ClusterSnapshotCopyStatus", {}),
                    "cluster_public_key": cluster.get("ClusterPublicKey"),
                    "cluster_nodes": cluster.get("ClusterNodes", []),
                    "elastic_ip_status": cluster.get("ElasticIpStatus", {}),
                    "cluster_revision_number": cluster.get("ClusterRevisionNumber"),
                    "tags": cluster.get("Tags", []),
                    "kms_key_id": cluster.get("KmsKeyId"),
                    "enhanced_vpc_routing": cluster.get("EnhancedVpcRouting"),
                    "iam_roles": cluster.get("IamRoles", []),
                    "pending_actions": cluster.get("PendingActions", []),
                    "maintenance_track_name": cluster.get("MaintenanceTrackName"),
                    "elastic_resize_number_of_node_options": cluster.get("ElasticResizeNumberOfNodeOptions"),
                    "deferred_maintenance_windows": cluster.get("DeferredMaintenanceWindows", []),
                    "snapshot_schedule_identifier": cluster.get("SnapshotScheduleIdentifier"),
                    "snapshot_schedule_state": cluster.get("SnapshotScheduleState"),
                    "expected_next_snapshot_schedule_time": cluster.get("ExpectedNextSnapshotScheduleTime").isoformat() if cluster.get("ExpectedNextSnapshotScheduleTime") else None,
                    "expected_next_snapshot_schedule_time_status": cluster.get("ExpectedNextSnapshotScheduleTimeStatus"),
                    "next_maintenance_window_start_time": cluster.get("NextMaintenanceWindowStartTime").isoformat() if cluster.get("NextMaintenanceWindowStartTime") else None,
                    "resize_info": cluster.get("ResizeInfo", {}),
                    "availability_zone_relocation_status": cluster.get("AvailabilityZoneRelocationStatus"),
                    "cluster_namespace_arn": cluster.get("ClusterNamespaceArn"),
                    "total_storage_capacity_in_mega_bytes": cluster.get("TotalStorageCapacityInMegaBytes"),
                    "aqua_configuration": cluster.get("AquaConfiguration", {}),
                    "default_iam_role_arn": cluster.get("DefaultIamRoleArn"),
                    "reserved_node_exchange_status": cluster.get("ReservedNodeExchangeStatus", {}),
                    "custom_domain_name": cluster.get("CustomDomainName"),
                    "custom_domain_certificate_arn": cluster.get("CustomDomainCertificateArn"),
                    "custom_domain_certificate_expiry_date": cluster.get("CustomDomainCertificateExpiryDate").isoformat() if cluster.get("CustomDomainCertificateExpiryDate") else None,
                    "master_password_secret_arn": cluster.get("MasterPasswordSecretArn"),
                    "master_password_secret_kms_key_id": cluster.get("MasterPasswordSecretKmsKeyId"),
                    "ip_address_type": cluster.get("IpAddressType"),
                    "multi_az": cluster.get("MultiAZ"),
                    "multi_az_secondary": cluster.get("MultiAZSecondary", {})
                }
                clusters.append(cluster_data)
            
            return clusters
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift clusters: {e}")
            return []
    
    def _collect_snapshots(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift snapshots"""
        try:
            snapshots = []
            
            response = client.describe_cluster_snapshots()
            for snapshot in response.get('Snapshots', []):
                snapshot_data = {
                    "snapshot_identifier": snapshot.get("SnapshotIdentifier"),
                    "cluster_identifier": snapshot.get("ClusterIdentifier"),
                    "snapshot_create_time": snapshot.get("SnapshotCreateTime").isoformat() if snapshot.get("SnapshotCreateTime") else None,
                    "status": snapshot.get("Status"),
                    "port": snapshot.get("Port"),
                    "availability_zone": snapshot.get("AvailabilityZone"),
                    "cluster_create_time": snapshot.get("ClusterCreateTime").isoformat() if snapshot.get("ClusterCreateTime") else None,
                    "master_username": snapshot.get("MasterUsername"),
                    "cluster_version": snapshot.get("ClusterVersion"),
                    "engine_full_version": snapshot.get("EngineFullVersion"),
                    "snapshot_type": snapshot.get("SnapshotType"),
                    "node_type": snapshot.get("NodeType"),
                    "number_of_nodes": snapshot.get("NumberOfNodes"),
                    "db_name": snapshot.get("DBName"),
                    "vpc_id": snapshot.get("VpcId"),
                    "encrypted": snapshot.get("Encrypted"),
                    "kms_key_id": snapshot.get("KmsKeyId"),
                    "encrypted_with_hsm": snapshot.get("EncryptedWithHSM"),
                    "accounts_with_restore_access": snapshot.get("AccountsWithRestoreAccess", []),
                    "owner_account": snapshot.get("OwnerAccount"),
                    "total_backup_size_in_mega_bytes": snapshot.get("TotalBackupSizeInMegaBytes"),
                    "actual_incremental_backup_size_in_mega_bytes": snapshot.get("ActualIncrementalBackupSizeInMegaBytes"),
                    "backup_progress_in_mega_bytes": snapshot.get("BackupProgressInMegaBytes"),
                    "current_backup_rate_in_mega_bytes_per_second": snapshot.get("CurrentBackupRateInMegaBytesPerSecond"),
                    "estimated_seconds_to_completion": snapshot.get("EstimatedSecondsToCompletion"),
                    "elapsed_time_in_seconds": snapshot.get("ElapsedTimeInSeconds"),
                    "source_region": snapshot.get("SourceRegion"),
                    "tags": snapshot.get("Tags", []),
                    "restorable_node_types": snapshot.get("RestorableNodeTypes", []),
                    "enhanced_vpc_routing": snapshot.get("EnhancedVpcRouting"),
                    "maintenance_track_name": snapshot.get("MaintenanceTrackName"),
                    "manual_snapshot_retention_period": snapshot.get("ManualSnapshotRetentionPeriod"),
                    "manual_snapshot_remaining_days": snapshot.get("ManualSnapshotRemainingDays"),
                    "snapshot_retention_start_time": snapshot.get("SnapshotRetentionStartTime").isoformat() if snapshot.get("SnapshotRetentionStartTime") else None,
                    "master_password_secret_arn": snapshot.get("MasterPasswordSecretArn"),
                    "master_password_secret_kms_key_id": snapshot.get("MasterPasswordSecretKmsKeyId")
                }
                snapshots.append(snapshot_data)
            
            return snapshots
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift snapshots: {e}")
            return []
    
    def _collect_cluster_subnet_groups(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift cluster subnet groups"""
        try:
            subnet_groups = []
            
            response = client.describe_cluster_subnet_groups()
            for sg in response.get('ClusterSubnetGroups', []):
                sg_data = {
                    "cluster_subnet_group_name": sg.get("ClusterSubnetGroupName"),
                    "description": sg.get("Description"),
                    "vpc_id": sg.get("VpcId"),
                    "subnet_group_status": sg.get("SubnetGroupStatus"),
                    "subnets": sg.get("Subnets", []),
                    "tags": sg.get("Tags", []),
                    "supported_cluster_ip_address_types": sg.get("SupportedClusterIpAddressTypes", [])
                }
                subnet_groups.append(sg_data)
            
            return subnet_groups
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift subnet groups: {e}")
            return []
    
    def _collect_cluster_parameter_groups(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift cluster parameter groups"""
        try:
            parameter_groups = []
            
            response = client.describe_cluster_parameter_groups()
            for pg in response.get('ParameterGroups', []):
                pg_data = {
                    "parameter_group_name": pg.get("ParameterGroupName"),
                    "parameter_group_family": pg.get("ParameterGroupFamily"),
                    "description": pg.get("Description"),
                    "tags": pg.get("Tags", [])
                }
                parameter_groups.append(pg_data)
            
            return parameter_groups
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift parameter groups: {e}")
            return []
    
    def _collect_cluster_security_groups(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift cluster security groups"""
        try:
            security_groups = []
            
            response = client.describe_cluster_security_groups()
            for sg in response.get('ClusterSecurityGroups', []):
                sg_data = {
                    "cluster_security_group_name": sg.get("ClusterSecurityGroupName"),
                    "description": sg.get("Description"),
                    "ec2_security_groups": sg.get("EC2SecurityGroups", []),
                    "ip_ranges": sg.get("IPRanges", []),
                    "tags": sg.get("Tags", [])
                }
                security_groups.append(sg_data)
            
            return security_groups
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift security groups: {e}")
            return []
    
    def _collect_event_subscriptions(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift event subscriptions"""
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
                    "severity": sub.get("Severity"),
                    "enabled": sub.get("Enabled"),
                    "tags": sub.get("Tags", [])
                }
                subscriptions.append(sub_data)
            
            return subscriptions
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift event subscriptions: {e}")
            return []
    
    def _collect_hsm_configurations(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift HSM configurations"""
        try:
            hsm_configs = []
            
            response = client.describe_hsm_configurations()
            for hsm in response.get('HsmConfigurations', []):
                hsm_data = {
                    "hsm_configuration_identifier": hsm.get("HsmConfigurationIdentifier"),
                    "description": hsm.get("Description"),
                    "hsm_ip_address": hsm.get("HsmIpAddress"),
                    "hsm_partition_name": hsm.get("HsmPartitionName"),
                    "tags": hsm.get("Tags", [])
                }
                hsm_configs.append(hsm_data)
            
            return hsm_configs
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift HSM configurations: {e}")
            return []
    
    def _collect_hsm_client_certificates(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift HSM client certificates"""
        try:
            certificates = []
            
            response = client.describe_hsm_client_certificates()
            for cert in response.get('HsmClientCertificates', []):
                cert_data = {
                    "hsm_client_certificate_identifier": cert.get("HsmClientCertificateIdentifier"),
                    "hsm_client_certificate_public_key": cert.get("HsmClientCertificatePublicKey"),
                    "tags": cert.get("Tags", [])
                }
                certificates.append(cert_data)
            
            return certificates
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift HSM client certificates: {e}")
            return []
    
    def _collect_scheduled_actions(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift scheduled actions"""
        try:
            actions = []
            
            response = client.describe_scheduled_actions()
            for action in response.get('ScheduledActions', []):
                action_data = {
                    "scheduled_action_name": action.get("ScheduledActionName"),
                    "target_action": action.get("TargetAction", {}),
                    "schedule": action.get("Schedule"),
                    "iam_role": action.get("IamRole"),
                    "scheduled_action_description": action.get("ScheduledActionDescription"),
                    "state": action.get("State"),
                    "next_invocations": [inv.isoformat() if inv else None for inv in action.get("NextInvocations", [])],
                    "start_time": action.get("StartTime").isoformat() if action.get("StartTime") else None,
                    "end_time": action.get("EndTime").isoformat() if action.get("EndTime") else None
                }
                actions.append(action_data)
            
            return actions
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift scheduled actions: {e}")
            return []
    
    def _collect_usage_limits(self, client) -> List[Dict[str, Any]]:
        """Collect Redshift usage limits"""
        try:
            limits = []
            
            response = client.describe_usage_limits()
            for limit in response.get('UsageLimits', []):
                limit_data = {
                    "usage_limit_id": limit.get("UsageLimitId"),
                    "cluster_identifier": limit.get("ClusterIdentifier"),
                    "feature_type": limit.get("FeatureType"),
                    "limit_type": limit.get("LimitType"),
                    "amount": limit.get("Amount"),
                    "period": limit.get("Period"),
                    "breach_action": limit.get("BreachAction"),
                    "tags": limit.get("Tags", [])
                }
                limits.append(limit_data)
            
            return limits
        except Exception as e:
            self.logger.warning(f"Error collecting Redshift usage limits: {e}")
            return []