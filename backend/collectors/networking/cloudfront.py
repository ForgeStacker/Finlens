"""
CloudFront Collector
Collects AWS CloudFront distributions
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CloudFrontCollector(BaseCollector):
    """Collector for AWS CloudFront resources"""
    
    category = "networking"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize CloudFront collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'cloudfront')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CloudFront resources
        
        Returns:
            Dictionary containing CloudFront data
        """
        try:
            logger.info(f"Collecting CloudFront distributions")
            
            resources = []
            
            # Collect distributions
            distributions = self._collect_distributions()
            resources.extend(distributions)
            
            logger.info(f"Collected {len(resources)} CloudFront distributions")
            
            summary = {
                'total_distributions': len(distributions),
                'enabled_distributions': sum(1 for d in distributions if d.get('enabled')),
                'disabled_distributions': sum(1 for d in distributions if not d.get('enabled'))
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting CloudFront resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_distributions(self) -> List[Dict[str, Any]]:
        """Collect CloudFront distributions"""
        distributions = []
        try:
            response = self.client.list_distributions()
            
            distribution_list = response.get('DistributionList', {})
            
            for dist_summary in distribution_list.get('Items', []):
                distributions.append({
                    'resource_id': dist_summary.get('Id'),
                    'resource_type': 'cloudfront-distribution',
                    'resource_name': dist_summary.get('DomainName'),
                    'region': 'global',
                    'distribution_id': dist_summary.get('Id'),
                    'arn': dist_summary.get('ARN'),
                    'domain_name': dist_summary.get('DomainName'),
                    'aliases': dist_summary.get('Aliases', {}).get('Items', []),
                    'enabled': dist_summary.get('Enabled'),
                    'status': dist_summary.get('Status'),
                    'last_modified_time': dist_summary.get('LastModifiedTime'),
                    'origin_domain_names': [origin.get('DomainName') for origin in dist_summary.get('Origins', {}).get('Items', [])],
                    'price_class': dist_summary.get('PriceClass'),
                    'web_acl_id': dist_summary.get('WebACLId'),
                    'http_version': dist_summary.get('HttpVersion'),
                    'is_ipv6_enabled': dist_summary.get('IsIPV6Enabled'),
                    'comment': dist_summary.get('Comment'),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting CloudFront distributions: {e}")
        
        return distributions
