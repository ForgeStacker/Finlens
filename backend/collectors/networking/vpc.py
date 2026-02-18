"""
VPC Collector
Collects VPC (Virtual Private Cloud) data from AWS
Implements standardized data collection following FinLens architecture
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class VPCCollector(BaseCollector):
    """Collects VPC information"""
    
    category = "networking"
    
    def __init__(self, profile_name: str, region_name: str):
        """
        Initialize VPC collector
        
        Args:
            profile_name: AWS profile name
            region_name: AWS region name
        """
        super().__init__(profile_name, region_name, 'ec2')  # VPC uses EC2 client
        self.collector_name = 'vpc'  # Name for logging and file naming
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect VPC data
        
        Returns:
            Standardized dictionary containing VPC data
        """
        try:
            logger.info(f"Collecting VPCs from {self.region_name}")
            
            # Collect VPCs
            vpcs = self._collect_vpcs()
            
            # Build summary
            summary = self._build_summary(vpcs)
            
            # Build response
            response = self._build_response_structure(
                resources=vpcs,
                summary=summary
            )
            
            logger.info(
                f"Collected {len(vpcs)} VPCs from {self.region_name}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error collecting VPC data: {e}")
            return self._build_response_structure(
                resources=[],
                summary={"resource_count": 0, "scan_status": "failed", "error": str(e)}
            )
    
    def _collect_vpcs(self) -> List[Dict[str, Any]]:
        """
        Collect VPCs
        
        Returns:
            List of VPC dictionaries
        """
        vpcs = []
        
        try:
            response = self.client.describe_vpcs()
            
            for vpc in response.get('Vpcs', []):
                formatted_vpc = self._format_vpc(vpc)
                
                # Enrich with additional data
                formatted_vpc['subnets'] = self._get_vpc_subnets(vpc['VpcId'])
                formatted_vpc['route_tables'] = self._get_vpc_route_tables(vpc['VpcId'])
                formatted_vpc['security_groups'] = self._get_vpc_security_groups(vpc['VpcId'])
                formatted_vpc['network_acls'] = self._get_vpc_network_acls(vpc['VpcId'])
                formatted_vpc['internet_gateways'] = self._get_vpc_internet_gateways(vpc['VpcId'])
                formatted_vpc['nat_gateways'] = self._get_vpc_nat_gateways(vpc['VpcId'])
                
                vpcs.append(formatted_vpc)
            
            logger.debug(f"Collected {len(vpcs)} VPCs")
            
        except Exception as e:
            self._handle_api_error('describe_vpcs', e)
        
        return vpcs
    
    def _format_vpc(self, vpc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format VPC data into standardized structure
        
        Args:
            vpc: Raw VPC data from boto3
            
        Returns:
            Formatted VPC dictionary
        """
        # Extract name from tags
        name = self._get_vpc_name(vpc)
        
        formatted = {
            "resource_id": vpc.get('VpcId'),
            "resource_name": name,
            "resource_type": "vpc",
            "region": self.region_name,
            "state": vpc.get('State'),
            "cidr_block": vpc.get('CidrBlock'),
            "cidr_block_association_set": [
                {
                    "cidr_block": assoc.get('CidrBlock'),
                    "state": assoc.get('CidrBlockState', {}).get('State')
                }
                for assoc in vpc.get('CidrBlockAssociationSet', [])
            ],
            "ipv6_cidr_block_association_set": [
                {
                    "ipv6_cidr_block": assoc.get('Ipv6CidrBlock'),
                    "state": assoc.get('Ipv6CidrBlockState', {}).get('State')
                }
                for assoc in vpc.get('Ipv6CidrBlockAssociationSet', [])
            ],
            "is_default": vpc.get('IsDefault', False),
            "dhcp_options_id": vpc.get('DhcpOptionsId'),
            "instance_tenancy": vpc.get('InstanceTenancy'),
            "tags": self._format_tags(vpc.get('Tags', [])),
        }
        
        return formatted
    
    def _get_vpc_name(self, vpc: Dict[str, Any]) -> str:
        """
        Extract VPC name from tags
        
        Args:
            vpc: VPC data
            
        Returns:
            VPC name or empty string
        """
        tags = vpc.get('Tags', [])
        for tag in tags:
            if tag.get('Key') == 'Name':
                return tag.get('Value', '')
        return ''
    
    def _format_tags(self, tags: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Format tags into key-value dictionary
        
        Args:
            tags: List of tag dictionaries
            
        Returns:
            Dictionary of tag key-value pairs
        """
        return {tag.get('Key', ''): tag.get('Value', '') for tag in tags}
    
    def _get_vpc_subnets(self, vpc_id: str) -> List[Dict[str, Any]]:
        """
        Get subnets for a VPC
        
        Args:
            vpc_id: VPC ID
            
        Returns:
            List of subnet information
        """
        try:
            response = self.client.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            
            subnets = []
            for subnet in response.get('Subnets', []):
                subnets.append({
                    "subnet_id": subnet.get('SubnetId'),
                    "cidr_block": subnet.get('CidrBlock'),
                    "availability_zone": subnet.get('AvailabilityZone'),
                    "available_ip_address_count": subnet.get('AvailableIpAddressCount'),
                    "state": subnet.get('State'),
                })
            
            return subnets
            
        except Exception as e:
            logger.warning(f"Could not fetch subnets for VPC {vpc_id}: {e}")
            return []
    
    def _get_vpc_route_tables(self, vpc_id: str) -> int:
        """
        Count route tables for a VPC
        
        Args:
            vpc_id: VPC ID
            
        Returns:
            Number of route tables
        """
        try:
            response = self.client.describe_route_tables(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            return len(response.get('RouteTables', []))
            
        except Exception as e:
            logger.warning(f"Could not fetch route tables for VPC {vpc_id}: {e}")
            return 0
    
    def _get_vpc_security_groups(self, vpc_id: str) -> int:
        """
        Count security groups for a VPC
        
        Args:
            vpc_id: VPC ID
            
        Returns:
            Number of security groups
        """
        try:
            response = self.client.describe_security_groups(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            return len(response.get('SecurityGroups', []))
            
        except Exception as e:
            logger.warning(f"Could not fetch security groups for VPC {vpc_id}: {e}")
            return 0
    
    def _get_vpc_network_acls(self, vpc_id: str) -> int:
        """
        Count network ACLs for a VPC
        
        Args:
            vpc_id: VPC ID
            
        Returns:
            Number of network ACLs
        """
        try:
            response = self.client.describe_network_acls(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            return len(response.get('NetworkAcls', []))
            
        except Exception as e:
            logger.warning(f"Could not fetch network ACLs for VPC {vpc_id}: {e}")
            return 0
    
    def _get_vpc_internet_gateways(self, vpc_id: str) -> int:
        """
        Count internet gateways attached to a VPC
        
        Args:
            vpc_id: VPC ID
            
        Returns:
            Number of internet gateways
        """
        try:
            response = self.client.describe_internet_gateways(
                Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
            )
            return len(response.get('InternetGateways', []))
            
        except Exception as e:
            logger.warning(f"Could not fetch internet gateways for VPC {vpc_id}: {e}")
            return 0
    
    def _get_vpc_nat_gateways(self, vpc_id: str) -> int:
        """
        Count NAT gateways in a VPC
        
        Args:
            vpc_id: VPC ID
            
        Returns:
            Number of NAT gateways
        """
        try:
            response = self.client.describe_nat_gateways(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            return len(response.get('NatGateways', []))
            
        except Exception as e:
            logger.warning(f"Could not fetch NAT gateways for VPC {vpc_id}: {e}")
            return 0
    
    def _build_summary(self, vpcs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build summary statistics for collected VPCs
        
        Args:
            vpcs: List of VPC dictionaries
            
        Returns:
            Summary dictionary
        """
        total_subnets = 0
        total_route_tables = 0
        total_security_groups = 0
        default_vpcs = 0
        
        for vpc in vpcs:
            total_subnets += len(vpc.get('subnets', []))
            total_route_tables += vpc.get('route_tables', 0)
            total_security_groups += vpc.get('security_groups', 0)
            if vpc.get('is_default'):
                default_vpcs += 1
        
        return {
            "resource_count": len(vpcs),
            "scan_status": "success",
            "default_vpcs": default_vpcs,
            "total_subnets": total_subnets,
            "total_route_tables": total_route_tables,
            "total_security_groups": total_security_groups,
        }
