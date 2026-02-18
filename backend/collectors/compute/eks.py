"""
EKS Collector
Collects EKS cluster data from AWS
Implements standardized data collection following FinLens architecture
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EKSCollector(BaseCollector):
    """Collects EKS cluster information"""
    
    category = "compute"
    
    def __init__(self, profile_name: str, region_name: str):
        """
        Initialize EKS collector
        
        Args:
            profile_name: AWS profile name
            region_name: AWS region name
        """
        super().__init__(profile_name, region_name, 'eks')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect EKS cluster data
        
        Returns:
            Standardized dictionary containing EKS data
        """
        try:
            logger.info(f"Collecting EKS clusters from {self.region_name}")
            
            # Collect clusters
            clusters = self._collect_clusters()
            
            # Build summary
            summary = self._build_summary(clusters)
            
            # Build response
            response = self._build_response_structure(
                resources=clusters,
                summary=summary
            )
            
            logger.info(
                f"Collected {len(clusters)} EKS clusters from {self.region_name}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error collecting EKS data: {e}")
            return self._build_response_structure(
                resources=[],
                summary={"resource_count": 0, "scan_status": "failed", "error": str(e)}
            )
    
    def _collect_clusters(self) -> List[Dict[str, Any]]:
        """
        Collect EKS clusters using pagination
        
        Returns:
            List of EKS cluster dictionaries
        """
        clusters = []
        
        try:
            # Use pagination to get all clusters
            paginator = self.client.get_paginator('list_clusters')
            
            for page in paginator.paginate():
                cluster_names = page.get('clusters', [])
                
                # Get detailed information for each cluster
                for cluster_name in cluster_names:
                    try:
                        response = self.client.describe_cluster(name=cluster_name)
                        cluster_detail = response.get('cluster', {})
                        if cluster_detail:
                            formatted_cluster = self._format_cluster(cluster_detail)
                            # Add node groups information
                            formatted_cluster['node_groups'] = self._get_cluster_node_groups(cluster_name)
                            clusters.append(formatted_cluster)
                    except Exception as e:
                        logger.warning(f"Could not describe cluster {cluster_name}: {e}")
                        continue
            
            logger.debug(f"Collected {len(clusters)} EKS clusters")
            
        except Exception as e:
            self._handle_api_error('list_clusters', e)
        
        return clusters
    
    def _get_cluster_node_groups(self, cluster_name: str) -> List[Dict[str, Any]]:
        """
        Get node groups for a specific cluster
        
        Args:
            cluster_name: Name of the EKS cluster
            
        Returns:
            List of node group dictionaries
        """
        node_groups = []
        
        try:
            # Get node group names
            response = self.client.list_nodegroups(clusterName=cluster_name)
            nodegroup_names = response.get('nodegroups', [])
            
            for ng_name in nodegroup_names:
                try:
                    ng_response = self.client.describe_nodegroup(
                        clusterName=cluster_name,
                        nodegroupName=ng_name
                    )
                    ng_detail = ng_response.get('nodegroup', {})
                    if ng_detail:
                        node_groups.append(self._format_node_group(ng_detail))
                except Exception as e:
                    logger.warning(f"Could not describe node group {ng_name}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Could not list node groups for cluster {cluster_name}: {e}")
        
        return node_groups
    
    def _format_cluster(self, cluster: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format EKS cluster data into standardized structure
        
        Args:
            cluster: Raw EKS cluster data from boto3
            
        Returns:
            Formatted cluster dictionary
        """
        # Get basic information
        cluster_name = cluster.get('name', '')
        arn = cluster.get('arn', '')
        status = cluster.get('status', '').lower()
        version = cluster.get('version', '')
        
        # Get creation time
        creation_time = cluster.get('createdAt')
        if creation_time:
            creation_time = creation_time.isoformat()
        
        # Get endpoint information
        endpoint = cluster.get('endpoint', '')
        
        # Get platform version
        platform_version = cluster.get('platformVersion', '')
        
        # Get role ARN
        role_arn = cluster.get('roleArn', '')
        
        # Get network configuration
        vpc_config = cluster.get('resourcesVpcConfig', {})
        subnet_ids = vpc_config.get('subnetIds', [])
        security_group_ids = vpc_config.get('securityGroupIds', [])
        cluster_security_group_id = vpc_config.get('clusterSecurityGroupId', '')
        vpc_id = vpc_config.get('vpcId', '')
        endpoint_private_access = vpc_config.get('endpointPrivateAccess', False)
        endpoint_public_access = vpc_config.get('endpointPublicAccess', False)
        public_access_cidrs = vpc_config.get('publicAccessCidrs', [])
        
        # Get logging configuration
        logging_config = cluster.get('logging', {})
        log_setup = logging_config.get('clusterLogging', [])
        enabled_log_types = []
        for log_config in log_setup:
            if log_config.get('enabled', False):
                enabled_log_types.extend(log_config.get('types', []))
        
        # Get identity providers
        identity = cluster.get('identity', {})
        oidc_issuer = identity.get('oidc', {}).get('issuer', '') if identity.get('oidc') else ''
        
        # Get encryption configuration
        encryption_config = cluster.get('encryptionConfig', [])
        encryption_enabled = len(encryption_config) > 0
        
        # Get add-ons information (this requires additional API calls)
        addon_names = self._get_cluster_addons(cluster_name)
        
        # Get tags
        tags = cluster.get('tags', {})
        
        return {
            'resource_id': cluster_name,
            'resource_name': cluster_name,
            'resource_type': 'eks-cluster',
            'region': self.region_name,
            'arn': arn,
            'status': status,
            'version': version,
            'platform_version': platform_version,
            'created_time': creation_time,
            'endpoint': endpoint,
            'role_arn': role_arn,
            'vpc_id': vpc_id,
            'subnet_ids': subnet_ids,
            'security_group_ids': security_group_ids,
            'cluster_security_group_id': cluster_security_group_id,
            'endpoint_private_access': endpoint_private_access,
            'endpoint_public_access': endpoint_public_access,
            'public_access_cidrs': public_access_cidrs,
            'enabled_log_types': enabled_log_types,
            'oidc_issuer': oidc_issuer,
            'encryption_enabled': encryption_enabled,
            'addon_names': addon_names,
            'tags': tags
        }
    
    def _format_node_group(self, node_group: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format EKS node group data into standardized structure
        
        Args:
            node_group: Raw EKS node group data from boto3
            
        Returns:
            Formatted node group dictionary
        """
        # Get basic information
        ng_name = node_group.get('nodegroupName', '')
        arn = node_group.get('nodegroupArn', '')
        status = node_group.get('status', '').lower()
        
        # Get creation time
        creation_time = node_group.get('createdAt')
        if creation_time:
            creation_time = creation_time.isoformat()
        
        # Get instance information
        instance_types = node_group.get('instanceTypes', [])
        ami_type = node_group.get('amiType', '')
        capacity_type = node_group.get('capacityType', '')
        
        # Get scaling configuration
        scaling_config = node_group.get('scalingConfig', {})
        min_size = scaling_config.get('minSize', 0)
        max_size = scaling_config.get('maxSize', 0)
        desired_size = scaling_config.get('desiredSize', 0)
        
        # Get subnet and security configuration
        subnet_ids = node_group.get('subnets', [])
        
        # Get remote access configuration
        remote_access = node_group.get('remoteAccess', {})
        ec2_ssh_key = remote_access.get('ec2SshKey', '')
        source_security_groups = remote_access.get('sourceSecurityGroups', [])
        
        # Get node role
        node_role = node_group.get('nodeRole', '')
        
        # Get disk size
        disk_size = node_group.get('diskSize', 0)
        
        # Get health status
        health = node_group.get('health', {})
        health_issues = health.get('issues', [])
        
        # Get tags
        tags = node_group.get('tags', {})
        
        return {
            'name': ng_name,
            'arn': arn,
            'status': status,
            'created_time': creation_time,
            'instance_types': instance_types,
            'ami_type': ami_type,
            'capacity_type': capacity_type,
            'min_size': min_size,
            'max_size': max_size,
            'desired_size': desired_size,
            'subnet_ids': subnet_ids,
            'ec2_ssh_key': ec2_ssh_key,
            'source_security_groups': source_security_groups,
            'node_role': node_role,
            'disk_size_gb': disk_size,
            'health_issues': health_issues,
            'tags': tags
        }
    
    def _get_cluster_addons(self, cluster_name: str) -> List[str]:
        """
        Get add-on names for a specific cluster
        
        Args:
            cluster_name: Name of the EKS cluster
            
        Returns:
            List of add-on names
        """
        addon_names = []
        
        try:
            response = self.client.list_addons(clusterName=cluster_name)
            addon_names = response.get('addons', [])
        except Exception as e:
            logger.warning(f"Could not list addons for cluster {cluster_name}: {e}")
        
        return addon_names
    
    def _build_summary(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build summary information for EKS resources
        
        Args:
            resources: List of EKS clusters
            
        Returns:
            Summary dictionary
        """
        if not resources:
            return {
                "resource_count": 0,
                "scan_status": "success",
                "clusters": 0,
                "total_node_groups": 0,
                "cluster_versions": {},
                "total_nodes": 0
            }
        
        # Count versions
        version_counts = {}
        total_node_groups = 0
        total_nodes = 0
        
        for cluster in resources:
            version = cluster.get('version', 'unknown')
            if version in version_counts:
                version_counts[version] += 1
            else:
                version_counts[version] = 1
            
            # Count node groups and total nodes
            node_groups = cluster.get('node_groups', [])
            total_node_groups += len(node_groups)
            
            for ng in node_groups:
                total_nodes += ng.get('desired_size', 0)
        
        return {
            "resource_count": len(resources),
            "scan_status": "success",
            "clusters": len(resources),
            "total_node_groups": total_node_groups,
            "cluster_versions": version_counts,
            "total_nodes": total_nodes
        }