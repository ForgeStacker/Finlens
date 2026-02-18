"""
CodePipeline Collector
Collects AWS CodePipeline pipelines
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CodePipelineCollector(BaseCollector):
    """Collector for AWS CodePipeline resources"""
    
    category = "devops_tools"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize CodePipeline collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'codepipeline')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CodePipeline resources
        
        Returns:
            Dictionary containing CodePipeline data
        """
        try:
            logger.info(f"Collecting CodePipeline pipelines from {self.region_name}")
            
            resources = []
            
            # Collect pipelines
            pipelines = self._collect_pipelines()
            resources.extend(pipelines)
            
            logger.info(f"Collected {len(resources)} CodePipeline pipelines from {self.region_name}")
            
            summary = {
                'total_pipelines': len(pipelines)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting CodePipeline resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_pipelines(self) -> List[Dict[str, Any]]:
        """Collect CodePipeline pipelines"""
        pipelines = []
        try:
            response = self.client.list_pipelines()
            
            for pipeline_summary in response.get('pipelines', []):
                pipeline_name = pipeline_summary.get('name')
                
                # Get pipeline details
                try:
                    detail = self.client.get_pipeline(name=pipeline_name)
                    pipeline = detail.get('pipeline', {})
                    metadata = detail.get('metadata', {})
                    
                    pipelines.append({
                        'resource_id': pipeline_name,
                        'resource_type': 'codepipeline-pipeline',
                        'resource_name': pipeline_name,
                        'region': self.region_name,
                        'version': pipeline_summary.get('version'),
                        'created': pipeline_summary.get('created'),
                        'updated': pipeline_summary.get('updated'),
                        'role_arn': pipeline.get('roleArn'),
                        'stage_count': len(pipeline.get('stages', [])),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting pipeline details for {pipeline_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting CodePipeline pipelines: {e}")
        
        return pipelines
