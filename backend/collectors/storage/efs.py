"""
EFS Collector
Collects AWS EFS file systems
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EFSCollector(BaseCollector):
    """Collector for AWS EFS resources"""
    
    category = "storage"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize EFS collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'efs')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect EFS resources
        
        Returns:
            Dictionary containing EFS data
        """
        try:
            logger.info(f"Collecting EFS file systems from {self.region_name}")
            
            resources = []
            
            # Collect file systems
            file_systems = self._collect_file_systems()
            resources.extend(file_systems)
            
            logger.info(f"Collected {len(resources)} EFS file systems from {self.region_name}")
            
            summary = {
                'total_file_systems': len(file_systems),
                'lifecycle_state_distribution': self._get_state_distribution(file_systems)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting EFS resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_file_systems(self) -> List[Dict[str, Any]]:
        """Collect EFS file systems"""
        file_systems = []
        try:
            response = self.client.describe_file_systems()
            
            for fs in response.get('FileSystems', []):
                fs_id = fs.get('FileSystemId')
                
                # Get mount targets
                mount_targets = []
                try:
                    mt_response = self.client.describe_mount_targets(FileSystemId=fs_id)
                    mount_targets = mt_response.get('MountTargets', [])
                except Exception:
                    pass
                
                file_systems.append({
                    'resource_id': fs_id,
                    'resource_type': 'efs-file-system',
                    'resource_name': fs.get('Name', fs_id),
                    'region': self.region_name,
                    'creation_token': fs.get('CreationToken'),
                    'creation_time': fs.get('CreationTime'),
                    'lifecycle_state': fs.get('LifeCycleState'),
                    'number_of_mount_targets': fs.get('NumberOfMountTargets'),
                    'size_in_bytes': fs.get('SizeInBytes', {}),
                    'performance_mode': fs.get('PerformanceMode'),
                    'encrypted': fs.get('Encrypted'),
                    'kms_key_id': fs.get('KmsKeyId'),
                    'throughput_mode': fs.get('ThroughputMode'),
                    'provisioned_throughput_in_mibps': fs.get('ProvisionedThroughputInMibps'),
                    'availability_zone_name': fs.get('AvailabilityZoneName'),
                    'mount_targets': mount_targets,
                    'tags': fs.get('Tags', [])
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting EFS file systems: {e}")
        
        return file_systems
    
    def _get_state_distribution(self, file_systems: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of lifecycle states"""
        distribution = {}
        for fs in file_systems:
            state = fs.get('lifecycle_state', 'unknown')
            distribution[state] = distribution.get(state, 0) + 1
        return distribution
