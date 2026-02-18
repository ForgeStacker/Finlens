"""
AMI (Amazon Machine Images) Collector for FinLens
Collects comprehensive AMI data including public, private, and shared images
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class AMICollector(BaseCollector):
    """Collector for AMI (Amazon Machine Images) data"""
    
    category = "compute"
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "ami"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def initialize_client(self) -> bool:
        """Initialize EC2 client since AMI uses EC2 service"""
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
            
            # Use EC2 client for AMI operations
            self.client = self.session.client('ec2', region_name=self.region_name)
            
            self.logger.info(f"AMI client initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing AMI client: {e}")
            return False
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for AMI data"""
        try:
            self.logger.info(f"[AMI_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Initialize client
            if not self.initialize_client():
                return {}
            
            ec2_client = self.client
            
            self.logger.info("Collecting ami data...")
            data = {
                "owned_amis": self._collect_owned_amis(ec2_client),
                "public_amis_used": self._collect_public_amis_used(ec2_client),
                "shared_amis": self._collect_shared_amis(ec2_client),
                "ami_permissions": self._collect_ami_permissions(ec2_client),
                "ami_launch_permissions": self._collect_ami_launch_permissions(ec2_client)
            }
            
            # Count total resources
            total_resources = (
                len(data["owned_amis"]) +
                len(data["public_amis_used"]) +
                len(data["shared_amis"])
            )
            
            self.logger.info(f"Collected {total_resources} AMI resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting AMI data: {str(e)}")
            return {}
    
    def _collect_owned_amis(self, client) -> List[Dict[str, Any]]:
        """Collect AMIs owned by this account"""
        try:
            amis = []
            
            # Get AMIs owned by this account
            response = client.describe_images(Owners=['self'])
            for ami in response.get('Images', []):
                ami_data = {
                    "image_id": ami.get("ImageId"),
                    "name": ami.get("Name"),
                    "description": ami.get("Description"),
                    "creation_date": ami.get("CreationDate"),
                    "state": ami.get("State"),
                    "public": ami.get("Public"),
                    "architecture": ami.get("Architecture"),
                    "image_type": ami.get("ImageType"),
                    "platform": ami.get("Platform"),
                    "platform_details": ami.get("PlatformDetails"),
                    "usage_operation": ami.get("UsageOperation"),
                    "root_device_type": ami.get("RootDeviceType"),
                    "root_device_name": ami.get("RootDeviceName"),
                    "block_device_mappings": ami.get("BlockDeviceMappings", []),
                    "virtualization_type": ami.get("VirtualizationType"),
                    "hypervisor": ami.get("Hypervisor"),
                    "ena_support": ami.get("EnaSupport"),
                    "sriov_net_support": ami.get("SriovNetSupport"),
                    "boot_mode": ami.get("BootMode"),
                    "tpm_support": ami.get("TpmSupport"),
                    "imds_support": ami.get("ImdsSupport"),
                    "deprecation_time": ami.get("DeprecationTime"),
                    "tags": ami.get("Tags", [])
                }
                
                # Get launch permissions for owned AMIs
                try:
                    launch_perms = client.describe_image_attribute(
                        ImageId=ami["ImageId"],
                        Attribute='launchPermission'
                    )
                    ami_data["launch_permissions"] = launch_perms.get("LaunchPermissions", [])
                except Exception as e:
                    self.logger.warning(f"Could not get launch permissions for AMI {ami['ImageId']}: {e}")
                    ami_data["launch_permissions"] = []
                
                amis.append(ami_data)
            
            return amis
        except Exception as e:
            self.logger.warning(f"Error collecting owned AMIs: {e}")
            return []
    
    def _collect_public_amis_used(self, client) -> List[Dict[str, Any]]:
        """Collect public AMIs currently being used by instances"""
        try:
            used_amis = []
            ami_ids = set()
            
            # Get all instances to find which AMIs are being used
            instances_response = client.describe_instances()
            for reservation in instances_response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    if instance.get('ImageId'):
                        ami_ids.add(instance['ImageId'])
            
            if ami_ids:
                # Get details for AMIs being used
                amis_response = client.describe_images(ImageIds=list(ami_ids))
                for ami in amis_response.get('Images', []):
                    # Only include public AMIs (not owned by this account)
                    if ami.get('Public') and ami.get('OwnerId') != 'self':
                        ami_data = {
                            "image_id": ami.get("ImageId"),
                            "name": ami.get("Name"),
                            "description": ami.get("Description"),
                            "owner_id": ami.get("OwnerId"),
                            "creation_date": ami.get("CreationDate"),
                            "state": ami.get("State"),
                            "architecture": ami.get("Architecture"),
                            "image_type": ami.get("ImageType"),
                            "platform": ami.get("Platform"),
                            "platform_details": ami.get("PlatformDetails"),
                            "root_device_type": ami.get("RootDeviceType"),
                            "virtualization_type": ami.get("VirtualizationType"),
                            "hypervisor": ami.get("Hypervisor")
                        }
                        used_amis.append(ami_data)
            
            return used_amis
        except Exception as e:
            self.logger.warning(f"Error collecting public AMIs used: {e}")
            return []
    
    def _collect_shared_amis(self, client) -> List[Dict[str, Any]]:
        """Collect AMIs shared with this account"""
        try:
            shared_amis = []
            
            # Get AMIs shared with this account (executable by this account but not owned)
            response = client.describe_images(ExecutableUsers=['self'])
            for ami in response.get('Images', []):
                # Only include AMIs not owned by this account
                if ami.get('OwnerId') != 'self':
                    ami_data = {
                        "image_id": ami.get("ImageId"),
                        "name": ami.get("Name"),
                        "description": ami.get("Description"),
                        "owner_id": ami.get("OwnerId"),
                        "creation_date": ami.get("CreationDate"),
                        "state": ami.get("State"),
                        "public": ami.get("Public"),
                        "architecture": ami.get("Architecture"),
                        "image_type": ami.get("ImageType"),
                        "platform": ami.get("Platform"),
                        "platform_details": ami.get("PlatformDetails"),
                        "root_device_type": ami.get("RootDeviceType"),
                        "virtualization_type": ami.get("VirtualizationType"),
                        "hypervisor": ami.get("Hypervisor")
                    }
                    shared_amis.append(ami_data)
            
            return shared_amis
        except Exception as e:
            self.logger.warning(f"Error collecting shared AMIs: {e}")
            return []
    
    def _collect_ami_permissions(self, client) -> List[Dict[str, Any]]:
        """Collect AMI attribute permissions for owned AMIs"""
        try:
            permissions = []
            
            # Get owned AMIs first
            owned_response = client.describe_images(Owners=['self'])
            for ami in owned_response.get('Images', []):
                ami_id = ami['ImageId']
                ami_permissions = {
                    "image_id": ami_id,
                    "attributes": {}
                }
                
                # Get various attributes
                attributes = ['description', 'kernel', 'ramdisk', 'launchPermission', 
                             'productCodes', 'blockDeviceMapping', 'sriovNetSupport']
                
                for attr in attributes:
                    try:
                        attr_response = client.describe_image_attribute(
                            ImageId=ami_id,
                            Attribute=attr
                        )
                        # Remove ImageId from response to avoid duplication
                        attr_data = {k: v for k, v in attr_response.items() if k != 'ImageId'}
                        ami_permissions["attributes"][attr] = attr_data
                    except Exception as e:
                        self.logger.debug(f"Could not get {attr} attribute for AMI {ami_id}: {e}")
                        ami_permissions["attributes"][attr] = None
                
                permissions.append(ami_permissions)
            
            return permissions
        except Exception as e:
            self.logger.warning(f"Error collecting AMI permissions: {e}")
            return []
    
    def _collect_ami_launch_permissions(self, client) -> List[Dict[str, Any]]:
        """Collect detailed launch permissions for owned AMIs"""
        try:
            launch_permissions = []
            
            # Get owned AMIs
            owned_response = client.describe_images(Owners=['self'])
            for ami in owned_response.get('Images', []):
                ami_id = ami['ImageId']
                
                try:
                    launch_perms = client.describe_image_attribute(
                        ImageId=ami_id,
                        Attribute='launchPermission'
                    )
                    
                    launch_data = {
                        "image_id": ami_id,
                        "launch_permissions": launch_perms.get("LaunchPermissions", [])
                    }
                    
                    # Categorize permissions
                    public_permission = False
                    user_permissions = []
                    group_permissions = []
                    
                    for perm in launch_perms.get("LaunchPermissions", []):
                        if perm.get("Group") == "all":
                            public_permission = True
                        elif perm.get("UserId"):
                            user_permissions.append(perm["UserId"])
                        elif perm.get("Group"):
                            group_permissions.append(perm["Group"])
                    
                    launch_data.update({
                        "is_public": public_permission,
                        "shared_with_users": user_permissions,
                        "shared_with_groups": group_permissions
                    })
                    
                    launch_permissions.append(launch_data)
                    
                except Exception as e:
                    self.logger.warning(f"Could not get launch permissions for AMI {ami_id}: {e}")
            
            return launch_permissions
        except Exception as e:
            self.logger.warning(f"Error collecting AMI launch permissions: {e}")
            return []