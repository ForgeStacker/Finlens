"""
Control Tower Collector
Collects AWS Control Tower landing zones and guardrails
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ControlTowerCollector(BaseCollector):
    """Collector for AWS Control Tower resources"""
    
    category = "management_governance"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Control Tower collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'controltower')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Control Tower resources
        
        Returns:
            Dictionary containing Control Tower data
        """
        try:
            logger.info(f"Collecting Control Tower resources from {self.region_name}")
            
            resources = []
            
            # Collect landing zones
            landing_zones = self._collect_landing_zones()
            resources.extend(landing_zones)
            
            # Collect enabled controls (guardrails)
            controls = self._collect_enabled_controls()
            resources.extend(controls)
            
            logger.info(f"Collected {len(resources)} Control Tower resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'landing_zones': len(landing_zones),
                'enabled_controls': len(controls)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Control Tower resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_landing_zones(self) -> List[Dict[str, Any]]:
        """Collect Control Tower landing zones"""
        landing_zones = []
        try:
            response = self.client.list_landing_zones()
            
            for lz in response.get('landingZones', []):
                lz_arn = lz.get('arn')
                
                # Get landing zone details
                try:
                    detail = self.client.get_landing_zone(landingZoneIdentifier=lz_arn)
                    lz_detail = detail.get('landingZone', {})
                    
                    landing_zones.append({
                        'resource_id': lz_arn,
                        'resource_type': 'controltower-landing-zone',
                        'resource_name': lz_arn.split('/')[-1],
                        'region': self.region_name,
                        'status': lz_detail.get('status'),
                        'version': lz_detail.get('version'),
                        'drift_status': lz_detail.get('driftStatus', {}).get('status'),
                        'latest_available_version': lz_detail.get('latestAvailableVersion'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting landing zone details for {lz_arn}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Control Tower landing zones: {e}")
        
        return landing_zones
    
    def _collect_enabled_controls(self) -> List[Dict[str, Any]]:
        """Collect enabled controls (guardrails)"""
        controls = []
        try:
            response = self.client.list_enabled_controls()
            
            for control in response.get('enabledControls', []):
                control_arn = control.get('arn')
                
                # Get control details
                try:
                    detail = self.client.get_enabled_control(enabledControlIdentifier=control_arn)
                    control_detail = detail.get('enabledControlDetails', {})
                    
                    controls.append({
                        'resource_id': control_arn,
                        'resource_type': 'controltower-enabled-control',
                        'resource_name': control_arn.split('/')[-1],
                        'region': self.region_name,
                        'control_identifier': control_detail.get('controlIdentifier'),
                        'drift_status': control_detail.get('driftStatusSummary', {}).get('driftStatus'),
                        'target_identifier': control_detail.get('targetIdentifier'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting control details for {control_arn}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Control Tower enabled controls: {e}")
        
        return controls
