"""
WAF Collector
Collects AWS WAF web ACLs and rules
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class WAFCollector(BaseCollector):
    """Collector for AWS WAF resources"""
    
    category = "security"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize WAF collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'waf')
        self.collector_name = 'waf'
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect WAF resources
        
        Returns:
            Dictionary containing WAF data
        """
        try:
            logger.info(f"Collecting WAF web ACLs from {self.region_name}")
            
            resources = []
            
            # Collect regional web ACLs
            regional_acls = self._collect_web_acls('REGIONAL')
            resources.extend(regional_acls)
            
            # Collect CloudFront web ACLs (only in us-east-1)
            if self.region_name == 'us-east-1':
                cloudfront_acls = self._collect_web_acls('CLOUDFRONT')
                resources.extend(cloudfront_acls)
            
            logger.info(f"Collected {len(resources)} WAF web ACLs from {self.region_name}")
            
            summary = {
                'total_web_acls': len(resources)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting WAF resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_web_acls(self, scope: str) -> List[Dict[str, Any]]:
        """Collect WAF web ACLs"""
        web_acls = []
        try:
            response = self.client.list_web_acls(Scope=scope)
            
            for acl_summary in response.get('WebACLs', []):
                acl_name = acl_summary.get('Name')
                acl_id = acl_summary.get('Id')
                
                # Get web ACL details
                try:
                    detail = self.client.get_web_acl(
                        Name=acl_name,
                        Scope=scope,
                        Id=acl_id
                    )
                    web_acl = detail.get('WebACL', {})
                    
                    web_acls.append({
                        'resource_id': acl_id,
                        'resource_type': 'waf-web-acl',
                        'resource_name': acl_name,
                        'region': self.region_name,
                        'arn': web_acl.get('ARN'),
                        'scope': scope,
                        'default_action': list(web_acl.get('DefaultAction', {}).keys())[0] if web_acl.get('DefaultAction') else 'unknown',
                        'rule_count': len(web_acl.get('Rules', [])),
                        'capacity': web_acl.get('Capacity'),
                        'managed_by_firewall_manager': web_acl.get('ManagedByFirewallManager'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting web ACL details for {acl_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting WAF web ACLs for scope {scope}: {e}")
        
        return web_acls
