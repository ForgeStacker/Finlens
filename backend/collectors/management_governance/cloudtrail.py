"""
CloudTrail Collector
Collects AWS CloudTrail trails and event selectors
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CloudTrailCollector(BaseCollector):
    """Collector for AWS CloudTrail resources"""
    
    category = "management_governance"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize CloudTrail collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'cloudtrail')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CloudTrail resources
        
        Returns:
            Dictionary containing CloudTrail data
        """
        try:
            logger.info(f"Collecting CloudTrail trails from {self.region_name}")
            
            resources = []
            
            # Collect trails
            trails = self._collect_trails()
            resources.extend(trails)
            
            logger.info(f"Collected {len(resources)} CloudTrail trails from {self.region_name}")
            
            summary = {
                'total_trails': len(trails),
                'multi_region_trails': sum(1 for t in trails if t.get('is_multi_region')),
                'logging_enabled': sum(1 for t in trails if t.get('is_logging'))
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting CloudTrail resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_trails(self) -> List[Dict[str, Any]]:
        """Collect CloudTrail trails"""
        trails = []
        try:
            response = self.client.describe_trails()
            
            for trail in response.get('trailList', []):
                trail_arn = trail.get('TrailARN')
                trail_name = trail.get('Name')
                
                # Get trail status
                try:
                    status = self.client.get_trail_status(Name=trail_name)
                    
                    trails.append({
                        'resource_id': trail_arn,
                        'resource_type': 'cloudtrail-trail',
                        'resource_name': trail_name,
                        'region': self.region_name,
                        's3_bucket_name': trail.get('S3BucketName'),
                        'is_multi_region': trail.get('IsMultiRegionTrail', False),
                        'is_organization_trail': trail.get('IsOrganizationTrail', False),
                        'is_logging': status.get('IsLogging', False),
                        'log_file_validation_enabled': trail.get('LogFileValidationEnabled', False),
                        'home_region': trail.get('HomeRegion'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting trail status for {trail_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting CloudTrail trails: {e}")
        
        return trails
