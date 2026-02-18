"""
Inspector Collector
Collects AWS Inspector findings and assessment runs
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class InspectorCollector(BaseCollector):
    """Collector for AWS Inspector resources"""
    
    category = "security"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Inspector collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'inspector')
        self.collector_name = 'inspector'
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Inspector resources
        
        Returns:
            Dictionary containing Inspector data
        """
        try:
            logger.info(f"Collecting Inspector findings from {self.region_name}")
            
            resources = []
            
            # Collect findings (limited to recent)
            findings = self._collect_findings()
            resources.extend(findings)
            
            logger.info(f"Collected {len(resources)} Inspector findings from {self.region_name}")
            
            summary = {
                'total_findings': len(findings),
                'severity_distribution': self._get_severity_distribution(findings)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Inspector resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_findings(self) -> List[Dict[str, Any]]:
        """Collect Inspector findings"""
        findings = []
        try:
            # List findings (limit to 100)
            response = self.client.list_findings(maxResults=100)
            
            for finding in response.get('findings', []):
                findings.append({
                    'resource_id': finding.get('findingArn'),
                    'resource_type': 'inspector-finding',
                    'resource_name': finding.get('title'),
                    'region': self.region_name,
                    'arn': finding.get('findingArn'),
                    'aws_account_id': finding.get('awsAccountId'),
                    'title': finding.get('title'),
                    'description': finding.get('description'),
                    'severity': finding.get('severity'),
                    'status': finding.get('status'),
                    'type': finding.get('type'),
                    'first_observed_at': finding.get('firstObservedAt'),
                    'last_observed_at': finding.get('lastObservedAt'),
                    'updated_at': finding.get('updatedAt'),
                    'remediation': finding.get('remediation', {}).get('recommendation', {}).get('text'),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting Inspector findings: {e}")
        
        return findings
    
    def _get_severity_distribution(self, findings: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of finding severities"""
        distribution = {}
        for finding in findings:
            severity = finding.get('severity', 'unknown')
            distribution[severity] = distribution.get(severity, 0) + 1
        return distribution
