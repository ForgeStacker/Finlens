"""
Storage Gateway Collector
Collects AWS Storage Gateway resources
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class StorageGatewayCollector(BaseCollector):
    """Collector for AWS Storage Gateway resources"""
    
    category = "storage"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Storage Gateway collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'storagegateway')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Storage Gateway resources
        
        Returns:
            Dictionary containing Storage Gateway data
        """
        try:
            logger.info(f"Collecting Storage Gateway resources from {self.region_name}")
            
            resources = []
            
            # Collect gateways
            gateways = self._collect_gateways()
            resources.extend(gateways)
            
            logger.info(f"Collected {len(resources)} Storage Gateway resources from {self.region_name}")
            
            summary = {
                'total_gateways': len(gateways),
                'gateway_state_distribution': self._get_state_distribution(gateways)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Storage Gateway resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_gateways(self) -> List[Dict[str, Any]]:
        """Collect Storage Gateways"""
        gateways = []
        try:
            response = self.client.list_gateways()
            
            for gateway in response.get('Gateways', []):
                gateway_arn = gateway.get('GatewayARN')
                
                # Get gateway details
                try:
                    detail_response = self.client.describe_gateway_information(GatewayARN=gateway_arn)
                    
                    gateways.append({
                        'resource_id': gateway_arn,
                        'resource_type': 'storage-gateway',
                        'resource_name': gateway.get('GatewayName'),
                        'region': self.region_name,
                        'arn': gateway_arn,
                        'gateway_id': gateway.get('GatewayId'),
                        'gateway_type': gateway.get('GatewayType'),
                        'gateway_operational_state': gateway.get('GatewayOperationalState'),
                        'gateway_timezone': detail_response.get('GatewayTimezone'),
                        'gateway_state': detail_response.get('GatewayState'),
                        'ec2_instance_id': detail_response.get('Ec2InstanceId'),
                        'ec2_instance_region': detail_response.get('Ec2InstanceRegion'),
                        'last_software_update': detail_response.get('LastSoftwareUpdate'),
                        'software_version': detail_response.get('GatewayVersion'),
                        'tags': detail_response.get('Tags', [])
                    })
                except Exception as e:
                    logger.warning(f"Error getting gateway details for {gateway_arn}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Storage Gateways: {e}")
        
        return gateways
    
    def _get_state_distribution(self, gateways: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of gateway states"""
        distribution = {}
        for gateway in gateways:
            state = gateway.get('gateway_state', 'unknown')
            distribution[state] = distribution.get(state, 0) + 1
        return distribution
