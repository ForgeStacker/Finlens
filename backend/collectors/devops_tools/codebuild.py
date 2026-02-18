"""
CodeBuild Collector
Collects AWS CodeBuild projects
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CodeBuildCollector(BaseCollector):
    """Collector for AWS CodeBuild resources"""
    
    category = "devops_tools"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize CodeBuild collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'codebuild')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CodeBuild resources
        
        Returns:
            Dictionary containing CodeBuild data
        """
        try:
            logger.info(f"Collecting CodeBuild projects from {self.region_name}")
            
            resources = []
            
            # Collect projects
            projects = self._collect_projects()
            resources.extend(projects)
            
            logger.info(f"Collected {len(resources)} CodeBuild projects from {self.region_name}")
            
            summary = {
                'total_projects': len(projects)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting CodeBuild resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_projects(self) -> List[Dict[str, Any]]:
        """Collect CodeBuild projects"""
        projects = []
        try:
            response = self.client.list_projects()
            project_names = response.get('projects', [])
            
            if project_names:
                # Batch get project details
                details_response = self.client.batch_get_projects(names=project_names)
                
                for project in details_response.get('projects', []):
                    projects.append({
                        'resource_id': project.get('arn'),
                        'resource_type': 'codebuild-project',
                        'resource_name': project.get('name'),
                        'region': self.region_name,
                        'arn': project.get('arn'),
                        'source_type': project.get('source', {}).get('type'),
                        'environment_type': project.get('environment', {}).get('type'),
                        'service_role': project.get('serviceRole'),
                        'created': project.get('created'),
                        'last_modified': project.get('lastModified'),
                        'tags': project.get('tags', [])
                    })
                    
        except Exception as e:
            logger.warning(f"Error collecting CodeBuild projects: {e}")
        
        return projects
