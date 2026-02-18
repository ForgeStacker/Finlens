"""
EBS (Elastic Block Store) Collector for FinLens
Collects comprehensive EBS volumes data including attachments, snapshots, and encryption
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class EBSCollector(BaseCollector):
    """Collector for EBS (Elastic Block Store) data"""
    
    category = "storage"
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "ebs"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def initialize_client(self) -> bool:
        """Initialize EC2 client since EBS uses EC2 service"""
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
            
            # Use EC2 client for EBS operations
            self.client = self.session.client('ec2', region_name=self.region_name)
            
            self.logger.info(f"EBS client initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing EBS client: {e}")
            return False
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for EBS data"""
        try:
            self.logger.info(f"[EBS_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Initialize client
            if not self.initialize_client():
                return {}
            
            ec2_client = self.client
            
            self.logger.info("Collecting ebs data...")
            data = {
                "volumes": self._collect_volumes(ec2_client),
                "volume_modifications": self._collect_volume_modifications(ec2_client),
                "fast_snapshot_restores": self._collect_fast_snapshot_restores(ec2_client)
            }
            
            # Count total resources
            total_resources = len(data["volumes"])
            
            self.logger.info(f"Collected {total_resources} EBS resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting EBS data: {str(e)}")
            return {}
    
    def _collect_volumes(self, client) -> List[Dict[str, Any]]:
        """Collect EBS volumes"""
        try:
            volumes = []
            
            response = client.describe_volumes()
            for volume in response.get('Volumes', []):
                volume_data = {
                    "volume_id": volume.get("VolumeId"),
                    "size": volume.get("Size"),
                    "volume_type": volume.get("VolumeType"),
                    "iops": volume.get("Iops"),
                    "throughput": volume.get("Throughput"),
                    "state": volume.get("State"),
                    "create_time": volume.get("CreateTime").isoformat() if volume.get("CreateTime") else None,
                    "availability_zone": volume.get("AvailabilityZone"),
                    "snapshot_id": volume.get("SnapshotId"),
                    "encrypted": volume.get("Encrypted"),
                    "kms_key_id": volume.get("KmsKeyId"),
                    "outpost_arn": volume.get("OutpostArn"),
                    "multi_attach_enabled": volume.get("MultiAttachEnabled"),
                    "fast_restored": volume.get("FastRestored"),
                    "attachments": volume.get("Attachments", []),
                    "tags": volume.get("Tags", [])
                }
                
                # Get volume attributes
                try:
                    attr_response = client.describe_volume_attribute(
                        VolumeId=volume["VolumeId"],
                        Attribute='autoEnableIO'
                    )
                    volume_data["auto_enable_io"] = attr_response.get("AutoEnableIO", {}).get("Value")
                except Exception as e:
                    self.logger.debug(f"Could not get autoEnableIO for volume {volume['VolumeId']}: {e}")
                    volume_data["auto_enable_io"] = None
                
                try:
                    attr_response = client.describe_volume_attribute(
                        VolumeId=volume["VolumeId"],
                        Attribute='productCodes'
                    )
                    volume_data["product_codes"] = attr_response.get("ProductCodes", [])
                except Exception as e:
                    self.logger.debug(f"Could not get productCodes for volume {volume['VolumeId']}: {e}")
                    volume_data["product_codes"] = []
                
                volumes.append(volume_data)
            
            return volumes
        except Exception as e:
            self.logger.warning(f"Error collecting EBS volumes: {e}")
            return []
    
    def _collect_volume_modifications(self, client) -> List[Dict[str, Any]]:
        """Collect EBS volume modifications history"""
        try:
            modifications = []
            
            response = client.describe_volumes_modifications()
            for modification in response.get('VolumesModifications', []):
                mod_data = {
                    "volume_id": modification.get("VolumeId"),
                    "modification_state": modification.get("ModificationState"),
                    "status_message": modification.get("StatusMessage"),
                    "target_size": modification.get("TargetSize"),
                    "target_iops": modification.get("TargetIops"),
                    "target_volume_type": modification.get("TargetVolumeType"),
                    "target_throughput": modification.get("TargetThroughput"),
                    "target_multi_attach_enabled": modification.get("TargetMultiAttachEnabled"),
                    "original_size": modification.get("OriginalSize"),
                    "original_iops": modification.get("OriginalIops"),
                    "original_volume_type": modification.get("OriginalVolumeType"),
                    "original_throughput": modification.get("OriginalThroughput"),
                    "original_multi_attach_enabled": modification.get("OriginalMultiAttachEnabled"),
                    "progress": modification.get("Progress"),
                    "start_time": modification.get("StartTime").isoformat() if modification.get("StartTime") else None,
                    "end_time": modification.get("EndTime").isoformat() if modification.get("EndTime") else None
                }
                modifications.append(mod_data)
            
            return modifications
        except Exception as e:
            self.logger.warning(f"Error collecting EBS volume modifications: {e}")
            return []
    
    def _collect_fast_snapshot_restores(self, client) -> List[Dict[str, Any]]:
        """Collect Fast Snapshot Restore configurations"""
        try:
            fast_restores = []
            
            response = client.describe_fast_snapshot_restores()
            for restore in response.get('FastSnapshotRestores', []):
                restore_data = {
                    "snapshot_id": restore.get("SnapshotId"),
                    "availability_zone": restore.get("AvailabilityZone"),
                    "state": restore.get("State"),
                    "state_transition_reason": restore.get("StateTransitionReason"),
                    "owner_id": restore.get("OwnerId"),
                    "owner_alias": restore.get("OwnerAlias"),
                    "enabled_time": restore.get("EnabledTime").isoformat() if restore.get("EnabledTime") else None,
                    "enabling_time": restore.get("EnablingTime").isoformat() if restore.get("EnablingTime") else None,
                    "disabled_time": restore.get("DisabledTime").isoformat() if restore.get("DisabledTime") else None,
                    "disabling_time": restore.get("DisablingTime").isoformat() if restore.get("DisablingTime") else None,
                    "optimizing_time": restore.get("OptimizingTime").isoformat() if restore.get("OptimizingTime") else None
                }
                fast_restores.append(restore_data)
            
            return fast_restores
        except Exception as e:
            self.logger.warning(f"Error collecting Fast Snapshot Restores: {e}")
            return []