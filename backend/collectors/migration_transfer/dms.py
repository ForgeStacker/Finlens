"""
Database Migration Service (DMS) Collector
Collects AWS DMS replication instances, tasks, and endpoints
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DMSCollector(BaseCollector):
    """Collector for AWS Database Migration Service resources"""
    
    category = "migration_transfer"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize DMS collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'dms')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect DMS resources
        
        Returns:
            Dictionary containing DMS data
        """
        try:
            logger.info(f"Collecting DMS resources from {self.region_name}")
            
            resources = []
            
            # Collect replication instances
            replication_instances = self._collect_replication_instances()
            resources.extend(replication_instances)
            
            # Collect replication tasks
            replication_tasks = self._collect_replication_tasks()
            resources.extend(replication_tasks)
            
            # Collect endpoints
            endpoints = self._collect_endpoints()
            resources.extend(endpoints)
            
            logger.info(f"Collected {len(resources)} DMS resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'replication_instances': len(replication_instances),
                'replication_tasks': len(replication_tasks),
                'endpoints': len(endpoints)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting DMS resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_replication_instances(self) -> List[Dict[str, Any]]:
        """Collect DMS replication instances"""
        instances = []
        try:
            response = self.client.describe_replication_instances()
            
            for instance in response.get('ReplicationInstances', []):
                instances.append({
                    'resource_id': instance.get('ReplicationInstanceArn'),
                    'resource_type': 'dms-replication-instance',
                    'resource_name': instance.get('ReplicationInstanceIdentifier'),
                    'region': self.region_name,
                    'status': instance.get('ReplicationInstanceStatus'),
                    'instance_class': instance.get('ReplicationInstanceClass'),
                    'engine_version': instance.get('EngineVersion'),
                    'allocated_storage': instance.get('AllocatedStorage'),
                    'multi_az': instance.get('MultiAZ'),
                    'creation_time': instance.get('InstanceCreateTime'),
                    'tags': []
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting DMS replication instances: {e}")
        
        return instances
    
    def _collect_replication_tasks(self) -> List[Dict[str, Any]]:
        """Collect DMS replication tasks"""
        tasks = []
        try:
            response = self.client.describe_replication_tasks()
            
            for task in response.get('ReplicationTasks', []):
                tasks.append({
                    'resource_id': task.get('ReplicationTaskArn'),
                    'resource_type': 'dms-replication-task',
                    'resource_name': task.get('ReplicationTaskIdentifier'),
                    'region': self.region_name,
                    'status': task.get('Status'),
                    'migration_type': task.get('MigrationType'),
                    'source_endpoint_arn': task.get('SourceEndpointArn'),
                    'target_endpoint_arn': task.get('TargetEndpointArn'),
                    'replication_instance_arn': task.get('ReplicationInstanceArn'),
                    'creation_time': task.get('ReplicationTaskCreationDate'),
                    'tags': []
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting DMS replication tasks: {e}")
        
        return tasks
    
    def _collect_endpoints(self) -> List[Dict[str, Any]]:
        """Collect DMS endpoints"""
        endpoints = []
        try:
            response = self.client.describe_endpoints()
            
            for endpoint in response.get('Endpoints', []):
                endpoints.append({
                    'resource_id': endpoint.get('EndpointArn'),
                    'resource_type': 'dms-endpoint',
                    'resource_name': endpoint.get('EndpointIdentifier'),
                    'region': self.region_name,
                    'status': endpoint.get('Status'),
                    'endpoint_type': endpoint.get('EndpointType'),
                    'engine_name': endpoint.get('EngineName'),
                    'server_name': endpoint.get('ServerName'),
                    'port': endpoint.get('Port'),
                    'database_name': endpoint.get('DatabaseName'),
                    'tags': []
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting DMS endpoints: {e}")
        
        return endpoints
