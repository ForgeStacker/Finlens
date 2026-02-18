"""
SES Collector
Collects SES (Simple Email Service) configuration and identity data from AWS
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SESCollector(BaseCollector):
    """Collects SES information"""
    
    category = "integration"
    
    def __init__(self, profile_name: str, region_name: str):
        super().__init__(profile_name, region_name, 'ses')
    
    def collect(self) -> Dict[str, Any]:
        """Collect SES data"""
        try:
            logger.info(f"Collecting SES data from {self.region_name}")
            
            # Collect email identities
            identities = []
            try:
                identities_response = self.client.list_identities()
                
                for identity in identities_response.get('Identities', []):
                    try:
                        # Get verification status
                        attrs = self.client.get_identity_verification_attributes(
                            Identities=[identity]
                        )
                        
                        verification = attrs.get('VerificationAttributes', {}).get(identity, {})
                        
                        identity_data = {
                            'identity': identity,
                            'identity_type': 'Domain' if '.' in identity and '@' not in identity else 'Email',
                            'verification_status': verification.get('VerificationStatus', 'Unknown'),
                            'verification_token': verification.get('VerificationToken', ''),
                            'region': self.region_name
                        }
                        
                        identities.append(identity_data)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get attributes for identity {identity}: {str(e)}")
                        continue
            except Exception as e:
                logger.warning(f"Failed to list identities: {str(e)}")
            
            # Get sending statistics
            send_stats = {}
            try:
                stats = self.client.get_send_statistics()
                data_points = stats.get('SendDataPoints', [])
                
                if data_points:
                    total_delivery_attempts = sum(dp.get('DeliveryAttempts', 0) for dp in data_points)
                    total_bounces = sum(dp.get('Bounces', 0) for dp in data_points)
                    total_complaints = sum(dp.get('Complaints', 0) for dp in data_points)
                    total_rejects = sum(dp.get('Rejects', 0) for dp in data_points)
                    
                    send_stats = {
                        'total_delivery_attempts': total_delivery_attempts,
                        'total_bounces': total_bounces,
                        'total_complaints': total_complaints,
                        'total_rejects': total_rejects,
                        'data_points_count': len(data_points)
                    }
            except Exception as e:
                logger.warning(f"Failed to get send statistics: {str(e)}")
                send_stats = {'error': 'Unable to fetch statistics'}
            
            # Get sending quota
            quota = {}
            try:
                quota_response = self.client.get_send_quota()
                quota = {
                    'max_24_hour_send': quota_response.get('Max24HourSend', 0),
                    'max_send_rate': quota_response.get('MaxSendRate', 0),
                    'sent_last_24_hours': quota_response.get('SentLast24Hours', 0)
                }
            except Exception as e:
                logger.warning(f"Failed to get send quota: {str(e)}")
                quota = {'error': 'Unable to fetch quota'}
            
            logger.info(f"Collected {len(identities)} SES identities from {self.region_name}")
            
            return {
                'service': 'ses',
                'region': self.region_name,
                'resource_count': len(identities),
                'identities': identities,
                'send_statistics': send_stats,
                'send_quota': quota,
                'metadata': {
                    'scan_timestamp': self.scan_timestamp,
                    'collector_version': '1.0.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting SES data: {str(e)}")
            raise
