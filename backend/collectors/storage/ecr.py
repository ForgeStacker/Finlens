"""
ECR Collector
Collects AWS ECR repositories and images
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ECRCollector(BaseCollector):
    """Collector for AWS ECR resources"""
    
    category = "storage"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize ECR collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'ecr')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect ECR resources
        
        Returns:
            Dictionary containing ECR data
        """
        try:
            logger.info(f"Collecting ECR repositories from {self.region_name}")
            
            resources = []
            
            # Collect repositories
            repositories = self._collect_repositories()
            resources.extend(repositories)
            
            logger.info(f"Collected {len(resources)} ECR repositories from {self.region_name}")
            
            summary = {
                'total_repositories': len(repositories)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting ECR resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_repositories(self) -> List[Dict[str, Any]]:
        """Collect ECR repositories"""
        repositories = []
        try:
            response = self.client.describe_repositories()
            
            for repo in response.get('repositories', []):
                repo_name = repo.get('repositoryName')
                
                # Get image count
                image_count = 0
                try:
                    images_response = self.client.list_images(repositoryName=repo_name)
                    image_count = len(images_response.get('imageIds', []))
                except Exception:
                    pass
                
                repositories.append({
                    'resource_id': repo.get('repositoryArn'),
                    'resource_type': 'ecr-repository',
                    'resource_name': repo_name,
                    'region': self.region_name,
                    'arn': repo.get('repositoryArn'),
                    'registry_id': repo.get('registryId'),
                    'repository_uri': repo.get('repositoryUri'),
                    'created_at': repo.get('createdAt'),
                    'image_tag_mutability': repo.get('imageTagMutability'),
                    'image_scanning_configuration': repo.get('imageScanningConfiguration'),
                    'encryption_configuration': repo.get('encryptionConfiguration'),
                    'image_count': image_count,
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting ECR repositories: {e}")
        
        return repositories
