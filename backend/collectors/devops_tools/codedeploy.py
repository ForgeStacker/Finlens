"""
CodeDeploy Collector
Collects AWS CodeDeploy applications and deployment groups
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CodeDeployCollector(BaseCollector):
    """Collector for AWS CodeDeploy resources"""
    
    category = "devops_tools"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize CodeDeploy collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'codedeploy')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CodeDeploy resources
        
        Returns:
            Dictionary containing CodeDeploy data
        """
        try:
            logger.info(f"Collecting CodeDeploy applications from {self.region_name}")
            
            resources = []
            
            # Collect applications
            applications = self._collect_applications()
            resources.extend(applications)
            
            logger.info(f"Collected {len(resources)} CodeDeploy applications from {self.region_name}")
            
            summary = {
                'total_applications': len(applications)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting CodeDeploy resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_applications(self) -> List[Dict[str, Any]]:
        """Collect CodeDeploy applications"""
        applications = []
        try:
            response = self.client.list_applications()
            app_names = response.get('applications', [])
            
            for app_name in app_names:
                # Get application details
                try:
                    detail = self.client.get_application(applicationName=app_name)
                    app_info = detail.get('application', {})
                    
                    # Get deployment groups for this application
                    dg_response = self.client.list_deployment_groups(applicationName=app_name)
                    deployment_group_count = len(dg_response.get('deploymentGroups', []))
                    
                    applications.append({
                        'resource_id': app_info.get('applicationId'),
                        'resource_type': 'codedeploy-application',
                        'resource_name': app_name,
                        'region': self.region_name,
                        'application_id': app_info.get('applicationId'),
                        'compute_platform': app_info.get('computePlatform'),
                        'deployment_groups': deployment_group_count,
                        'create_time': app_info.get('createTime'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting application details for {app_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting CodeDeploy applications: {e}")
        
        return applications
