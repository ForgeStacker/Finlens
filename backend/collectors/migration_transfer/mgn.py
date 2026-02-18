"""
Application Migration Service (MGN) Collector
Collects AWS Application Migration Service source servers and jobs
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MGNCollector(BaseCollector):
    """Collector for AWS Application Migration Service resources"""
    
    category = "migration_transfer"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize MGN collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'mgn')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect MGN resources
        
        Returns:
            Dictionary containing MGN data
        """
        try:
            logger.info(f"Collecting MGN resources from {self.region_name}")
            
            resources = []
            
            # Collect source servers
            source_servers = self._collect_source_servers()
            resources.extend(source_servers)
            
            # Collect jobs
            jobs = self._collect_jobs()
            resources.extend(jobs)
            
            logger.info(f"Collected {len(resources)} MGN resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'source_servers': len(source_servers),
                'jobs': len(jobs)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting MGN resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_source_servers(self) -> List[Dict[str, Any]]:
        """Collect MGN source servers"""
        source_servers = []
        try:
            response = self.client.describe_source_servers()
            
            for server in response.get('items', []):
                source_servers.append({
                    'resource_id': server.get('sourceServerID'),
                    'resource_type': 'mgn-source-server',
                    'resource_name': server.get('sourceServerID'),
                    'region': self.region_name,
                    'lifecycle_state': server.get('lifeCycle', {}).get('state'),
                    'replication_status': server.get('dataReplicationInfo', {}).get('dataReplicationState'),
                    'last_launch_result': server.get('lifeCycle', {}).get('lastLaunch', {}).get('initiated', {}).get('type'),
                    'arn': server.get('arn'),
                    'tags': server.get('tags', {})
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting MGN source servers: {e}")
        
        return source_servers
    
    def _collect_jobs(self) -> List[Dict[str, Any]]:
        """Collect MGN jobs"""
        jobs = []
        try:
            response = self.client.describe_jobs(filters={})
            
            for job in response.get('items', []):
                jobs.append({
                    'resource_id': job.get('jobID'),
                    'resource_type': 'mgn-job',
                    'resource_name': job.get('jobID'),
                    'region': self.region_name,
                    'status': job.get('status'),
                    'type': job.get('type'),
                    'creation_date_time': job.get('creationDateTime'),
                    'end_date_time': job.get('endDateTime'),
                    'arn': job.get('arn'),
                    'tags': job.get('tags', {})
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting MGN jobs: {e}")
        
        return jobs
