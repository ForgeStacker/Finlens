"""
KMS Collector
Collects AWS KMS keys and aliases
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class KMSCollector(BaseCollector):
    """Collector for AWS KMS resources"""
    
    category = "security"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize KMS collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'kms')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect KMS resources
        
        Returns:
            Dictionary containing KMS data
        """
        try:
            logger.info(f"Collecting KMS keys from {self.region_name}")
            
            resources = []
            
            # Collect keys
            keys = self._collect_keys()
            resources.extend(keys)
            
            logger.info(f"Collected {len(resources)} KMS keys from {self.region_name}")
            
            summary = {
                'total_keys': len(keys),
                'key_state_distribution': self._get_key_state_distribution(keys)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting KMS resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_keys(self) -> List[Dict[str, Any]]:
        """Collect KMS keys"""
        keys = []
        try:
            response = self.client.list_keys()
            
            for key_entry in response.get('Keys', []):
                key_id = key_entry.get('KeyId')
                
                # Get key details
                try:
                    key_metadata = self.client.describe_key(KeyId=key_id)
                    key_info = key_metadata.get('KeyMetadata', {})
                    
                    # Get aliases
                    aliases_response = self.client.list_aliases(KeyId=key_id)
                    aliases = [alias.get('AliasName') for alias in aliases_response.get('Aliases', [])]
                    
                    keys.append({
                        'resource_id': key_id,
                        'resource_type': 'kms-key',
                        'resource_name': aliases[0] if aliases else key_id,
                        'region': self.region_name,
                        'key_state': key_info.get('KeyState'),
                        'key_usage': key_info.get('KeyUsage'),
                        'key_manager': key_info.get('KeyManager'),
                        'creation_date': key_info.get('CreationDate'),
                        'enabled': key_info.get('Enabled'),
                        'arn': key_info.get('Arn'),
                        'aliases': aliases,
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting key details for {key_id}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting KMS keys: {e}")
        
        return keys
    
    def _get_key_state_distribution(self, keys: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of key states"""
        distribution = {}
        for key in keys:
            state = key.get('key_state', 'unknown')
            distribution[state] = distribution.get(state, 0) + 1
        return distribution
