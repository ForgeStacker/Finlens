"""
API Gateway Collector
Collects API Gateway REST and HTTP APIs from AWS
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class APIGatewayCollector(BaseCollector):
    """Collects API Gateway information"""
    
    category = "integration"
    
    def __init__(self, profile_name: str, region_name: str):
        super().__init__(profile_name, region_name, 'apigateway')
    
    def collect(self) -> Dict[str, Any]:
        """Collect API Gateway data"""
        try:
            logger.info(f"Collecting API Gateway APIs from {self.region_name}")
            
            apis = []
            
            # Collect REST APIs
            try:
                rest_apis_response = self.client.get_rest_apis()
                for api in rest_apis_response.get('items', []):
                    api_id = api.get('id')
                    
                    # Get stages
                    stages = []
                    try:
                        stages_response = self.client.get_stages(restApiId=api_id)
                        stages = [
                            {
                                'name': stage.get('stageName'),
                                'deployment_id': stage.get('deploymentId'),
                                'description': stage.get('description', ''),
                                'cache_enabled': stage.get('cacheClusterEnabled', False),
                                'created_date': str(stage.get('createdDate', ''))
                            }
                            for stage in stages_response.get('item', [])
                        ]
                    except Exception as e:
                        logger.warning(f"Failed to get stages for API {api_id}: {str(e)}")
                    
                    api_data = {
                        'api_id': api_id,
                        'name': api.get('name'),
                        'api_type': 'REST',
                        'description': api.get('description', ''),
                        'created_date': str(api.get('createdDate', '')),
                        'version': api.get('version', ''),
                        'endpoint_configuration': api.get('endpointConfiguration', {}),
                        'stages_count': len(stages),
                        'stages': stages,
                        'region': self.region_name
                    }
                    
                    apis.append(api_data)
            except Exception as e:
                logger.warning(f"Failed to collect REST APIs: {str(e)}")
            
            # Collect HTTP APIs (API Gateway v2)
            try:
                from backend.utils.aws_client import get_aws_client
                apigw_v2_client = get_aws_client(self.profile_name, self.region_name, 'apigatewayv2')
                
                if apigw_v2_client:
                    http_apis_response = apigw_v2_client.get_apis()
                    for api in http_apis_response.get('Items', []):
                        api_id = api.get('ApiId')
                        
                        api_data = {
                            'api_id': api_id,
                            'name': api.get('Name'),
                            'api_type': 'HTTP',
                            'protocol_type': api.get('ProtocolType'),
                            'description': api.get('Description', ''),
                            'created_date': str(api.get('CreatedDate', '')),
                            'api_endpoint': api.get('ApiEndpoint'),
                            'region': self.region_name
                        }
                        
                        apis.append(api_data)
            except Exception as e:
                logger.warning(f"Failed to collect HTTP APIs: {str(e)}")
            
            logger.info(f"Collected {len(apis)} API Gateway APIs from {self.region_name}")
            
            return {
                'service': 'apigateway',
                'region': self.region_name,
                'resource_count': len(apis),
                'apis': apis,
                'metadata': {
                    'scan_timestamp': self.scan_timestamp,
                    'collector_version': '1.0.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting API Gateway data: {str(e)}")
            raise
