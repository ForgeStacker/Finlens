"""
Comprehend Collector
Collects AWS Comprehend entities and sentiment analysis endpoints
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ComprehendCollector(BaseCollector):
    """Collector for AWS Comprehend resources"""
    
    category = "ai_ml"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Comprehend collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'comprehend')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Comprehend resources
        
        Returns:
            Dictionary containing Comprehend data
        """
        try:
            logger.info(f"Collecting Comprehend resources from {self.region_name}")
            
            resources = []
            
            # Collect entity recognizers
            entity_recognizers = self._collect_entity_recognizers()
            resources.extend(entity_recognizers)
            
            # Collect document classifiers
            document_classifiers = self._collect_document_classifiers()
            resources.extend(document_classifiers)
            
            # Collect endpoints
            endpoints = self._collect_endpoints()
            resources.extend(endpoints)
            
            logger.info(f"Collected {len(resources)} Comprehend resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'entity_recognizers': len(entity_recognizers),
                'document_classifiers': len(document_classifiers),
                'endpoints': len(endpoints)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Comprehend resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_entity_recognizers(self) -> List[Dict[str, Any]]:
        """Collect entity recognizers"""
        recognizers = []
        try:
            response = self.client.list_entity_recognizers()
            
            for props in response.get('EntityRecognizerPropertiesList', []):
                recognizers.append({
                    'resource_id': props.get('EntityRecognizerArn'),
                    'resource_type': 'entity-recognizer',
                    'resource_name': props.get('EntityRecognizerArn', '').split('/')[-1],
                    'region': self.region_name,
                    'status': props.get('Status'),
                    'language_code': props.get('LanguageCode'),
                    'submit_time': props.get('SubmitTime'),
                    'end_time': props.get('EndTime'),
                    'tags': {}
                })
        except Exception as e:
            logger.warning(f"Error collecting entity recognizers: {e}")
        
        return recognizers
    
    def _collect_document_classifiers(self) -> List[Dict[str, Any]]:
        """Collect document classifiers"""
        classifiers = []
        try:
            response = self.client.list_document_classifiers()
            
            for props in response.get('DocumentClassifierPropertiesList', []):
                classifiers.append({
                    'resource_id': props.get('DocumentClassifierArn'),
                    'resource_type': 'document-classifier',
                    'resource_name': props.get('DocumentClassifierArn', '').split('/')[-1],
                    'region': self.region_name,
                    'status': props.get('Status'),
                    'language_code': props.get('LanguageCode'),
                    'submit_time': props.get('SubmitTime'),
                    'end_time': props.get('EndTime'),
                    'tags': {}
                })
        except Exception as e:
            logger.warning(f"Error collecting document classifiers: {e}")
        
        return classifiers
    
    def _collect_endpoints(self) -> List[Dict[str, Any]]:
        """Collect endpoints"""
        endpoints = []
        try:
            response = self.client.list_endpoints()
            
            for props in response.get('EndpointPropertiesList', []):
                endpoints.append({
                    'resource_id': props.get('EndpointArn'),
                    'resource_type': 'endpoint',
                    'resource_name': props.get('EndpointArn', '').split('/')[-1],
                    'region': self.region_name,
                    'status': props.get('Status'),
                    'model_arn': props.get('ModelArn'),
                    'desired_inference_units': props.get('DesiredInferenceUnits'),
                    'current_inference_units': props.get('CurrentInferenceUnits'),
                    'creation_time': props.get('CreationTime'),
                    'tags': {}
                })
        except Exception as e:
            logger.warning(f"Error collecting endpoints: {e}")
        
        return endpoints
