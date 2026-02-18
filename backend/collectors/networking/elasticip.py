"""
Elastic IP Collector
Collects AWS Elastic IP addresses
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ElasticIPCollector(BaseCollector):
    """Collector for AWS Elastic IP resources"""
    
    category = "networking"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Elastic IP collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'ec2')
        self.collector_name = 'elasticip'
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Elastic IP resources
        
        Returns:
            Dictionary containing Elastic IP data
        """
        try:
            logger.info(f"Collecting Elastic IPs from {self.region_name}")
            
            resources = []
            
            # Collect Elastic IPs
            elastic_ips = self._collect_elastic_ips()
            resources.extend(elastic_ips)
            
            logger.info(f"Collected {len(resources)} Elastic IPs from {self.region_name}")
            
            summary = {
                'total_elastic_ips': len(elastic_ips),
                'associated_ips': sum(1 for eip in elastic_ips if eip.get('association_id')),
                'unassociated_ips': sum(1 for eip in elastic_ips if not eip.get('association_id'))
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Elastic IP resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_elastic_ips(self) -> List[Dict[str, Any]]:
        """Collect Elastic IPs"""
        elastic_ips = []
        try:
            response = self.client.describe_addresses()
            
            for address in response.get('Addresses', []):
                elastic_ips.append({
                    'resource_id': address.get('AllocationId', address.get('PublicIp')),
                    'resource_type': 'elastic-ip',
                    'resource_name': address.get('PublicIp'),
                    'region': self.region_name,
                    'public_ip': address.get('PublicIp'),
                    'allocation_id': address.get('AllocationId'),
                    'domain': address.get('Domain'),
                    'instance_id': address.get('InstanceId'),
                    'association_id': address.get('AssociationId'),
                    'network_interface_id': address.get('NetworkInterfaceId'),
                    'network_interface_owner_id': address.get('NetworkInterfaceOwnerId'),
                    'private_ip_address': address.get('PrivateIpAddress'),
                    'public_ipv4_pool': address.get('PublicIpv4Pool'),
                    'network_border_group': address.get('NetworkBorderGroup'),
                    'tags': address.get('Tags', [])
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting Elastic IPs: {e}")
        
        return elastic_ips
