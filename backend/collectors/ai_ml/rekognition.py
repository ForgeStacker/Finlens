"""
Rekognition Collector
Collects AWS Rekognition collections and stream processors
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RekognitionCollector(BaseCollector):
    """Collector for AWS Rekognition resources"""
    
    category = "ai_ml"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Rekognition collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'rekognition')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Rekognition resources
        
        Returns:
            Dictionary containing Rekognition data
        """
        try:
            logger.info(f"Collecting Rekognition resources from {self.region_name}")
            
            resources = []
            
            # Collect collections
            collections = self._collect_collections()
            resources.extend(collections)
            
            # Collect stream processors
            stream_processors = self._collect_stream_processors()
            resources.extend(stream_processors)
            
            logger.info(f"Collected {len(resources)} Rekognition resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'collections': len(collections),
                'stream_processors': len(stream_processors)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Rekognition resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_collections(self) -> List[Dict[str, Any]]:
        """Collect Rekognition collections"""
        collections = []
        try:
            response = self.client.list_collections()
            
            for collection_id in response.get('CollectionIds', []):
                # Get collection details
                try:
                    detail = self.client.describe_collection(CollectionId=collection_id)
                    
                    collections.append({
                        'resource_id': detail.get('CollectionARN'),
                        'resource_type': 'rekognition-collection',
                        'resource_name': collection_id,
                        'region': self.region_name,
                        'face_count': detail.get('FaceCount'),
                        'face_model_version': detail.get('FaceModelVersion'),
                        'creation_timestamp': detail.get('CreationTimestamp'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting collection details for {collection_id}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Rekognition collections: {e}")
        
        return collections
    
    def _collect_stream_processors(self) -> List[Dict[str, Any]]:
        """Collect Rekognition stream processors"""
        stream_processors = []
        try:
            response = self.client.list_stream_processors()
            
            for processor in response.get('StreamProcessors', []):
                processor_name = processor.get('Name')
                
                # Get stream processor details
                try:
                    detail = self.client.describe_stream_processor(Name=processor_name)
                    
                    stream_processors.append({
                        'resource_id': detail.get('StreamProcessorArn'),
                        'resource_type': 'rekognition-stream-processor',
                        'resource_name': processor_name,
                        'region': self.region_name,
                        'status': processor.get('Status'),
                        'creation_timestamp': detail.get('CreationTimestamp'),
                        'last_update_timestamp': detail.get('LastUpdateTimestamp'),
                        'input': detail.get('Input'),
                        'output': detail.get('Output'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting stream processor details for {processor_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Rekognition stream processors: {e}")
        
        return stream_processors
