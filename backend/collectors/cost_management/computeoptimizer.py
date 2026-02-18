"""
Compute Optimizer Collector
Collects AWS Compute Optimizer recommendations
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ComputeOptimizerCollector(BaseCollector):
    """Collector for AWS Compute Optimizer resources"""
    
    category = "cost_management"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Compute Optimizer collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'compute-optimizer')
        self.collector_name = 'computeoptimizer'
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Compute Optimizer resources
        
        Returns:
            Dictionary containing Compute Optimizer data
        """
        try:
            logger.info(f"Collecting Compute Optimizer recommendations from {self.region_name}")
            
            resources = []
            
            # Collect EC2 recommendations
            ec2_recommendations = self._collect_ec2_recommendations()
            resources.extend(ec2_recommendations)
            
            # Collect Auto Scaling group recommendations
            asg_recommendations = self._collect_asg_recommendations()
            resources.extend(asg_recommendations)
            
            # Collect EBS volume recommendations
            ebs_recommendations = self._collect_ebs_recommendations()
            resources.extend(ebs_recommendations)
            
            # Collect Lambda recommendations
            lambda_recommendations = self._collect_lambda_recommendations()
            resources.extend(lambda_recommendations)
            
            logger.info(f"Collected {len(resources)} Compute Optimizer recommendations from {self.region_name}")
            
            summary = {
                'total_recommendations': len(resources),
                'ec2_recommendations': len(ec2_recommendations),
                'asg_recommendations': len(asg_recommendations),
                'ebs_recommendations': len(ebs_recommendations),
                'lambda_recommendations': len(lambda_recommendations)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Compute Optimizer recommendations: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_ec2_recommendations(self) -> List[Dict[str, Any]]:
        """Collect EC2 instance recommendations"""
        recommendations = []
        try:
            response = self.client.get_ec2_instance_recommendations()
            
            for rec in response.get('instanceRecommendations', []):
                recommendations.append({
                    'resource_id': rec.get('instanceArn'),
                    'resource_type': 'compute-optimizer-ec2-recommendation',
                    'resource_name': rec.get('instanceName', rec.get('instanceArn', '').split('/')[-1]),
                    'region': self.region_name,
                    'current_instance_type': rec.get('currentInstanceType'),
                    'finding': rec.get('finding'),
                    'finding_reason_codes': rec.get('findingReasonCodes', []),
                    'recommendation_options': rec.get('recommendationOptions', []),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting EC2 recommendations: {e}")
        
        return recommendations
    
    def _collect_asg_recommendations(self) -> List[Dict[str, Any]]:
        """Collect Auto Scaling group recommendations"""
        recommendations = []
        try:
            response = self.client.get_auto_scaling_group_recommendations()
            
            for rec in response.get('autoScalingGroupRecommendations', []):
                recommendations.append({
                    'resource_id': rec.get('autoScalingGroupArn'),
                    'resource_type': 'compute-optimizer-asg-recommendation',
                    'resource_name': rec.get('autoScalingGroupName'),
                    'region': self.region_name,
                    'current_configuration': rec.get('currentConfiguration', {}),
                    'finding': rec.get('finding'),
                    'recommendation_options': rec.get('recommendationOptions', []),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting ASG recommendations: {e}")
        
        return recommendations
    
    def _collect_ebs_recommendations(self) -> List[Dict[str, Any]]:
        """Collect EBS volume recommendations"""
        recommendations = []
        try:
            response = self.client.get_ebs_volume_recommendations()
            
            for rec in response.get('volumeRecommendations', []):
                recommendations.append({
                    'resource_id': rec.get('volumeArn'),
                    'resource_type': 'compute-optimizer-ebs-recommendation',
                    'resource_name': rec.get('volumeArn', '').split('/')[-1],
                    'region': self.region_name,
                    'current_configuration': rec.get('currentConfiguration', {}),
                    'finding': rec.get('finding'),
                    'volume_recommendation_options': rec.get('volumeRecommendationOptions', []),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting EBS recommendations: {e}")
        
        return recommendations
    
    def _collect_lambda_recommendations(self) -> List[Dict[str, Any]]:
        """Collect Lambda function recommendations"""
        recommendations = []
        try:
            response = self.client.get_lambda_function_recommendations()
            
            for rec in response.get('lambdaFunctionRecommendations', []):
                recommendations.append({
                    'resource_id': rec.get('functionArn'),
                    'resource_type': 'compute-optimizer-lambda-recommendation',
                    'resource_name': rec.get('functionArn', '').split(':')[-1],
                    'region': self.region_name,
                    'current_memory_size': rec.get('currentMemorySize'),
                    'finding': rec.get('finding'),
                    'finding_reason_codes': rec.get('findingReasonCodes', []),
                    'memory_size_recommendation_options': rec.get('memorySizeRecommendationOptions', []),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting Lambda recommendations: {e}")
        
        return recommendations
