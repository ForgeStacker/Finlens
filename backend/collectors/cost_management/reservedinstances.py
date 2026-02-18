"""
Reserved Instances Collector
Collects AWS Reserved Instances information
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ReservedInstancesCollector(BaseCollector):
    """Collector for AWS Reserved Instances resources"""
    
    category = "cost_management"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Reserved Instances collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'ec2')
        self.collector_name = 'reservedinstances'
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Reserved Instances resources
        
        Returns:
            Dictionary containing Reserved Instances data
        """
        try:
            logger.info(f"Collecting Reserved Instances from {self.region_name}")
            
            resources = []
            
            # Collect EC2 reserved instances
            ec2_ris = self._collect_ec2_reserved_instances()
            resources.extend(ec2_ris)
            
            # Collect RDS reserved instances
            rds_ris = self._collect_rds_reserved_instances()
            resources.extend(rds_ris)
            
            logger.info(f"Collected {len(resources)} Reserved Instances from {self.region_name}")
            
            summary = {
                'total_reserved_instances': len(resources),
                'ec2_reserved_instances': len(ec2_ris),
                'rds_reserved_instances': len(rds_ris)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Reserved Instances: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_ec2_reserved_instances(self) -> List[Dict[str, Any]]:
        """Collect EC2 reserved instances"""
        reserved_instances = []
        try:
            response = self.client.describe_reserved_instances()
            
            for ri in response.get('ReservedInstances', []):
                reserved_instances.append({
                    'resource_id': ri.get('ReservedInstancesId'),
                    'resource_type': 'ec2-reserved-instance',
                    'resource_name': ri.get('ReservedInstancesId'),
                    'region': self.region_name,
                    'instance_type': ri.get('InstanceType'),
                    'instance_count': ri.get('InstanceCount'),
                    'state': ri.get('State'),
                    'offering_type': ri.get('OfferingType'),
                    'offering_class': ri.get('OfferingClass'),
                    'start': ri.get('Start'),
                    'end': ri.get('End'),
                    'duration': ri.get('Duration'),
                    'fixed_price': ri.get('FixedPrice'),
                    'usage_price': ri.get('UsagePrice'),
                    'tags': ri.get('Tags', [])
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting EC2 reserved instances: {e}")
        
        return reserved_instances
    
    def _collect_rds_reserved_instances(self) -> List[Dict[str, Any]]:
        """Collect RDS reserved instances"""
        reserved_instances = []
        try:
            # Create RDS client
            from backend.utils.aws_client import get_aws_client
            rds_client = get_aws_client('rds', self.profile_name, self.region_name)
            
            if rds_client:
                response = rds_client.describe_reserved_db_instances()
                
                for ri in response.get('ReservedDBInstances', []):
                    reserved_instances.append({
                        'resource_id': ri.get('ReservedDBInstanceId'),
                        'resource_type': 'rds-reserved-instance',
                        'resource_name': ri.get('ReservedDBInstanceId'),
                        'region': self.region_name,
                        'db_instance_class': ri.get('DBInstanceClass'),
                        'db_instance_count': ri.get('DBInstanceCount'),
                        'state': ri.get('State'),
                        'offering_type': ri.get('OfferingType'),
                        'start_time': ri.get('StartTime'),
                        'duration': ri.get('Duration'),
                        'fixed_price': ri.get('FixedPrice'),
                        'usage_price': ri.get('UsagePrice'),
                        'tags': {}
                    })
                    
        except Exception as e:
            logger.warning(f"Error collecting RDS reserved instances: {e}")
        
        return reserved_instances
