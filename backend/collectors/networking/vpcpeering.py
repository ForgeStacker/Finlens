"""
VPC Peering Collector
Collects AWS VPC Peering Connections
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VPCPeeringCollector(BaseCollector):
    """Collector for AWS VPC Peering Connection resources"""
    
    category = "networking"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize VPC Peering collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'ec2')
        self.collector_name = 'vpcpeering'
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect VPC Peering Connection resources
        
        Returns:
            Dictionary containing VPC Peering data
        """
        try:
            logger.info(f"Collecting VPC Peering Connections from {self.region_name}")
            
            resources = []
            
            # Collect peering connections
            peering_connections = self._collect_peering_connections()
            resources.extend(peering_connections)
            
            logger.info(f"Collected {len(resources)} VPC Peering Connections from {self.region_name}")
            
            summary = {
                'total_peering_connections': len(peering_connections),
                'status_distribution': self._get_status_distribution(peering_connections)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting VPC Peering Connection resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_peering_connections(self) -> List[Dict[str, Any]]:
        """Collect VPC Peering Connections"""
        peering_connections = []
        try:
            response = self.client.describe_vpc_peering_connections()
            
            for pcx in response.get('VpcPeeringConnections', []):
                peering_connections.append({
                    'resource_id': pcx.get('VpcPeeringConnectionId'),
                    'resource_type': 'vpc-peering-connection',
                    'resource_name': pcx.get('VpcPeeringConnectionId'),
                    'region': self.region_name,
                    'accepter_vpc_info': pcx.get('AccepterVpcInfo', {}),
                    'requester_vpc_info': pcx.get('RequesterVpcInfo', {}),
                    'status': pcx.get('Status', {}).get('Code'),
                    'status_message': pcx.get('Status', {}).get('Message'),
                    'expiration_time': pcx.get('ExpirationTime'),
                    'tags': pcx.get('Tags', [])
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting VPC Peering Connections: {e}")
        
        return peering_connections
    
    def _get_status_distribution(self, peering_connections: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of peering connection statuses"""
        distribution = {}
        for pcx in peering_connections:
            status = pcx.get('status', 'unknown')
            distribution[status] = distribution.get(status, 0) + 1
        return distribution
