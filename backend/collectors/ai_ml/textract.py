"""
Textract Collector
Collects AWS Textract adapters
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class TextractCollector(BaseCollector):
    """Collector for AWS Textract resources"""
    
    category = "ai_ml"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Textract collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'textract')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Textract resources
        
        Returns:
            Dictionary containing Textract data
        """
        try:
            logger.info(f"Collecting Textract adapters from {self.region_name}")
            
            resources = []
            
            # Collect adapters
            adapters = self._collect_adapters()
            resources.extend(adapters)
            
            logger.info(f"Collected {len(resources)} Textract adapters from {self.region_name}")
            
            summary = {
                'total_adapters': len(adapters)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Textract resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_adapters(self) -> List[Dict[str, Any]]:
        """Collect Textract adapters"""
        adapters = []
        try:
            response = self.client.list_adapters()
            
            for adapter in response.get('Adapters', []):
                adapter_id = adapter.get('AdapterId')
                
                # Get adapter details
                try:
                    detail = self.client.get_adapter(AdapterId=adapter_id)
                    
                    adapters.append({
                        'resource_id': adapter_id,
                        'resource_type': 'textract-adapter',
                        'resource_name': adapter.get('AdapterName'),
                        'region': self.region_name,
                        'creation_time': adapter.get('CreationTime'),
                        'feature_types': adapter.get('FeatureTypes', []),
                        'adapter_version': detail.get('AdapterVersion'),
                        'tags': detail.get('Tags', {})
                    })
                except Exception as e:
                    logger.warning(f"Error getting adapter details for {adapter_id}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Textract adapters: {e}")
        
        return adapters
