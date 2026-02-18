"""
EventBridge Collector
Collects EventBridge event bus and rule data from AWS
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EventBridgeCollector(BaseCollector):
    """Collects EventBridge information"""
    
    category = "integration"
    
    def __init__(self, profile_name: str, region_name: str):
        super().__init__(profile_name, region_name, 'events')
        self.collector_name = 'eventbridge'
    
    def collect(self) -> Dict[str, Any]:
        """Collect EventBridge data"""
        try:
            logger.info(f"Collecting EventBridge data from {self.region_name}")
            
            # Collect event buses
            event_buses = []
            buses_response = self.client.list_event_buses()
            
            for bus in buses_response.get('EventBuses', []):
                bus_name = bus.get('Name')
                
                # Get rules for this bus
                rules = []
                try:
                    rules_paginator = self.client.get_paginator('list_rules')
                    for rules_page in rules_paginator.paginate(EventBusName=bus_name):
                        for rule in rules_page.get('Rules', []):
                            rules.append({
                                'name': rule.get('Name'),
                                'state': rule.get('State'),
                                'description': rule.get('Description', ''),
                                'event_pattern': rule.get('EventPattern', 'Not configured'),
                                'schedule_expression': rule.get('ScheduleExpression', '')
                            })
                except Exception as e:
                    logger.warning(f"Failed to get rules for bus {bus_name}: {str(e)}")
                
                bus_data = {
                    'name': bus_name,
                    'arn': bus.get('Arn'),
                    'policy': bus.get('Policy', 'Not configured'),
                    'rules_count': len(rules),
                    'rules': rules,
                    'region': self.region_name
                }
                
                event_buses.append(bus_data)
            
            logger.info(f"Collected {len(event_buses)} EventBridge buses from {self.region_name}")
            
            return {
                'service': 'eventbridge',
                'region': self.region_name,
                'resource_count': len(event_buses),
                'event_buses': event_buses,
                'metadata': {
                    'scan_timestamp': self.scan_timestamp,
                    'collector_version': '1.0.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting EventBridge data: {str(e)}")
            raise
