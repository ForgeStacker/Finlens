"""
Secrets Manager Collector
Collects AWS Secrets Manager secrets
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SecretsManagerCollector(BaseCollector):
    """Collector for AWS Secrets Manager resources"""
    
    category = "security"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Secrets Manager collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'secretsmanager')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Secrets Manager resources
        
        Returns:
            Dictionary containing Secrets Manager data
        """
        try:
            logger.info(f"Collecting Secrets Manager secrets from {self.region_name}")
            
            resources = []
            
            # Collect secrets
            secrets = self._collect_secrets()
            resources.extend(secrets)
            
            logger.info(f"Collected {len(resources)} secrets from {self.region_name}")
            
            summary = {
                'total_secrets': len(secrets)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Secrets Manager resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_secrets(self) -> List[Dict[str, Any]]:
        """Collect secrets"""
        secrets = []
        try:
            response = self.client.list_secrets()
            
            for secret in response.get('SecretList', []):
                secrets.append({
                    'resource_id': secret.get('ARN'),
                    'resource_type': 'secret',
                    'resource_name': secret.get('Name'),
                    'region': self.region_name,
                    'arn': secret.get('ARN'),
                    'description': secret.get('Description'),
                    'kms_key_id': secret.get('KmsKeyId'),
                    'rotation_enabled': secret.get('RotationEnabled'),
                    'rotation_lambda_arn': secret.get('RotationLambdaARN'),
                    'last_rotated_date': secret.get('LastRotatedDate'),
                    'last_changed_date': secret.get('LastChangedDate'),
                    'last_accessed_date': secret.get('LastAccessedDate'),
                    'created_date': secret.get('CreatedDate'),
                    'tags': secret.get('Tags', [])
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting secrets: {e}")
        
        return secrets
