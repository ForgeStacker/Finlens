"""
OpenSearch Collector
Collects AWS OpenSearch Service (formerly Elasticsearch Service) domains
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OpenSearchCollector(BaseCollector):
    """Collector for AWS OpenSearch Service resources"""
    
    category = "analytics"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize OpenSearch collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'opensearch')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect OpenSearch domains
        
        Returns:
            Dictionary containing OpenSearch resources
        """
        logger.info(f"Collecting opensearch data from {self.region_name}")
        
        try:
            domains = self._collect_domains()
            
            return {
                'service': 'opensearch',
                'region': self.region_name,
                'account_id': self.account_id,
                'profile': self.profile_name,
                'domains': domains,
                'summary': {
                    'domain_count': len(domains),
                    'active_domains': sum(1 for d in domains if d.get('processing') == False),
                    'processing_domains': sum(1 for d in domains if d.get('processing') == True)
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting opensearch data: {e}")
            raise
    
    def _collect_domains(self) -> List[Dict[str, Any]]:
        """Collect OpenSearch domains"""
        domains = []
        
        try:
            # List all domain names
            response = self.client.list_domain_names()
            
            for domain_info in response.get('DomainNames', []):
                domain_name = domain_info.get('DomainName')
                
                try:
                    # Get detailed domain information
                    desc_response = self.client.describe_domain(DomainName=domain_name)
                    domain_status = desc_response.get('DomainStatus', {})
                    
                    domain_data = {
                        'domain_name': domain_name,
                        'domain_id': domain_status.get('DomainId'),
                        'arn': domain_status.get('ARN'),
                        'created': domain_status.get('Created', False),
                        'deleted': domain_status.get('Deleted', False),
                        'processing': domain_status.get('Processing', False),
                        'upgrade_processing': domain_status.get('UpgradeProcessing', False),
                        'engine_version': domain_status.get('EngineVersion'),
                        'endpoint': domain_status.get('Endpoint', ''),
                        'endpoints': domain_status.get('Endpoints', {}),
                        'cluster_config': {
                            'instance_type': domain_status.get('ClusterConfig', {}).get('InstanceType'),
                            'instance_count': domain_status.get('ClusterConfig', {}).get('InstanceCount'),
                            'dedicated_master_enabled': domain_status.get('ClusterConfig', {}).get('DedicatedMasterEnabled'),
                            'dedicated_master_type': domain_status.get('ClusterConfig', {}).get('DedicatedMasterType'),
                            'dedicated_master_count': domain_status.get('ClusterConfig', {}).get('DedicatedMasterCount'),
                            'zone_awareness_enabled': domain_status.get('ClusterConfig', {}).get('ZoneAwarenessEnabled'),
                            'zone_awareness_config': domain_status.get('ClusterConfig', {}).get('ZoneAwarenessConfig', {}),
                            'warm_enabled': domain_status.get('ClusterConfig', {}).get('WarmEnabled'),
                            'warm_type': domain_status.get('ClusterConfig', {}).get('WarmType'),
                            'warm_count': domain_status.get('ClusterConfig', {}).get('WarmCount')
                        },
                        'ebs_options': {
                            'ebs_enabled': domain_status.get('EBSOptions', {}).get('EBSEnabled'),
                            'volume_type': domain_status.get('EBSOptions', {}).get('VolumeType'),
                            'volume_size': domain_status.get('EBSOptions', {}).get('VolumeSize'),
                            'iops': domain_status.get('EBSOptions', {}).get('Iops')
                        },
                        'access_policies': domain_status.get('AccessPolicies', ''),
                        'snapshot_options': domain_status.get('SnapshotOptions', {}),
                        'vpc_options': {
                            'vpc_id': domain_status.get('VPCOptions', {}).get('VPCId'),
                            'subnet_ids': domain_status.get('VPCOptions', {}).get('SubnetIds', []),
                            'security_group_ids': domain_status.get('VPCOptions', {}).get('SecurityGroupIds', []),
                            'availability_zones': domain_status.get('VPCOptions', {}).get('AvailabilityZones', [])
                        },
                        'cognito_options': {
                            'enabled': domain_status.get('CognitoOptions', {}).get('Enabled'),
                            'user_pool_id': domain_status.get('CognitoOptions', {}).get('UserPoolId', ''),
                            'identity_pool_id': domain_status.get('CognitoOptions', {}).get('IdentityPoolId', '')
                        },
                        'encryption_at_rest': {
                            'enabled': domain_status.get('EncryptionAtRestOptions', {}).get('Enabled'),
                            'kms_key_id': domain_status.get('EncryptionAtRestOptions', {}).get('KmsKeyId', '')
                        },
                        'node_to_node_encryption': {
                            'enabled': domain_status.get('NodeToNodeEncryptionOptions', {}).get('Enabled')
                        },
                        'advanced_options': domain_status.get('AdvancedOptions', {}),
                        'log_publishing_options': domain_status.get('LogPublishingOptions', {}),
                        'service_software_options': {
                            'current_version': domain_status.get('ServiceSoftwareOptions', {}).get('CurrentVersion'),
                            'new_version': domain_status.get('ServiceSoftwareOptions', {}).get('NewVersion'),
                            'update_available': domain_status.get('ServiceSoftwareOptions', {}).get('UpdateAvailable'),
                            'update_status': domain_status.get('ServiceSoftwareOptions', {}).get('UpdateStatus')
                        },
                        'domain_endpoint_options': {
                            'enforce_https': domain_status.get('DomainEndpointOptions', {}).get('EnforceHTTPS'),
                            'tls_security_policy': domain_status.get('DomainEndpointOptions', {}).get('TLSSecurityPolicy'),
                            'custom_endpoint_enabled': domain_status.get('DomainEndpointOptions', {}).get('CustomEndpointEnabled'),
                            'custom_endpoint': domain_status.get('DomainEndpointOptions', {}).get('CustomEndpoint', '')
                        },
                        'advanced_security_options': {
                            'enabled': domain_status.get('AdvancedSecurityOptions', {}).get('Enabled'),
                            'internal_user_database_enabled': domain_status.get('AdvancedSecurityOptions', {}).get('InternalUserDatabaseEnabled')
                        },
                        'auto_tune_options': domain_status.get('AutoTuneOptions', {}),
                        'tags': self._get_domain_tags(domain_name)
                    }
                    
                    domains.append(domain_data)
                    
                except Exception as e:
                    logger.warning(f"Could not get details for OpenSearch domain {domain_name}: {e}")
                    domains.append({
                        'domain_name': domain_name,
                        'error': str(e)
                    })
            
            logger.info(f"Collected {len(domains)} OpenSearch domains from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing OpenSearch domains: {e}")
        
        return domains
    
    def _get_domain_tags(self, domain_name: str) -> Dict[str, str]:
        """Get tags for an OpenSearch domain"""
        try:
            # Construct ARN for the domain
            domain_arn = f"arn:aws:es:{self.region_name}:{self.account_id}:domain/{domain_name}"
            
            response = self.client.list_tags(ARN=domain_arn)
            tags = {tag['Key']: tag['Value'] for tag in response.get('TagList', [])}
            return tags
        except Exception as e:
            logger.warning(f"Could not get tags for OpenSearch domain {domain_name}: {e}")
            return {}
