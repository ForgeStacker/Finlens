"""
Budgets Collector
Collects AWS Budgets information
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class BudgetsCollector(BaseCollector):
    """Collector for AWS Budgets resources"""
    
    category = "cost_management"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Budgets collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'budgets')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Budgets resources
        
        Returns:
            Dictionary containing Budgets data
        """
        try:
            logger.info(f"Collecting Budgets from {self.region_name}")
            
            resources = []
            
            # Collect budgets
            budgets = self._collect_budgets()
            resources.extend(budgets)
            
            logger.info(f"Collected {len(resources)} Budgets from {self.region_name}")
            
            summary = {
                'total_budgets': len(budgets)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Budgets: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_budgets(self) -> List[Dict[str, Any]]:
        """Collect AWS Budgets"""
        budgets = []
        try:
            response = self.client.describe_budgets(AccountId=self.account_id)
            
            for budget in response.get('Budgets', []):
                budget_name = budget.get('BudgetName')
                
                budgets.append({
                    'resource_id': budget_name,
                    'resource_type': 'budget',
                    'resource_name': budget_name,
                    'region': self.region_name,
                    'budget_type': budget.get('BudgetType'),
                    'budget_limit': budget.get('BudgetLimit', {}),
                    'time_unit': budget.get('TimeUnit'),
                    'time_period': budget.get('TimePeriod', {}),
                    'calculated_spend': budget.get('CalculatedSpend', {}),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting Budgets: {e}")
        
        return budgets
