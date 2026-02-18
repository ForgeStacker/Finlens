"""
Savings Plans Collector
Collects AWS Savings Plans information
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SavingsPlansCollector(BaseCollector):
    """Collector for AWS Savings Plans resources"""
    
    category = "cost_management"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Savings Plans collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'savingsplans')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Savings Plans resources
        
        Returns:
            Dictionary containing Savings Plans data
        """
        try:
            logger.info(f"Collecting Savings Plans from {self.region_name}")
            
            resources = []
            
            # Collect savings plans
            savings_plans = self._collect_savings_plans()
            resources.extend(savings_plans)
            
            logger.info(f"Collected {len(resources)} Savings Plans from {self.region_name}")
            
            summary = {
                'total_savings_plans': len(savings_plans),
                'state_distribution': self._get_state_distribution(savings_plans)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Savings Plans: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_savings_plans(self) -> List[Dict[str, Any]]:
        """Collect Savings Plans"""
        savings_plans = []
        try:
            response = self.client.describe_savings_plans()
            
            for plan in response.get('savingsPlans', []):
                savings_plans.append({
                    'resource_id': plan.get('savingsPlanId'),
                    'resource_type': 'savings-plan',
                    'resource_name': plan.get('savingsPlanId'),
                    'region': self.region_name,
                    'savings_plan_arn': plan.get('savingsPlanArn'),
                    'savings_plan_type': plan.get('savingsPlanType'),
                    'payment_option': plan.get('paymentOption'),
                    'state': plan.get('state'),
                    'commitment': plan.get('commitment'),
                    'upfront_payment_amount': plan.get('upfrontPaymentAmount'),
                    'recurring_payment_amount': plan.get('recurringPaymentAmount'),
                    'start': plan.get('start'),
                    'end': plan.get('end'),
                    'tags': plan.get('tags', {})
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting Savings Plans: {e}")
        
        return savings_plans
    
    def _get_state_distribution(self, plans: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of savings plan states"""
        distribution = {}
        for plan in plans:
            state = plan.get('state', 'unknown')
            distribution[state] = distribution.get(state, 0) + 1
        return distribution
