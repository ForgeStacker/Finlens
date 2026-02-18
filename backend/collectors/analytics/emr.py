"""
EMR Collector
Collects AWS EMR (Elastic MapReduce) clusters and configurations
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EMRCollector(BaseCollector):
    """Collector for AWS EMR resources"""
    
    category = "analytics"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize EMR collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'emr')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect EMR clusters
        
        Returns:
            Dictionary containing EMR resources
        """
        logger.info(f"Collecting emr data from {self.region_name}")
        
        try:
            clusters = self._collect_clusters()
            studios = self._collect_studios()
            
            return {
                'service': 'emr',
                'region': self.region_name,
                'account_id': self.account_id,
                'profile': self.profile_name,
                'clusters': clusters,
                'studios': studios,
                'summary': {
                    'cluster_count': len(clusters),
                    'studio_count': len(studios),
                    'active_clusters': sum(1 for c in clusters if c.get('status') in ['RUNNING', 'WAITING']),
                    'terminated_clusters': sum(1 for c in clusters if c.get('status') == 'TERMINATED')
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting emr data: {e}")
            raise
    
    def _collect_clusters(self) -> List[Dict[str, Any]]:
        """Collect EMR clusters"""
        clusters = []
        
        try:
            # List all clusters (including terminated ones from last 2 weeks)
            paginator = self.client.get_paginator('list_clusters')
            
            for page in paginator.paginate():
                for cluster_summary in page.get('Clusters', []):
                    cluster_id = cluster_summary.get('Id')
                    
                    try:
                        # Get detailed cluster information
                        response = self.client.describe_cluster(ClusterId=cluster_id)
                        cluster = response.get('Cluster', {})
                        
                        cluster_data = {
                            'cluster_id': cluster_id,
                            'name': cluster.get('Name'),
                            'status': cluster.get('Status', {}).get('State'),
                            'state_change_reason': cluster.get('Status', {}).get('StateChangeReason', {}),
                            'created': str(cluster.get('Status', {}).get('Timeline', {}).get('CreationDateTime', '')),
                            'ready': str(cluster.get('Status', {}).get('Timeline', {}).get('ReadyDateTime', '')),
                            'ended': str(cluster.get('Status', {}).get('Timeline', {}).get('EndDateTime', '')),
                            'release_label': cluster.get('ReleaseLabel'),
                            'normalized_instance_hours': cluster.get('NormalizedInstanceHours'),
                            'master_public_dns': cluster.get('MasterPublicDnsName', ''),
                            'instance_collection_type': cluster.get('InstanceCollectionType'),
                            'applications': [app.get('Name') for app in cluster.get('Applications', [])],
                            'tags': cluster.get('Tags', []),
                            'service_role': cluster.get('ServiceRole'),
                            'auto_terminate': cluster.get('AutoTerminate'),
                            'scale_down_behavior': cluster.get('ScaleDownBehavior'),
                            'visible_to_all_users': cluster.get('VisibleToAllUsers'),
                            'log_uri': cluster.get('LogUri', ''),
                            'ec2_instance_attributes': {
                                'ec2_key_name': cluster.get('Ec2InstanceAttributes', {}).get('Ec2KeyName'),
                                'ec2_subnet_id': cluster.get('Ec2InstanceAttributes', {}).get('Ec2SubnetId'),
                                'iam_instance_profile': cluster.get('Ec2InstanceAttributes', {}).get('IamInstanceProfile')
                            }
                        }
                        
                        # Get instance fleet/group details
                        try:
                            instances_response = self.client.list_instances(ClusterId=cluster_id)
                            cluster_data['instance_count'] = len(instances_response.get('Instances', []))
                            cluster_data['instances'] = [
                                {
                                    'id': inst.get('Id'),
                                    'instance_type': inst.get('InstanceType'),
                                    'instance_group_id': inst.get('InstanceGroupId'),
                                    'market': inst.get('Market'),
                                    'status': inst.get('Status', {}).get('State'),
                                    'private_ip': inst.get('PrivateIpAddress'),
                                    'public_ip': inst.get('PublicIpAddress', '')
                                }
                                for inst in instances_response.get('Instances', [])[:10]  # Limit to first 10
                            ]
                        except Exception as e:
                            logger.warning(f"Could not get instances for cluster {cluster_id}: {e}")
                            cluster_data['instance_count'] = 0
                            cluster_data['instances'] = []
                        
                        clusters.append(cluster_data)
                        
                    except Exception as e:
                        logger.warning(f"Could not get details for cluster {cluster_id}: {e}")
                        clusters.append({
                            'cluster_id': cluster_id,
                            'name': cluster_summary.get('Name'),
                            'status': cluster_summary.get('Status', {}).get('State'),
                            'error': str(e)
                        })
            
            logger.info(f"Collected {len(clusters)} EMR clusters from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing EMR clusters: {e}")
        
        return clusters
    
    def _collect_studios(self) -> List[Dict[str, Any]]:
        """Collect EMR Studios"""
        studios = []
        
        try:
            paginator = self.client.get_paginator('list_studios')
            
            for page in paginator.paginate():
                for studio_summary in page.get('Studios', []):
                    studio_id = studio_summary.get('StudioId')
                    
                    try:
                        # Get detailed studio information
                        response = self.client.describe_studio(StudioId=studio_id)
                        studio = response.get('Studio', {})
                        
                        studios.append({
                            'studio_id': studio_id,
                            'name': studio.get('Name'),
                            'description': studio.get('Description', ''),
                            'url': studio.get('Url', ''),
                            'auth_mode': studio.get('AuthMode'),
                            'vpc_id': studio.get('VpcId'),
                            'subnet_ids': studio.get('SubnetIds', []),
                            'service_role': studio.get('ServiceRole'),
                            'user_role': studio.get('UserRole'),
                            'workspace_security_group_id': studio.get('WorkspaceSecurityGroupId'),
                            'engine_security_group_id': studio.get('EngineSecurityGroupId'),
                            'default_s3_location': studio.get('DefaultS3Location', ''),
                            'creation_time': str(studio.get('CreationTime', '')),
                            'tags': studio.get('Tags', [])
                        })
                        
                    except Exception as e:
                        logger.warning(f"Could not get details for studio {studio_id}: {e}")
                        studios.append({
                            'studio_id': studio_id,
                            'name': studio_summary.get('Name'),
                            'error': str(e)
                        })
            
            logger.info(f"Collected {len(studios)} EMR Studios from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing EMR Studios: {e}")
        
        return studios
