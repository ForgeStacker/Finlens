"""
Organizations Collector
Collects AWS Organizations accounts and organizational units
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OrganizationsCollector(BaseCollector):
    """Collector for AWS Organizations resources"""
    
    category = "security"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Organizations collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'organizations')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Organizations resources
        
        Returns:
            Dictionary containing Organizations data
        """
        try:
            logger.info(f"Collecting Organizations resources from {self.region_name}")
            
            resources = []
            
            # Collect accounts
            accounts = self._collect_accounts()
            resources.extend(accounts)
            
            # Collect organizational units
            ous = self._collect_organizational_units()
            resources.extend(ous)
            
            logger.info(f"Collected {len(resources)} Organizations resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'accounts': len(accounts),
                'organizational_units': len(ous)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Organizations resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_accounts(self) -> List[Dict[str, Any]]:
        """Collect AWS accounts"""
        accounts = []
        try:
            response = self.client.list_accounts()
            
            for account in response.get('Accounts', []):
                accounts.append({
                    'resource_id': account.get('Id'),
                    'resource_type': 'organizations-account',
                    'resource_name': account.get('Name'),
                    'region': self.region_name,
                    'email': account.get('Email'),
                    'status': account.get('Status'),
                    'joined_method': account.get('JoinedMethod'),
                    'joined_timestamp': account.get('JoinedTimestamp'),
                    'arn': account.get('Arn'),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting accounts: {e}")
        
        return accounts
    
    def _collect_organizational_units(self) -> List[Dict[str, Any]]:
        """Collect organizational units"""
        ous = []
        try:
            # Get root first
            roots_response = self.client.list_roots()
            
            for root in roots_response.get('Roots', []):
                root_id = root.get('Id')
                
                # List OUs under root
                ou_response = self.client.list_organizational_units_for_parent(ParentId=root_id)
                
                for ou in ou_response.get('OrganizationalUnits', []):
                    ous.append({
                        'resource_id': ou.get('Id'),
                        'resource_type': 'organizational-unit',
                        'resource_name': ou.get('Name'),
                        'region': self.region_name,
                        'arn': ou.get('Arn'),
                        'tags': {}
                    })
                    
        except Exception as e:
            logger.warning(f"Error collecting organizational units: {e}")
        
        return ous
