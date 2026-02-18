"""
CodeCommit Collector
Collects AWS CodeCommit repositories
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CodeCommitCollector(BaseCollector):
    """Collector for AWS CodeCommit resources"""
    
    category = "devops_tools"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize CodeCommit collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'codecommit')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CodeCommit resources
        
        Returns:
            Dictionary containing CodeCommit data
        """
        try:
            logger.info(f"Collecting CodeCommit repositories from {self.region_name}")
            
            resources = []
            
            # Collect repositories
            repositories = self._collect_repositories()
            resources.extend(repositories)
            
            logger.info(f"Collected {len(resources)} CodeCommit repositories from {self.region_name}")
            
            summary = {
                'total_repositories': len(repositories)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting CodeCommit resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_repositories(self) -> List[Dict[str, Any]]:
        """Collect CodeCommit repositories"""
        repositories = []
        try:
            response = self.client.list_repositories()
            
            for repo in response.get('repositories', []):
                repo_name = repo.get('repositoryName')
                
                # Get repository details
                try:
                    detail = self.client.get_repository(repositoryName=repo_name)
                    repo_metadata = detail.get('repositoryMetadata', {})
                    
                    repositories.append({
                        'resource_id': repo_metadata.get('repositoryId'),
                        'resource_type': 'codecommit-repository',
                        'resource_name': repo_name,
                        'region': self.region_name,
                        'arn': repo_metadata.get('Arn'),
                        'clone_url_http': repo_metadata.get('cloneUrlHttp'),
                        'clone_url_ssh': repo_metadata.get('cloneUrlSsh'),
                        'creation_date': repo_metadata.get('creationDate'),
                        'last_modified_date': repo_metadata.get('lastModifiedDate'),
                        'default_branch': repo_metadata.get('defaultBranch'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting repository details for {repo_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting CodeCommit repositories: {e}")
        
        return repositories
