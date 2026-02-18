"""
Shield Collector
Collects AWS Shield protections and subscriptions
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ShieldCollector(BaseCollector):
    """Collector for AWS Shield resources"""
    
    category = "security"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Shield collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'shield')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Shield resources
        
        Returns:
            Dictionary containing Shield data
        """
        try:
            logger.info(f"Collecting Shield protections from {self.region_name}")
            
            resources = []
            
            # Collect protections
            protections = self._collect_protections()
            resources.extend(protections)
            
            logger.info(f"Collected {len(resources)} Shield protections from {self.region_name}")
            
            summary = {
                'total_protections': len(protections)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Shield resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_protections(self) -> List[Dict[str, Any]]:
        """Collect Shield protections"""
        protections = []
        try:
            response = self.client.list_protections()
            
            for protection in response.get('Protections', []):
                protections.append({
                    'resource_id': protection.get('Id'),
                    'resource_type': 'shield-protection',
                    'resource_name': protection.get('Name'),
                    'region': self.region_name,
                    'protection_id': protection.get('Id'),
                    'protected_resource_arn': protection.get('ResourceArn'),
                    'health_check_ids': protection.get('HealthCheckIds', []),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting Shield protections: {e}")
        
        return protections
