"""
AWS Config Collector
Collects AWS Config rules and recorders
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigCollector(BaseCollector):
    """Collector for AWS Config resources"""
    
    category = "management_governance"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize AWS Config collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'config')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect AWS Config resources
        
        Returns:
            Dictionary containing Config data
        """
        try:
            logger.info(f"Collecting AWS Config resources from {self.region_name}")
            
            resources = []
            
            # Collect configuration recorders
            recorders = self._collect_recorders()
            resources.extend(recorders)
            
            # Collect config rules
            rules = self._collect_rules()
            resources.extend(rules)
            
            logger.info(f"Collected {len(resources)} AWS Config resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'recorders': len(recorders),
                'config_rules': len(rules)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting AWS Config resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_recorders(self) -> List[Dict[str, Any]]:
        """Collect AWS Config recorders"""
        recorders = []
        try:
            response = self.client.describe_configuration_recorders()
            
            for recorder in response.get('ConfigurationRecorders', []):
                recorder_name = recorder.get('name')
                
                # Get recorder status
                try:
                    status_response = self.client.describe_configuration_recorder_status(
                        ConfigurationRecorderNames=[recorder_name]
                    )
                    status = status_response.get('ConfigurationRecordersStatus', [{}])[0]
                    
                    recorders.append({
                        'resource_id': recorder_name,
                        'resource_type': 'config-recorder',
                        'resource_name': recorder_name,
                        'region': self.region_name,
                        'role_arn': recorder.get('roleARN'),
                        'recording': status.get('recording', False),
                        'last_status': status.get('lastStatus'),
                        'last_start_time': status.get('lastStartTime'),
                        'last_stop_time': status.get('lastStopTime'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting recorder status for {recorder_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Config recorders: {e}")
        
        return recorders
    
    def _collect_rules(self) -> List[Dict[str, Any]]:
        """Collect AWS Config rules"""
        rules = []
        try:
            response = self.client.describe_config_rules()
            
            for rule in response.get('ConfigRules', []):
                rules.append({
                    'resource_id': rule.get('ConfigRuleArn'),
                    'resource_type': 'config-rule',
                    'resource_name': rule.get('ConfigRuleName'),
                    'region': self.region_name,
                    'config_rule_state': rule.get('ConfigRuleState'),
                    'source': rule.get('Source', {}).get('Owner'),
                    'source_identifier': rule.get('Source', {}).get('SourceIdentifier'),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting Config rules: {e}")
        
        return rules
