"""
Systems Manager (SSM) Collector
Collects AWS Systems Manager parameters, documents, and managed instances
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SSMCollector(BaseCollector):
    """Collector for AWS Systems Manager resources"""
    
    category = "management_governance"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize SSM collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'ssm')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect SSM resources
        
        Returns:
            Dictionary containing SSM data
        """
        try:
            logger.info(f"Collecting SSM resources from {self.region_name}")
            
            resources = []
            
            # Collect parameters
            parameters = self._collect_parameters()
            resources.extend(parameters)
            
            # Collect documents
            documents = self._collect_documents()
            resources.extend(documents)
            
            # Collect managed instances
            instances = self._collect_managed_instances()
            resources.extend(instances)
            
            logger.info(f"Collected {len(resources)} SSM resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'parameters': len(parameters),
                'documents': len(documents),
                'managed_instances': len(instances)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting SSM resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_parameters(self) -> List[Dict[str, Any]]:
        """Collect SSM parameters"""
        parameters = []
        try:
            paginator = self.client.get_paginator('describe_parameters')
            
            for page in paginator.paginate():
                for param in page.get('Parameters', []):
                    parameters.append({
                        'resource_id': param.get('Name'),
                        'resource_type': 'ssm-parameter',
                        'resource_name': param.get('Name'),
                        'region': self.region_name,
                        'type': param.get('Type'),
                        'data_type': param.get('DataType'),
                        'last_modified_date': param.get('LastModifiedDate'),
                        'tier': param.get('Tier'),
                        'version': param.get('Version'),
                        'tags': {}
                    })
                    
        except Exception as e:
            logger.warning(f"Error collecting SSM parameters: {e}")
        
        return parameters
    
    def _collect_documents(self) -> List[Dict[str, Any]]:
        """Collect SSM documents"""
        documents = []
        try:
            paginator = self.client.get_paginator('list_documents')
            
            for page in paginator.paginate(Filters=[{'Key': 'Owner', 'Values': ['Self']}]):
                for doc in page.get('DocumentIdentifiers', []):
                    documents.append({
                        'resource_id': doc.get('Name'),
                        'resource_type': 'ssm-document',
                        'resource_name': doc.get('Name'),
                        'region': self.region_name,
                        'document_type': doc.get('DocumentType'),
                        'document_format': doc.get('DocumentFormat'),
                        'document_version': doc.get('DocumentVersion'),
                        'owner': doc.get('Owner'),
                        'platform_types': doc.get('PlatformTypes', []),
                        'tags': doc.get('Tags', [])
                    })
                    
        except Exception as e:
            logger.warning(f"Error collecting SSM documents: {e}")
        
        return documents
    
    def _collect_managed_instances(self) -> List[Dict[str, Any]]:
        """Collect SSM managed instances"""
        instances = []
        try:
            paginator = self.client.get_paginator('describe_instance_information')
            
            for page in paginator.paginate():
                for instance in page.get('InstanceInformationList', []):
                    instances.append({
                        'resource_id': instance.get('InstanceId'),
                        'resource_type': 'ssm-managed-instance',
                        'resource_name': instance.get('Name', instance.get('InstanceId')),
                        'region': self.region_name,
                        'ping_status': instance.get('PingStatus'),
                        'platform_type': instance.get('PlatformType'),
                        'platform_name': instance.get('PlatformName'),
                        'platform_version': instance.get('PlatformVersion'),
                        'agent_version': instance.get('AgentVersion'),
                        'last_ping_date_time': instance.get('LastPingDateTime'),
                        'tags': {}
                    })
                    
        except Exception as e:
            logger.warning(f"Error collecting SSM managed instances: {e}")
        
        return instances
