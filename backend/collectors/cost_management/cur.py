"""
Cost & Usage Report (CUR) Collector
Collects AWS Cost & Usage Report definitions
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CURCollector(BaseCollector):
    """Collector for AWS Cost & Usage Report resources"""
    
    category = "cost_management"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize CUR collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'cur')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CUR resources
        
        Returns:
            Dictionary containing CUR data
        """
        try:
            logger.info(f"Collecting Cost & Usage Reports from {self.region_name}")
            
            resources = []
            
            # Collect report definitions
            reports = self._collect_report_definitions()
            resources.extend(reports)
            
            logger.info(f"Collected {len(resources)} Cost & Usage Reports from {self.region_name}")
            
            summary = {
                'total_reports': len(reports)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Cost & Usage Reports: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_report_definitions(self) -> List[Dict[str, Any]]:
        """Collect CUR report definitions"""
        reports = []
        try:
            response = self.client.describe_report_definitions()
            
            for report in response.get('ReportDefinitions', []):
                reports.append({
                    'resource_id': report.get('ReportName'),
                    'resource_type': 'cur-report',
                    'resource_name': report.get('ReportName'),
                    'region': self.region_name,
                    'time_unit': report.get('TimeUnit'),
                    'format': report.get('Format'),
                    'compression': report.get('Compression'),
                    's3_bucket': report.get('S3Bucket'),
                    's3_prefix': report.get('S3Prefix'),
                    's3_region': report.get('S3Region'),
                    'additional_schema_elements': report.get('AdditionalSchemaElements', []),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting CUR report definitions: {e}")
        
        return reports
