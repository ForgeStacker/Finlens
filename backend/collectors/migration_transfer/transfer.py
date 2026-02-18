"""
Transfer Family Collector
Collects AWS Transfer Family servers and users
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class TransferCollector(BaseCollector):
    """Collector for AWS Transfer Family resources"""
    
    category = "migration_transfer"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Transfer Family collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'transfer')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Transfer Family resources
        
        Returns:
            Dictionary containing Transfer Family data
        """
        try:
            logger.info(f"Collecting Transfer Family servers from {self.region_name}")
            
            resources = []
            
            # Collect servers
            servers = self._collect_servers()
            resources.extend(servers)
            
            logger.info(f"Collected {len(resources)} Transfer Family servers from {self.region_name}")
            
            summary = {
                'total_servers': len(servers)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Transfer Family resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_servers(self) -> List[Dict[str, Any]]:
        """Collect Transfer Family servers"""
        servers = []
        try:
            response = self.client.list_servers()
            
            for server in response.get('Servers', []):
                server_id = server.get('ServerId')
                
                # Get server details
                try:
                    detail = self.client.describe_server(ServerId=server_id)
                    server_detail = detail.get('Server', {})
                    
                    servers.append({
                        'resource_id': server.get('Arn'),
                        'resource_type': 'transfer-server',
                        'resource_name': server_id,
                        'region': self.region_name,
                        'state': server.get('State'),
                        'endpoint_type': server.get('EndpointType'),
                        'identity_provider_type': server_detail.get('IdentityProviderType'),
                        'protocols': server_detail.get('Protocols', []),
                        'user_count': server.get('UserCount'),
                        'tags': server_detail.get('Tags', [])
                    })
                except Exception as e:
                    logger.warning(f"Error getting server details for {server_id}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Transfer Family servers: {e}")
        
        return servers
