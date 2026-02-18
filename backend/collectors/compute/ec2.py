"""
EC2 Collector
Collects EC2 instance data from AWS
Implements standardized data collection following FinLens architecture
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EC2Collector(BaseCollector):
    """Collects EC2 instance information"""
    
    category = "compute"
    
    def __init__(self, profile_name: str, region_name: str):
        """
        Initialize EC2 collector
        
        Args:
            profile_name: AWS profile name
            region_name: AWS region name
        """
        super().__init__(profile_name, region_name, 'ec2')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect EC2 instance data
        
        Returns:
            Standardized dictionary containing EC2 data
        """
        try:
            logger.info(f"Collecting EC2 instances from {self.region_name}")
            
            # Collect instances
            instances = self._collect_instances()
            
            # Build summary
            summary = self._build_summary(instances)
            
            # Build response
            response = self._build_response_structure(
                resources=instances,
                summary=summary
            )
            
            logger.info(
                f"Collected {len(instances)} EC2 instances from {self.region_name}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error collecting EC2 data: {e}")
            return self._build_response_structure(
                resources=[],
                summary={"resource_count": 0, "scan_status": "failed", "error": str(e)}
            )
    
    def _collect_instances(self) -> List[Dict[str, Any]]:
        """
        Collect EC2 instances using pagination
        
        Returns:
            List of EC2 instance dictionaries
        """
        instances = []
        
        try:
            # Use pagination to get all instances
            paginator = self.client.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        instances.append(self._format_instance(instance))
            
            logger.debug(f"Collected {len(instances)} EC2 instances")
            
        except Exception as e:
            self._handle_api_error('describe_instances', e)
        
        return instances
    
    def _format_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format EC2 instance data into standardized structure
        
        Args:
            instance: Raw EC2 instance data from boto3
            
        Returns:
            Formatted instance dictionary
        """
        # Extract name from tags
        name = self._get_instance_name(instance)
        
        # Format instance data
        formatted = {
            "resource_id": instance.get('InstanceId'),
            "resource_name": name,
            "resource_type": "ec2-instance",
            "region": self.region_name,
            "state": instance.get('State', {}).get('Name'),
            "instance_type": instance.get('InstanceType'),
            "launch_time": instance.get('LaunchTime'),
            "platform": instance.get('Platform', 'linux'),  # Default to linux if not specified
            "vpc_id": instance.get('VpcId'),
            "subnet_id": instance.get('SubnetId'),
            "private_ip_address": instance.get('PrivateIpAddress'),
            "public_ip_address": instance.get('PublicIpAddress'),
            "key_name": instance.get('KeyName'),
            "security_groups": [
                {
                    "id": sg.get('GroupId'),
                    "name": sg.get('GroupName')
                }
                for sg in instance.get('SecurityGroups', [])
            ],
            "tags": self._format_tags(instance.get('Tags', [])),
            "monitoring": instance.get('Monitoring', {}).get('State', 'disabled'),
            "architecture": instance.get('Architecture'),
            "root_device_type": instance.get('RootDeviceType'),
            "virtualization_type": instance.get('VirtualizationType'),
        }
        
        # Add storage information
        formatted['storage'] = self._get_storage_info(instance)
        
        # Add network information
        formatted['network_interfaces'] = len(instance.get('NetworkInterfaces', []))
        
        # Add vCPU and RAM info (basic info, detailed specs would require instance type mapping)
        formatted['vcpu'] = self._estimate_vcpu(instance.get('InstanceType'))
        formatted['ram_gb'] = self._estimate_ram(instance.get('InstanceType'))
        
        return formatted
    
    def _get_instance_name(self, instance: Dict[str, Any]) -> str:
        """
        Extract instance name from tags
        
        Args:
            instance: EC2 instance data
            
        Returns:
            Instance name or empty string
        """
        tags = instance.get('Tags', [])
        for tag in tags:
            if tag.get('Key') == 'Name':
                return tag.get('Value', '')
        return ''
    
    def _format_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Format tags into key-value dictionary
        
        Args:
            tags: List of tag dictionaries
            
        Returns:
            Dictionary of tag key-value pairs
        """
        return {tag.get('Key', ''): tag.get('Value', '') for tag in tags}
    
    def _get_storage_info(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract storage information
        
        Args:
            instance: EC2 instance data
            
        Returns:
            Storage information dictionary
        """
        block_devices = instance.get('BlockDeviceMappings', [])
        
        total_volumes = len(block_devices)
        volume_ids = [bd.get('Ebs', {}).get('VolumeId') for bd in block_devices if 'Ebs' in bd]
        
        return {
            "volume_count": total_volumes,
            "volume_ids": volume_ids,
            "root_device_name": instance.get('RootDeviceName'),
        }
    
    def _estimate_vcpu(self, instance_type: str) -> int:
        """
        Estimate vCPU count from instance type
        This is a simplified estimation. In production, use instance type mapping.
        
        Args:
            instance_type: EC2 instance type (e.g., 't3a.xlarge')
            
        Returns:
            Estimated vCPU count
        """
        if not instance_type:
            return 0
        
        # Simple mapping for common sizes
        size_mapping = {
            'nano': 1,
            'micro': 1,
            'small': 1,
            'medium': 1,
            'large': 2,
            'xlarge': 4,
            '2xlarge': 8,
            '4xlarge': 16,
            '8xlarge': 32,
            '16xlarge': 64,
        }
        
        # Extract size from instance type
        parts = instance_type.split('.')
        if len(parts) > 1:
            size = parts[1]
            return size_mapping.get(size, 2)
        
        return 2  # Default
    
    def _estimate_ram(self, instance_type: str) -> int:
        """
        Estimate RAM in GB from instance type
        This is a simplified estimation. In production, use instance type mapping.
        
        Args:
            instance_type: EC2 instance type
            
        Returns:
            Estimated RAM in GB
        """
        if not instance_type:
            return 0
        
        # Simple mapping for common sizes
        size_mapping = {
            'nano': 0.5,
            'micro': 1,
            'small': 2,
            'medium': 4,
            'large': 8,
            'xlarge': 16,
            '2xlarge': 32,
            '4xlarge': 64,
            '8xlarge': 128,
            '16xlarge': 256,
        }
        
        # Extract size from instance type
        parts = instance_type.split('.')
        if len(parts) > 1:
            size = parts[1]
            return size_mapping.get(size, 8)
        
        return 8  # Default
    
    def _build_summary(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build summary statistics for collected instances
        
        Args:
            instances: List of instance dictionaries
            
        Returns:
            Summary dictionary
        """
        # Count by state
        state_counts = {}
        instance_types = set()
        total_vcpu = 0
        total_ram = 0
        
        for instance in instances:
            state = instance.get('state', 'unknown')
            state_counts[state] = state_counts.get(state, 0) + 1
            
            instance_type = instance.get('instance_type')
            if instance_type:
                instance_types.add(instance_type)
            
            total_vcpu += instance.get('vcpu', 0)
            total_ram += instance.get('ram_gb', 0)
        
        return {
            "resource_count": len(instances),
            "scan_status": "success",
            "state_distribution": state_counts,
            "unique_instance_types": len(instance_types),
            "total_vcpu": total_vcpu,
            "total_ram_gb": total_ram,
        }
