"""
RDS Collector
Collects RDS database instances and clusters from AWS
Implements standardized data collection following FinLens architecture
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RDSCollector(BaseCollector):
    """Collects RDS database information"""
    
    category = "database"
    
    def __init__(self, profile_name: str, region_name: str):
        """
        Initialize RDS collector
        
        Args:
            profile_name: AWS profile name
            region_name: AWS region name
        """
        super().__init__(profile_name, region_name, 'rds')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect RDS database data
        
        Returns:
            Standardized dictionary containing RDS data
        """
        try:
            logger.info(f"Collecting RDS databases from {self.region_name}")
            
            # Collect DB instances and clusters
            db_instances = self._collect_db_instances()
            db_clusters = self._collect_db_clusters()
            
            # Combine all resources
            all_resources = db_instances + db_clusters
            
            # Build summary
            summary = self._build_summary(all_resources)
            
            # Build response
            response = self._build_response_structure(
                resources=all_resources,
                summary=summary
            )
            
            logger.info(
                f"Collected {len(all_resources)} RDS resources from {self.region_name}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error collecting RDS data: {e}")
            return self._build_response_structure(
                resources=[],
                summary={"resource_count": 0, "scan_status": "failed", "error": str(e)}
            )
    
    def _collect_db_instances(self) -> List[Dict[str, Any]]:
        """
        Collect RDS database instances using pagination
        
        Returns:
            List of RDS instance dictionaries
        """
        instances = []
        
        try:
            # Use pagination to get all instances
            paginator = self.client.get_paginator('describe_db_instances')
            
            for page in paginator.paginate():
                for instance in page.get('DBInstances', []):
                    instances.append(self._format_db_instance(instance))
            
            logger.debug(f"Collected {len(instances)} RDS instances")
            
        except Exception as e:
            self._handle_api_error('describe_db_instances', e)
        
        return instances
    
    def _collect_db_clusters(self) -> List[Dict[str, Any]]:
        """
        Collect RDS database clusters using pagination
        
        Returns:
            List of RDS cluster dictionaries
        """
        clusters = []
        
        try:
            # Use pagination to get all clusters
            paginator = self.client.get_paginator('describe_db_clusters')
            
            for page in paginator.paginate():
                for cluster in page.get('DBClusters', []):
                    clusters.append(self._format_db_cluster(cluster))
            
            logger.debug(f"Collected {len(clusters)} RDS clusters")
            
        except Exception as e:
            self._handle_api_error('describe_db_clusters', e)
        
        return clusters
    
    def _format_db_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format RDS instance data into standardized structure
        
        Args:
            instance: Raw RDS instance data from boto3
            
        Returns:
            Formatted instance dictionary
        """
        # Get basic information
        instance_id = instance.get('DBInstanceIdentifier', '')
        instance_class = instance.get('DBInstanceClass', '')
        engine = instance.get('Engine', '')
        engine_version = instance.get('EngineVersion', '')
        
        # Get status and availability
        status = instance.get('DBInstanceStatus', '').lower()
        multi_az = instance.get('MultiAZ', False)
        availability_zone = instance.get('AvailabilityZone', '')
        
        # Get storage information
        allocated_storage = instance.get('AllocatedStorage', 0)
        storage_type = instance.get('StorageType', '')
        storage_encrypted = instance.get('StorageEncrypted', False)
        
        # Get network information
        vpc_id = ''
        subnet_group = instance.get('DBSubnetGroup', {})
        if subnet_group:
            vpc_id = subnet_group.get('VpcId', '')
        
        endpoint = instance.get('Endpoint', {})
        endpoint_address = endpoint.get('Address', '') if endpoint else ''
        endpoint_port = endpoint.get('Port', '') if endpoint else ''
        
        # Get security groups
        security_groups = []
        for sg in instance.get('VpcSecurityGroups', []):
            security_groups.append({
                'id': sg.get('VpcSecurityGroupId', ''),
                'status': sg.get('Status', '')
            })
        
        # Get backup information
        backup_retention_days = instance.get('BackupRetentionPeriod', 0)
        preferred_backup_window = instance.get('PreferredBackupWindow', '')
        preferred_maintenance_window = instance.get('PreferredMaintenanceWindow', '')
        
        # Get creation time
        creation_time = instance.get('InstanceCreateTime')
        if creation_time:
            creation_time = creation_time.isoformat()
        
        # Get tags
        tags = self._format_tags(instance.get('TagList', []))
        
        return {
            'resource_id': instance_id,
            'resource_name': instance_id,
            'resource_type': 'rds-instance',
            'region': self.region_name,
            'status': status,
            'engine': engine,
            'engine_version': engine_version,
            'instance_class': instance_class,
            'created_time': creation_time,
            'multi_az': multi_az,
            'availability_zone': availability_zone,
            'allocated_storage_gb': allocated_storage,
            'storage_type': storage_type,
            'storage_encrypted': storage_encrypted,
            'vpc_id': vpc_id,
            'endpoint_address': endpoint_address,
            'endpoint_port': endpoint_port,
            'security_groups': security_groups,
            'backup_retention_days': backup_retention_days,
            'preferred_backup_window': preferred_backup_window,
            'preferred_maintenance_window': preferred_maintenance_window,
            'tags': tags
        }
    
    def _format_db_cluster(self, cluster: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format RDS cluster data into standardized structure
        
        Args:
            cluster: Raw RDS cluster data from boto3
            
        Returns:
            Formatted cluster dictionary
        """
        # Get basic information
        cluster_id = cluster.get('DBClusterIdentifier', '')
        engine = cluster.get('Engine', '')
        engine_version = cluster.get('EngineVersion', '')
        
        # Get status and availability
        status = cluster.get('Status', '').lower()
        multi_az = cluster.get('MultiAZ', False)
        availability_zones = cluster.get('AvailabilityZones', [])
        
        # Get storage information
        storage_encrypted = cluster.get('StorageEncrypted', False)
        
        # Get network information
        vpc_id = cluster.get('DbClusterResourceId', '')  # This might need adjustment
        endpoint = cluster.get('Endpoint', '')
        reader_endpoint = cluster.get('ReaderEndpoint', '')
        port = cluster.get('Port', '')
        
        # Get cluster members
        cluster_members = []
        for member in cluster.get('DBClusterMembers', []):
            cluster_members.append({
                'instance_id': member.get('DBInstanceIdentifier', ''),
                'is_cluster_writer': member.get('IsClusterWriter', False),
                'promotion_tier': member.get('PromotionTier', 0)
            })
        
        # Get backup information
        backup_retention_days = cluster.get('BackupRetentionPeriod', 0)
        preferred_backup_window = cluster.get('PreferredBackupWindow', '')
        preferred_maintenance_window = cluster.get('PreferredMaintenanceWindow', '')
        
        # Get creation time
        creation_time = cluster.get('ClusterCreateTime')
        if creation_time:
            creation_time = creation_time.isoformat()
        
        # Get tags
        tags = self._format_tags(cluster.get('TagList', []))
        
        return {
            'resource_id': cluster_id,
            'resource_name': cluster_id,
            'resource_type': 'rds-cluster',
            'region': self.region_name,
            'status': status,
            'engine': engine,
            'engine_version': engine_version,
            'created_time': creation_time,
            'multi_az': multi_az,
            'availability_zones': availability_zones,
            'storage_encrypted': storage_encrypted,
            'endpoint': endpoint,
            'reader_endpoint': reader_endpoint,
            'port': port,
            'cluster_members': cluster_members,
            'backup_retention_days': backup_retention_days,
            'preferred_backup_window': preferred_backup_window,
            'preferred_maintenance_window': preferred_maintenance_window,
            'tags': tags
        }
    
    def _format_tags(self, tag_list: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Convert AWS tag list to dictionary format
        
        Args:
            tag_list: List of AWS tag dictionaries
            
        Returns:
            Dictionary mapping tag keys to values
        """
        tags = {}
        for tag in tag_list:
            key = tag.get('Key', '')
            value = tag.get('Value', '')
            if key:
                tags[key] = value
        return tags
    
    def _build_summary(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build summary information for RDS resources
        
        Args:
            resources: List of RDS resources
            
        Returns:
            Summary dictionary
        """
        if not resources:
            return {
                "resource_count": 0,
                "scan_status": "success",
                "instances": 0,
                "clusters": 0,
                "engines": {},
                "storage_total_gb": 0
            }
        
        # Count resource types
        instance_count = len([r for r in resources if r['resource_type'] == 'rds-instance'])
        cluster_count = len([r for r in resources if r['resource_type'] == 'rds-cluster'])
        
        # Count engines
        engine_counts = {}
        total_storage = 0
        
        for resource in resources:
            engine = resource.get('engine', 'unknown')
            if engine in engine_counts:
                engine_counts[engine] += 1
            else:
                engine_counts[engine] = 1
            
            # Add storage (only for instances)
            if resource['resource_type'] == 'rds-instance':
                total_storage += resource.get('allocated_storage_gb', 0)
        
        return {
            "resource_count": len(resources),
            "scan_status": "success",
            "instances": instance_count,
            "clusters": cluster_count,
            "engines": engine_counts,
            "storage_total_gb": total_storage
        }