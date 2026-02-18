"""
ACM Collector
Collects AWS Certificate Manager certificates
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ACMCollector(BaseCollector):
    """Collector for AWS Certificate Manager resources"""
    
    category = "security"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize ACM collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'acm')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect ACM resources
        
        Returns:
            Dictionary containing ACM data
        """
        try:
            logger.info(f"Collecting ACM certificates from {self.region_name}")
            
            resources = []
            
            # Collect certificates
            certificates = self._collect_certificates()
            resources.extend(certificates)
            
            logger.info(f"Collected {len(resources)} certificates from {self.region_name}")
            
            summary = {
                'total_certificates': len(certificates),
                'status_distribution': self._get_status_distribution(certificates)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting ACM resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_certificates(self) -> List[Dict[str, Any]]:
        """Collect ACM certificates"""
        certificates = []
        try:
            response = self.client.list_certificates()
            
            for cert_summary in response.get('CertificateSummaryList', []):
                cert_arn = cert_summary.get('CertificateArn')
                
                # Get certificate details
                try:
                    cert_detail = self.client.describe_certificate(CertificateArn=cert_arn)
                    cert = cert_detail.get('Certificate', {})
                    
                    certificates.append({
                        'resource_id': cert_arn,
                        'resource_type': 'acm-certificate',
                        'resource_name': cert.get('DomainName'),
                        'region': self.region_name,
                        'arn': cert_arn,
                        'domain_name': cert.get('DomainName'),
                        'subject_alternative_names': cert.get('SubjectAlternativeNames', []),
                        'status': cert.get('Status'),
                        'type': cert.get('Type'),
                        'in_use_by': cert.get('InUseBy', []),
                        'issued_at': cert.get('IssuedAt'),
                        'not_before': cert.get('NotBefore'),
                        'not_after': cert.get('NotAfter'),
                        'key_algorithm': cert.get('KeyAlgorithm'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting certificate details for {cert_arn}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting ACM certificates: {e}")
        
        return certificates
    
    def _get_status_distribution(self, certificates: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of certificate statuses"""
        distribution = {}
        for cert in certificates:
            status = cert.get('status', 'unknown')
            distribution[status] = distribution.get(status, 0) + 1
        return distribution
