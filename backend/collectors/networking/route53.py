"""
Route 53 Collector
Collects AWS Route 53 hosted zones and records
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class Route53Collector(BaseCollector):
    """Collector for AWS Route 53 resources"""
    
    category = "networking"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Route 53 collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'route53')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Route 53 resources
        
        Returns:
            Dictionary containing Route 53 data
        """
        try:
            logger.info(f"Collecting Route 53 hosted zones")
            
            resources = []
            
            # Collect hosted zones
            hosted_zones = self._collect_hosted_zones()
            resources.extend(hosted_zones)
            
            logger.info(f"Collected {len(resources)} Route 53 hosted zones")
            
            summary = {
                'total_hosted_zones': len(hosted_zones),
                'private_zones': sum(1 for hz in hosted_zones if hz.get('is_private')),
                'public_zones': sum(1 for hz in hosted_zones if not hz.get('is_private'))
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Route 53 resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_hosted_zones(self) -> List[Dict[str, Any]]:
        """Collect Route 53 hosted zones"""
        hosted_zones = []
        try:
            response = self.client.list_hosted_zones()
            
            for zone in response.get('HostedZones', []):
                zone_id = zone.get('Id').split('/')[-1]
                
                # Get record count
                record_count = 0
                try:
                    records_response = self.client.list_resource_record_sets(HostedZoneId=zone_id)
                    record_count = len(records_response.get('ResourceRecordSets', []))
                except Exception:
                    pass
                
                hosted_zones.append({
                    'resource_id': zone_id,
                    'resource_type': 'route53-hosted-zone',
                    'resource_name': zone.get('Name'),
                    'region': 'global',
                    'zone_id': zone_id,
                    'name': zone.get('Name'),
                    'caller_reference': zone.get('CallerReference'),
                    'config': zone.get('Config', {}),
                    'is_private': zone.get('Config', {}).get('PrivateZone', False),
                    'resource_record_set_count': zone.get('ResourceRecordSetCount'),
                    'record_count': record_count,
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting Route 53 hosted zones: {e}")
        
        return hosted_zones
