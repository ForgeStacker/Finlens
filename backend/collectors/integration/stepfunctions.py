"""
Step Functions Collector
Collects Step Functions state machine data from AWS
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class StepFunctionsCollector(BaseCollector):
    """Collects Step Functions state machine information"""
    
    category = "integration"
    
    def __init__(self, profile_name: str, region_name: str):
        super().__init__(profile_name, region_name, 'stepfunctions')
    
    def collect(self) -> Dict[str, Any]:
        """Collect Step Functions data"""
        try:
            logger.info(f"Collecting Step Functions from {self.region_name}")
            
            state_machines = []
            paginator = self.client.get_paginator('list_state_machines')
            
            for page in paginator.paginate():
                for sm in page.get('stateMachines', []):
                    sm_arn = sm.get('stateMachineArn')
                    
                    try:
                        # Get detailed info
                        details = self.client.describe_state_machine(stateMachineArn=sm_arn)
                        
                        # Get execution count
                        executions = self.client.list_executions(
                            stateMachineArn=sm_arn,
                            maxResults=10
                        )
                        
                        sm_data = {
                            'name': sm.get('name'),
                            'arn': sm_arn,
                            'type': sm.get('type'),
                            'status': details.get('status'),
                            'creation_date': str(sm.get('creationDate')),
                            'role_arn': details.get('roleArn'),
                            'definition': details.get('definition', 'Not available'),
                            'logging_configuration': details.get('loggingConfiguration', {}),
                            'tracing_configuration': details.get('tracingConfiguration', {}),
                            'recent_executions_count': len(executions.get('executions', [])),
                            'region': self.region_name
                        }
                        
                        state_machines.append(sm_data)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get details for state machine {sm_arn}: {str(e)}")
                        continue
            
            logger.info(f"Collected {len(state_machines)} Step Functions from {self.region_name}")
            
            return {
                'service': 'stepfunctions',
                'region': self.region_name,
                'resource_count': len(state_machines),
                'state_machines': state_machines,
                'metadata': {
                    'scan_timestamp': self.scan_timestamp,
                    'collector_version': '1.0.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting Step Functions data: {str(e)}")
            raise
