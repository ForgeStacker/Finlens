"""
Migration Hub Collector
Collects AWS Migration Hub applications and migration tasks
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MigrationHubCollector(BaseCollector):
    """Collector for AWS Migration Hub resources"""
    
    category = "migration_transfer"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Migration Hub collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'mgh')
        self.collector_name = 'migrationhub'
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Migration Hub resources
        
        Returns:
            Dictionary containing Migration Hub data
        """
        try:
            logger.info(f"Collecting Migration Hub resources from {self.region_name}")
            
            resources = []
            
            # Collect applications
            applications = self._collect_applications()
            resources.extend(applications)
            
            # Collect migration tasks
            migration_tasks = self._collect_migration_tasks()
            resources.extend(migration_tasks)
            
            logger.info(f"Collected {len(resources)} Migration Hub resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'applications': len(applications),
                'migration_tasks': len(migration_tasks)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Migration Hub resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_applications(self) -> List[Dict[str, Any]]:
        """Collect Migration Hub applications"""
        applications = []
        try:
            response = self.client.list_application_states()
            
            for app_state in response.get('ApplicationStateList', []):
                applications.append({
                    'resource_id': app_state.get('ApplicationId'),
                    'resource_type': 'migration-hub-application',
                    'resource_name': app_state.get('ApplicationId'),
                    'region': self.region_name,
                    'status': app_state.get('ApplicationStatus'),
                    'last_updated': app_state.get('LastUpdatedTime'),
                    'tags': {}
                })
        except Exception as e:
            logger.warning(f"Error collecting Migration Hub applications: {e}")
        
        return applications
    
    def _collect_migration_tasks(self) -> List[Dict[str, Any]]:
        """Collect migration tasks"""
        migration_tasks = []
        try:
            response = self.client.list_migration_tasks()
            
            for task in response.get('MigrationTaskSummaryList', []):
                migration_tasks.append({
                    'resource_id': task.get('MigrationTaskName'),
                    'resource_type': 'migration-task',
                    'resource_name': task.get('MigrationTaskName'),
                    'region': self.region_name,
                    'status': task.get('Status'),
                    'progress_update_stream': task.get('ProgressUpdateStream'),
                    'update_date_time': task.get('UpdateDateTime'),
                    'tags': {}
                })
        except Exception as e:
            logger.warning(f"Error collecting migration tasks: {e}")
        
        return migration_tasks
