"""
CloudFormation Collector
Collects AWS CloudFormation stacks
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CloudFormationCollector(BaseCollector):
    """Collector for AWS CloudFormation resources"""
    
    category = "devops_tools"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize CloudFormation collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'cloudformation')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CloudFormation resources
        
        Returns:
            Dictionary containing CloudFormation data
        """
        try:
            logger.info(f"Collecting CloudFormation stacks from {self.region_name}")
            
            resources = []
            
            # Collect stacks
            stacks = self._collect_stacks()
            resources.extend(stacks)
            
            logger.info(f"Collected {len(resources)} CloudFormation stacks from {self.region_name}")
            
            summary = {
                'total_stacks': len(stacks),
                'status_distribution': self._get_status_distribution(stacks)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting CloudFormation resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_stacks(self) -> List[Dict[str, Any]]:
        """Collect CloudFormation stacks"""
        stacks = []
        try:
            response = self.client.list_stacks(
                StackStatusFilter=[
                    'CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE',
                    'ROLLBACK_COMPLETE', 'CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS',
                    'ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_IN_PROGRESS'
                ]
            )
            
            for stack_summary in response.get('StackSummaries', []):
                stack_name = stack_summary.get('StackName')
                
                # Get stack details
                try:
                    detail = self.client.describe_stacks(StackName=stack_name)
                    stack_details = detail.get('Stacks', [{}])[0]
                    
                    stacks.append({
                        'resource_id': stack_summary.get('StackId'),
                        'resource_type': 'cloudformation-stack',
                        'resource_name': stack_name,
                        'region': self.region_name,
                        'status': stack_summary.get('StackStatus'),
                        'creation_time': stack_summary.get('CreationTime'),
                        'last_updated_time': stack_summary.get('LastUpdatedTime'),
                        'drift_status': stack_summary.get('DriftInformation', {}).get('StackDriftStatus'),
                        'description': stack_details.get('Description'),
                        'capabilities': stack_details.get('Capabilities', []),
                        'tags': stack_details.get('Tags', [])
                    })
                except Exception as e:
                    logger.warning(f"Error getting stack details for {stack_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting CloudFormation stacks: {e}")
        
        return stacks
    
    def _get_status_distribution(self, stacks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of stack statuses"""
        distribution = {}
        for stack in stacks:
            status = stack.get('status', 'unknown')
            distribution[status] = distribution.get(status, 0) + 1
        return distribution
