"""
Cost Explorer Collector
Collects AWS Cost Explorer cost and usage data
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CostExplorerCollector(BaseCollector):
    """Collector for AWS Cost Explorer data"""
    
    category = "cost_management"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Cost Explorer collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'ce')
        self.collector_name = 'costexplorer'
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Cost Explorer data
        
        Returns:
            Dictionary containing Cost Explorer data
        """
        try:
            logger.info(f"Collecting Cost Explorer data from {self.region_name}")
            
            resources = []
            
            # Get cost and usage for last 30 days
            cost_data = self._collect_cost_and_usage()
            resources.append(cost_data)
            
            # Get cost forecast
            forecast_data = self._collect_cost_forecast()
            resources.append(forecast_data)
            
            logger.info(f"Collected {len(resources)} Cost Explorer data points from {self.region_name}")
            
            summary = {
                'total_data_points': len(resources),
                'has_cost_data': bool(cost_data),
                'has_forecast': bool(forecast_data)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Cost Explorer data: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_cost_and_usage(self) -> Dict[str, Any]:
        """Collect cost and usage for last 30 days"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost', 'UsageQuantity']
            )
            
            return {
                'resource_id': 'cost-and-usage-30d',
                'resource_type': 'cost-explorer-data',
                'resource_name': 'Cost and Usage - Last 30 Days',
                'region': self.region_name,
                'time_period': f"{start_date} to {end_date}",
                'results_by_time': response.get('ResultsByTime', []),
                'tags': {}
            }
                    
        except Exception as e:
            logger.warning(f"Error collecting cost and usage: {e}")
            return {}
    
    def _collect_cost_forecast(self) -> Dict[str, Any]:
        """Collect cost forecast for next 30 days"""
        try:
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=30)
            
            response = self.client.get_cost_forecast(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metric='UNBLENDED_COST'
            )
            
            return {
                'resource_id': 'cost-forecast-30d',
                'resource_type': 'cost-explorer-forecast',
                'resource_name': 'Cost Forecast - Next 30 Days',
                'region': self.region_name,
                'time_period': f"{start_date} to {end_date}",
                'total': response.get('Total', {}),
                'forecast_results': response.get('ForecastResultsByTime', []),
                'tags': {}
            }
                    
        except Exception as e:
            logger.warning(f"Error collecting cost forecast: {e}")
            return {}
