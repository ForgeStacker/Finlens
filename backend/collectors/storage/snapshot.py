"""
Snapshot Collector for FinLens
Collects comprehensive EBS snapshots data including sharing permissions and lifecycle
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class SnapshotCollector(BaseCollector):
    """Collector for EBS Snapshots data"""
    
    category = "storage"
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "snapshot"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def initialize_client(self) -> bool:
        """Initialize EC2 client since Snapshots use EC2 service"""
        try:
            import boto3
            self.session = boto3.Session(
                profile_name=self.profile_name,
                region_name=self.region_name
            )
            
            # Get account ID
            try:
                sts = self.session.client('sts')
                self.account_id = sts.get_caller_identity()['Account']
            except:
                self.account_id = 'unknown'
            
            # Use EC2 client for snapshot operations
            self.client = self.session.client('ec2', region_name=self.region_name)
            
            self.logger.info(f"Snapshot client initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing Snapshot client: {e}")
            return False
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for Snapshot data"""
        try:
            self.logger.info(f"[SNAPSHOT_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Initialize client
            if not self.initialize_client():
                return {}
            
            ec2_client = self.client
            
            self.logger.info("Collecting snapshot data...")
            data = {
                "owned_snapshots": self._collect_owned_snapshots(ec2_client),
                "shared_snapshots": self._collect_shared_snapshots(ec2_client),
                "public_snapshots": self._collect_public_snapshots_used(ec2_client),
                "snapshot_lifecycle_policies": self._collect_dlm_policies(),
                "snapshot_recycle_bin": self._collect_recycle_bin_resources()
            }
            
            # Count total resources
            total_resources = len(data["owned_snapshots"]) + len(data["shared_snapshots"]) + len(data["public_snapshots"])
            
            self.logger.info(f"Collected {total_resources} Snapshot resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting Snapshot data: {str(e)}")
            return {}
    
    def _collect_owned_snapshots(self, client) -> List[Dict[str, Any]]:
        """Collect snapshots owned by the account"""
        try:
            snapshots = []
            
            # Get owned snapshots
            response = client.describe_snapshots(OwnerIds=['self'])
            for snapshot in response.get('Snapshots', []):
                snapshot_data = {
                    "snapshot_id": snapshot.get("SnapshotId"),
                    "volume_id": snapshot.get("VolumeId"),
                    "state": snapshot.get("State"),
                    "state_message": snapshot.get("StateMessage"),
                    "start_time": snapshot.get("StartTime").isoformat() if snapshot.get("StartTime") else None,
                    "progress": snapshot.get("Progress"),
                    "volume_size": snapshot.get("VolumeSize"),
                    "description": snapshot.get("Description"),
                    "encrypted": snapshot.get("Encrypted"),
                    "kms_key_id": snapshot.get("KmsKeyId"),
                    "data_encryption_key_id": snapshot.get("DataEncryptionKeyId"),
                    "owner_id": snapshot.get("OwnerId"),
                    "owner_alias": snapshot.get("OwnerAlias"),
                    "outpost_arn": snapshot.get("OutpostArn"),
                    "storage_tier": snapshot.get("StorageTier"),
                    "restore_expiry_time": snapshot.get("RestoreExpiryTime").isoformat() if snapshot.get("RestoreExpiryTime") else None,
                    "sse_type": snapshot.get("SseType"),
                    "tags": snapshot.get("Tags", [])
                }
                
                # Get snapshot attributes (sharing permissions)
                snapshot_data["sharing_permissions"] = self._get_snapshot_sharing_permissions(client, snapshot["SnapshotId"])
                
                snapshots.append(snapshot_data)
            
            return snapshots
        except Exception as e:
            self.logger.warning(f"Error collecting owned snapshots: {e}")
            return []
    
    def _collect_shared_snapshots(self, client) -> List[Dict[str, Any]]:
        """Collect snapshots shared with the account"""
        try:
            snapshots = []
            
            # Get snapshots shared with this account
            response = client.describe_snapshots(RestorableByUserIds=['self'])
            for snapshot in response.get('Snapshots', []):
                # Skip if we own this snapshot (already collected above)
                if snapshot.get("OwnerId") == self._get_account_id():
                    continue
                    
                snapshot_data = {
                    "snapshot_id": snapshot.get("SnapshotId"),
                    "volume_id": snapshot.get("VolumeId"),
                    "state": snapshot.get("State"),
                    "state_message": snapshot.get("StateMessage"),
                    "start_time": snapshot.get("StartTime").isoformat() if snapshot.get("StartTime") else None,
                    "progress": snapshot.get("Progress"),
                    "volume_size": snapshot.get("VolumeSize"),
                    "description": snapshot.get("Description"),
                    "encrypted": snapshot.get("Encrypted"),
                    "kms_key_id": snapshot.get("KmsKeyId"),
                    "data_encryption_key_id": snapshot.get("DataEncryptionKeyId"),
                    "owner_id": snapshot.get("OwnerId"),
                    "owner_alias": snapshot.get("OwnerAlias"),
                    "outpost_arn": snapshot.get("OutpostArn"),
                    "storage_tier": snapshot.get("StorageTier"),
                    "restore_expiry_time": snapshot.get("RestoreExpiryTime").isoformat() if snapshot.get("RestoreExpiryTime") else None,
                    "sse_type": snapshot.get("SseType"),
                    "tags": snapshot.get("Tags", []),
                    "shared": True
                }
                
                snapshots.append(snapshot_data)
            
            return snapshots
        except Exception as e:
            self.logger.warning(f"Error collecting shared snapshots: {e}")
            return []
    
    def _collect_public_snapshots_used(self, client) -> List[Dict[str, Any]]:
        """Collect public snapshots that are being used (referenced in AMIs or volumes)"""
        try:
            public_snapshots = []
            public_snapshot_ids = set()
            
            # Find public snapshots used in AMIs
            try:
                ami_response = client.describe_images(Owners=['self'])
                for ami in ami_response.get('Images', []):
                    for block_device in ami.get('BlockDeviceMappings', []):
                        ebs = block_device.get('Ebs', {})
                        if ebs.get('SnapshotId'):
                            public_snapshot_ids.add(ebs['SnapshotId'])
            except Exception as e:
                self.logger.debug(f"Could not check AMIs for snapshot references: {e}")
            
            # Find public snapshots used in volumes
            try:
                volume_response = client.describe_volumes()
                for volume in volume_response.get('Volumes', []):
                    if volume.get('SnapshotId'):
                        public_snapshot_ids.add(volume['SnapshotId'])
            except Exception as e:
                self.logger.debug(f"Could not check volumes for snapshot references: {e}")
            
            # Get details for these snapshots
            if public_snapshot_ids:
                try:
                    snapshot_response = client.describe_snapshots(SnapshotIds=list(public_snapshot_ids))
                    for snapshot in snapshot_response.get('Snapshots', []):
                        # Only include if it's not owned by us (i.e., it's public or shared)
                        if snapshot.get("OwnerId") != self._get_account_id():
                            snapshot_data = {
                                "snapshot_id": snapshot.get("SnapshotId"),
                                "volume_id": snapshot.get("VolumeId"),
                                "state": snapshot.get("State"),
                                "state_message": snapshot.get("StateMessage"),
                                "start_time": snapshot.get("StartTime").isoformat() if snapshot.get("StartTime") else None,
                                "progress": snapshot.get("Progress"),
                                "volume_size": snapshot.get("VolumeSize"),
                                "description": snapshot.get("Description"),
                                "encrypted": snapshot.get("Encrypted"),
                                "kms_key_id": snapshot.get("KmsKeyId"),
                                "data_encryption_key_id": snapshot.get("DataEncryptionKeyId"),
                                "owner_id": snapshot.get("OwnerId"),
                                "owner_alias": snapshot.get("OwnerAlias"),
                                "outpost_arn": snapshot.get("OutpostArn"),
                                "storage_tier": snapshot.get("StorageTier"),
                                "restore_expiry_time": snapshot.get("RestoreExpiryTime").isoformat() if snapshot.get("RestoreExpiryTime") else None,
                                "sse_type": snapshot.get("SseType"),
                                "tags": snapshot.get("Tags", []),
                                "public_or_shared": True,
                                "used_in_resources": True
                            }
                            public_snapshots.append(snapshot_data)
                except Exception as e:
                    self.logger.debug(f"Could not describe snapshots: {e}")
            
            return public_snapshots
        except Exception as e:
            self.logger.warning(f"Error collecting public snapshots: {e}")
            return []
    
    def _get_snapshot_sharing_permissions(self, client, snapshot_id: str) -> Dict[str, Any]:
        """Get sharing permissions for a snapshot"""
        try:
            response = client.describe_snapshot_attribute(
                SnapshotId=snapshot_id,
                Attribute='createVolumePermission'
            )
            
            permissions = {
                "create_volume_permissions": response.get("CreateVolumePermissions", []),
                "product_codes": []
            }
            
            # Get product codes if any
            try:
                product_response = client.describe_snapshot_attribute(
                    SnapshotId=snapshot_id,
                    Attribute='productCodes'
                )
                permissions["product_codes"] = product_response.get("ProductCodes", [])
            except Exception:
                pass  # Product codes might not exist
            
            return permissions
        except Exception as e:
            self.logger.debug(f"Could not get sharing permissions for snapshot {snapshot_id}: {e}")
            return {"create_volume_permissions": [], "product_codes": []}
    
    def _collect_dlm_policies(self) -> List[Dict[str, Any]]:
        """Collect Data Lifecycle Manager policies for snapshots"""
        try:
            # Initialize DLM client
            dlm_client = self.session.client('dlm', region_name=self.region_name)
            
            policies = []
            response = dlm_client.get_lifecycle_policies()
            
            for policy_summary in response.get('Policies', []):
                policy_id = policy_summary.get('PolicyId')
                
                # Get detailed policy information
                try:
                    policy_detail_response = dlm_client.get_lifecycle_policy(PolicyId=policy_id)
                    policy_detail = policy_detail_response.get('Policy', {})
                    
                    policy_data = {
                        "policy_id": policy_detail.get("PolicyId"),
                        "description": policy_detail.get("Description"),
                        "state": policy_detail.get("State"),
                        "status_message": policy_detail.get("StatusMessage"),
                        "execution_role_arn": policy_detail.get("ExecutionRoleArn"),
                        "date_created": policy_detail.get("DateCreated").isoformat() if policy_detail.get("DateCreated") else None,
                        "date_modified": policy_detail.get("DateModified").isoformat() if policy_detail.get("DateModified") else None,
                        "policy_details": policy_detail.get("PolicyDetails"),
                        "tags": policy_detail.get("Tags", {})
                    }
                    policies.append(policy_data)
                except Exception as e:
                    self.logger.debug(f"Could not get details for DLM policy {policy_id}: {e}")
            
            return policies
        except Exception as e:
            self.logger.warning(f"Error collecting DLM policies: {e}")
            return []
    
    def _collect_recycle_bin_resources(self) -> List[Dict[str, Any]]:
        """Collect snapshots in Recycle Bin"""
        try:
            # Initialize Recycle Bin client
            rbin_client = self.session.client('rbin', region_name=self.region_name)
            
            resources = []
            response = rbin_client.list_resources(
                ResourceType='EBS_SNAPSHOT'
            )
            
            for resource in response.get('Resources', []):
                resource_data = {
                    "resource_arn": resource.get("ResourceArn"),
                    "resource_id": resource.get("ResourceId"),
                    "resource_type": resource.get("ResourceType"),
                    "retention_rule_arn": resource.get("RetentionRuleArn"),
                    "last_modified_time": resource.get("LastModifiedTime").isoformat() if resource.get("LastModifiedTime") else None,
                    "deletion_time": resource.get("DeletionTime").isoformat() if resource.get("DeletionTime") else None,
                    "status": resource.get("Status")
                }
                resources.append(resource_data)
            
            return resources
        except Exception as e:
            self.logger.warning(f"Error collecting Recycle Bin resources: {e}")
            return []
    
    def _get_account_id(self) -> Optional[str]:
        """Get the current AWS account ID"""
        try:
            sts_client = self.session.client('sts')
            response = sts_client.get_caller_identity()
            return response.get('Account')
        except Exception as e:
            self.logger.debug(f"Could not get account ID: {e}")
            return None