"""
Snowball Collector
Collects AWS Snowball jobs
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SnowballCollector(BaseCollector):
    """Collector for AWS Snowball resources"""
    
    category = "migration_transfer"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Snowball collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'snowball')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Snowball resources
        
        Returns:
            Dictionary containing Snowball data
        """
        try:
            logger.info(f"Collecting Snowball jobs from {self.region_name}")
            
            resources = []
            
            # Collect jobs
            jobs = self._collect_jobs()
            resources.extend(jobs)
            
            logger.info(f"Collected {len(resources)} Snowball jobs from {self.region_name}")
            
            summary = {
                'total_jobs': len(jobs)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Snowball resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_jobs(self) -> List[Dict[str, Any]]:
        """Collect Snowball jobs"""
        jobs = []
        try:
            response = self.client.list_jobs()
            
            for job in response.get('JobListEntries', []):
                job_id = job.get('JobId')
                
                # Get job details
                try:
                    detail = self.client.describe_job(JobId=job_id)
                    job_metadata = detail.get('JobMetadata', {})
                    
                    jobs.append({
                        'resource_id': job_id,
                        'resource_type': 'snowball-job',
                        'resource_name': job_id,
                        'region': self.region_name,
                        'state': job.get('JobState'),
                        'job_type': job.get('JobType'),
                        'is_master': job.get('IsMaster'),
                        'creation_date': job.get('CreationDate'),
                        'description': job_metadata.get('Description'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting job details for {job_id}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Snowball jobs: {e}")
        
        return jobs
