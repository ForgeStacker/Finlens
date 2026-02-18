"""
DataSync Collector
Collects AWS DataSync tasks, locations, and agents
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class DataSyncCollector(BaseCollector):
    """Collector for AWS DataSync resources"""
    
    category = "migration_transfer"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize DataSync collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'datasync')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect DataSync resources
        
        Returns:
            Dictionary containing DataSync data
        """
        try:
            logger.info(f"Collecting DataSync resources from {self.region_name}")
            
            resources = []
            
            # Collect tasks
            tasks = self._collect_tasks()
            resources.extend(tasks)
            
            # Collect locations
            locations = self._collect_locations()
            resources.extend(locations)
            
            # Collect agents
            agents = self._collect_agents()
            resources.extend(agents)
            
            logger.info(f"Collected {len(resources)} DataSync resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'tasks': len(tasks),
                'locations': len(locations),
                'agents': len(agents)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting DataSync resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_tasks(self) -> List[Dict[str, Any]]:
        """Collect DataSync tasks"""
        tasks = []
        try:
            response = self.client.list_tasks()
            
            for task in response.get('Tasks', []):
                task_arn = task.get('TaskArn')
                
                # Get task details
                try:
                    detail = self.client.describe_task(TaskArn=task_arn)
                    
                    tasks.append({
                        'resource_id': task_arn,
                        'resource_type': 'datasync-task',
                        'resource_name': task.get('Name', task_arn.split('/')[-1]),
                        'region': self.region_name,
                        'status': task.get('Status'),
                        'source_location': detail.get('SourceLocationArn'),
                        'destination_location': detail.get('DestinationLocationArn'),
                        'creation_time': detail.get('CreationTime'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting task details for {task_arn}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting DataSync tasks: {e}")
        
        return tasks
    
    def _collect_locations(self) -> List[Dict[str, Any]]:
        """Collect DataSync locations"""
        locations = []
        try:
            response = self.client.list_locations()
            
            for location in response.get('Locations', []):
                location_arn = location.get('LocationArn')
                
                locations.append({
                    'resource_id': location_arn,
                    'resource_type': 'datasync-location',
                    'resource_name': location_arn.split('/')[-1],
                    'region': self.region_name,
                    'location_uri': location.get('LocationUri'),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting DataSync locations: {e}")
        
        return locations
    
    def _collect_agents(self) -> List[Dict[str, Any]]:
        """Collect DataSync agents"""
        agents = []
        try:
            response = self.client.list_agents()
            
            for agent in response.get('Agents', []):
                agent_arn = agent.get('AgentArn')
                
                # Get agent details
                try:
                    detail = self.client.describe_agent(AgentArn=agent_arn)
                    
                    agents.append({
                        'resource_id': agent_arn,
                        'resource_type': 'datasync-agent',
                        'resource_name': agent.get('Name', agent_arn.split('/')[-1]),
                        'region': self.region_name,
                        'status': detail.get('Status'),
                        'creation_time': detail.get('CreationTime'),
                        'last_connection_time': detail.get('LastConnectionTime'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting agent details for {agent_arn}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting DataSync agents: {e}")
        
        return agents
