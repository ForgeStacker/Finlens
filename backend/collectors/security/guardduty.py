"""
GuardDuty Collector
Collects AWS GuardDuty detectors and findings
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class GuardDutyCollector(BaseCollector):
    """Collector for AWS GuardDuty resources"""
    
    category = "security"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize GuardDuty collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'guardduty')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect GuardDuty resources
        
        Returns:
            Dictionary containing GuardDuty data
        """
        try:
            logger.info(f"Collecting GuardDuty detectors from {self.region_name}")
            
            resources = []
            
            # Collect detectors
            detectors = self._collect_detectors()
            resources.extend(detectors)
            
            logger.info(f"Collected {len(resources)} GuardDuty detectors from {self.region_name}")
            
            summary = {
                'total_detectors': len(detectors)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting GuardDuty resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_detectors(self) -> List[Dict[str, Any]]:
        """Collect GuardDuty detectors"""
        detectors = []
        try:
            response = self.client.list_detectors()
            
            for detector_id in response.get('DetectorIds', []):
                # Get detector details
                try:
                    detector_detail = self.client.get_detector(DetectorId=detector_id)
                    
                    # Get finding statistics
                    finding_stats = {}
                    try:
                        stats_response = self.client.get_findings_statistics(
                            DetectorId=detector_id,
                            FindingStatisticTypes=['COUNT_BY_SEVERITY']
                        )
                        finding_stats = stats_response.get('FindingStatistics', {}).get('CountBySeverity', {})
                    except Exception:
                        pass
                    
                    detectors.append({
                        'resource_id': detector_id,
                        'resource_type': 'guardduty-detector',
                        'resource_name': detector_id,
                        'region': self.region_name,
                        'status': detector_detail.get('Status'),
                        'service_role': detector_detail.get('ServiceRole'),
                        'created_at': detector_detail.get('CreatedAt'),
                        'updated_at': detector_detail.get('UpdatedAt'),
                        'finding_publishing_frequency': detector_detail.get('FindingPublishingFrequency'),
                        'finding_statistics': finding_stats,
                        'tags': detector_detail.get('Tags', {})
                    })
                except Exception as e:
                    logger.warning(f"Error getting detector details for {detector_id}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting GuardDuty detectors: {e}")
        
        return detectors
