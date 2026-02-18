"""
ELB (Elastic Load Balancer) Collector for FinLens
Collects comprehensive ELB data including Classic ELB, Application LB, and Network LB
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class ELBCollector(BaseCollector):
    """Collector for ELB (Classic ELB + ALB/NLB) data"""
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "elb"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for ELB data"""
        try:
            self.logger.info(f"[ELB_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Create both ELB and ELBv2 clients for comprehensive data collection
            elbv2_client = self.session.client('elbv2')
            elb_client = self.session.client('elb')
            self.logger.info("ELB clients initialized successfully")
            
            self.logger.info("Collecting elb data...")
            data = {
                "application_load_balancers": self._collect_application_load_balancers(elbv2_client),
                "network_load_balancers": self._collect_network_load_balancers(elbv2_client), 
                "gateway_load_balancers": self._collect_gateway_load_balancers(elbv2_client),
                "classic_load_balancers": self._collect_classic_load_balancers(elb_client),
                "target_groups": self._collect_target_groups(elbv2_client),
                "listeners": self._collect_listeners(elbv2_client),
                "ssl_certificates": self._collect_ssl_certificates(elbv2_client),
                "tags": self._collect_tags(elbv2_client, elb_client)
            }
            
            # Count total resources
            total_resources = (
                len(data["application_load_balancers"]) +
                len(data["network_load_balancers"]) +
                len(data["gateway_load_balancers"]) +
                len(data["classic_load_balancers"]) +
                len(data["target_groups"])
            )
            
            self.logger.info(f"Collected {total_resources} ELB resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting ELB data: {str(e)}")
            return {}
    
    def _collect_application_load_balancers(self, client) -> List[Dict[str, Any]]:
        """Collect Application Load Balancers"""
        try:
            load_balancers = []
            
            response = client.describe_load_balancers()
            for lb in response.get('LoadBalancers', []):
                if lb.get('Type') == 'application':
                    lb_data = {
                        "load_balancer_arn": lb.get("LoadBalancerArn"),
                        "load_balancer_name": lb.get("LoadBalancerName"),
                        "dns_name": lb.get("DNSName"),
                        "canonical_hosted_zone_id": lb.get("CanonicalHostedZoneId"),
                        "created_time": lb.get("CreatedTime").isoformat() if lb.get("CreatedTime") else None,
                        "scheme": lb.get("Scheme"),
                        "vpc_id": lb.get("VpcId"),
                        "state": lb.get("State"),
                        "type": lb.get("Type"),
                        "availability_zones": lb.get("AvailabilityZones", []),
                        "security_groups": lb.get("SecurityGroups", []),
                        "ip_address_type": lb.get("IpAddressType"),
                        "customer_owned_ipv4_pool": lb.get("CustomerOwnedIpv4Pool"),
                        "enable_prefix_for_ipv6_source_nat": lb.get("EnablePrefixForIpv6SourceNat")
                    }
                    
                    # Get load balancer attributes
                    try:
                        attr_response = client.describe_load_balancer_attributes(
                            LoadBalancerArn=lb["LoadBalancerArn"]
                        )
                        lb_data["attributes"] = attr_response.get("Attributes", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get attributes for ALB {lb['LoadBalancerName']}: {e}")
                        lb_data["attributes"] = []
                    
                    # Get listeners
                    try:
                        listeners_response = client.describe_listeners(
                            LoadBalancerArn=lb["LoadBalancerArn"]
                        )
                        lb_data["listeners"] = listeners_response.get("Listeners", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get listeners for ALB {lb['LoadBalancerName']}: {e}")
                        lb_data["listeners"] = []
                    
                    load_balancers.append(lb_data)
            
            return load_balancers
        except Exception as e:
            self.logger.warning(f"Error collecting Application Load Balancers: {e}")
            return []
    
    def _collect_network_load_balancers(self, client) -> List[Dict[str, Any]]:
        """Collect Network Load Balancers"""
        try:
            load_balancers = []
            
            response = client.describe_load_balancers()
            for lb in response.get('LoadBalancers', []):
                if lb.get('Type') == 'network':
                    lb_data = {
                        "load_balancer_arn": lb.get("LoadBalancerArn"),
                        "load_balancer_name": lb.get("LoadBalancerName"),
                        "dns_name": lb.get("DNSName"),
                        "canonical_hosted_zone_id": lb.get("CanonicalHostedZoneId"),
                        "created_time": lb.get("CreatedTime").isoformat() if lb.get("CreatedTime") else None,
                        "scheme": lb.get("Scheme"),
                        "vpc_id": lb.get("VpcId"),
                        "state": lb.get("State"),
                        "type": lb.get("Type"),
                        "availability_zones": lb.get("AvailabilityZones", []),
                        "ip_address_type": lb.get("IpAddressType"),
                        "customer_owned_ipv4_pool": lb.get("CustomerOwnedIpv4Pool"),
                        "enable_prefix_for_ipv6_source_nat": lb.get("EnablePrefixForIpv6SourceNat")
                    }
                    
                    # Get load balancer attributes
                    try:
                        attr_response = client.describe_load_balancer_attributes(
                            LoadBalancerArn=lb["LoadBalancerArn"]
                        )
                        lb_data["attributes"] = attr_response.get("Attributes", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get attributes for NLB {lb['LoadBalancerName']}: {e}")
                        lb_data["attributes"] = []
                    
                    # Get listeners
                    try:
                        listeners_response = client.describe_listeners(
                            LoadBalancerArn=lb["LoadBalancerArn"]
                        )
                        lb_data["listeners"] = listeners_response.get("Listeners", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get listeners for NLB {lb['LoadBalancerName']}: {e}")
                        lb_data["listeners"] = []
                    
                    load_balancers.append(lb_data)
            
            return load_balancers
        except Exception as e:
            self.logger.warning(f"Error collecting Network Load Balancers: {e}")
            return []
    
    def _collect_gateway_load_balancers(self, client) -> List[Dict[str, Any]]:
        """Collect Gateway Load Balancers"""
        try:
            load_balancers = []
            
            response = client.describe_load_balancers()
            for lb in response.get('LoadBalancers', []):
                if lb.get('Type') == 'gateway':
                    lb_data = {
                        "load_balancer_arn": lb.get("LoadBalancerArn"),
                        "load_balancer_name": lb.get("LoadBalancerName"),
                        "dns_name": lb.get("DNSName"),
                        "canonical_hosted_zone_id": lb.get("CanonicalHostedZoneId"),
                        "created_time": lb.get("CreatedTime").isoformat() if lb.get("CreatedTime") else None,
                        "scheme": lb.get("Scheme"),
                        "vpc_id": lb.get("VpcId"),
                        "state": lb.get("State"),
                        "type": lb.get("Type"),
                        "availability_zones": lb.get("AvailabilityZones", []),
                        "ip_address_type": lb.get("IpAddressType")
                    }
                    
                    # Get load balancer attributes
                    try:
                        attr_response = client.describe_load_balancer_attributes(
                            LoadBalancerArn=lb["LoadBalancerArn"]
                        )
                        lb_data["attributes"] = attr_response.get("Attributes", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get attributes for GWLB {lb['LoadBalancerName']}: {e}")
                        lb_data["attributes"] = []
                    
                    load_balancers.append(lb_data)
            
            return load_balancers
        except Exception as e:
            self.logger.warning(f"Error collecting Gateway Load Balancers: {e}")
            return []
    
    def _collect_classic_load_balancers(self, client) -> List[Dict[str, Any]]:
        """Collect Classic Load Balancers"""
        try:
            load_balancers = []
            
            response = client.describe_load_balancers()
            for lb in response.get('LoadBalancerDescriptions', []):
                lb_data = {
                    "load_balancer_name": lb.get("LoadBalancerName"),
                    "dns_name": lb.get("DNSName"),
                    "canonical_hosted_zone_name": lb.get("CanonicalHostedZoneName"),
                    "canonical_hosted_zone_name_id": lb.get("CanonicalHostedZoneNameID"),
                    "created_time": lb.get("CreatedTime").isoformat() if lb.get("CreatedTime") else None,
                    "scheme": lb.get("Scheme"),
                    "vpc_id": lb.get("VPCId"),
                    "instances": lb.get("Instances", []),
                    "health_check": lb.get("HealthCheck"),
                    "source_security_group": lb.get("SourceSecurityGroup"),
                    "security_groups": lb.get("SecurityGroups", []),
                    "subnets": lb.get("Subnets", []),
                    "availability_zones": lb.get("AvailabilityZones", []),
                    "listener_descriptions": lb.get("ListenerDescriptions", []),
                    "policies": lb.get("Policies"),
                    "backend_server_descriptions": lb.get("BackendServerDescriptions", [])
                }
                
                # Get instance health for classic ELB
                try:
                    health_response = client.describe_instance_health(
                        LoadBalancerName=lb["LoadBalancerName"]
                    )
                    lb_data["instance_health"] = health_response.get("InstanceStates", [])
                except Exception as e:
                    self.logger.warning(f"Could not get instance health for Classic ELB {lb['LoadBalancerName']}: {e}")
                    lb_data["instance_health"] = []
                
                # Get attributes for classic ELB
                try:
                    attr_response = client.describe_load_balancer_attributes(
                        LoadBalancerName=lb["LoadBalancerName"]
                    )
                    lb_data["attributes"] = attr_response.get("LoadBalancerAttributes")
                except Exception as e:
                    self.logger.warning(f"Could not get attributes for Classic ELB {lb['LoadBalancerName']}: {e}")
                    lb_data["attributes"] = {}
                
                load_balancers.append(lb_data)
            
            return load_balancers
        except Exception as e:
            self.logger.warning(f"Error collecting Classic Load Balancers: {e}")
            return []
    
    def _collect_target_groups(self, client) -> List[Dict[str, Any]]:
        """Collect Target Groups"""
        try:
            target_groups = []
            
            response = client.describe_target_groups()
            for tg in response.get('TargetGroups', []):
                tg_data = {
                    "target_group_arn": tg.get("TargetGroupArn"),
                    "target_group_name": tg.get("TargetGroupName"),
                    "protocol": tg.get("Protocol"),
                    "port": tg.get("Port"),
                    "vpc_id": tg.get("VpcId"),
                    "health_check_protocol": tg.get("HealthCheckProtocol"),
                    "health_check_port": tg.get("HealthCheckPort"),
                    "health_check_enabled": tg.get("HealthCheckEnabled"),
                    "health_check_interval_seconds": tg.get("HealthCheckIntervalSeconds"),
                    "health_check_timeout_seconds": tg.get("HealthCheckTimeoutSeconds"),
                    "healthy_threshold_count": tg.get("HealthyThresholdCount"),
                    "unhealthy_threshold_count": tg.get("UnhealthyThresholdCount"),
                    "health_check_path": tg.get("HealthCheckPath"),
                    "matcher": tg.get("Matcher"),
                    "load_balancer_arns": tg.get("LoadBalancerArns", []),
                    "target_type": tg.get("TargetType"),
                    "protocol_version": tg.get("ProtocolVersion"),
                    "ip_address_type": tg.get("IpAddressType")
                }
                
                # Get target health
                try:
                    health_response = client.describe_target_health(
                        TargetGroupArn=tg["TargetGroupArn"]
                    )
                    tg_data["target_health"] = health_response.get("TargetHealthDescriptions", [])
                except Exception as e:
                    self.logger.warning(f"Could not get target health for TG {tg['TargetGroupName']}: {e}")
                    tg_data["target_health"] = []
                
                # Get target group attributes
                try:
                    attr_response = client.describe_target_group_attributes(
                        TargetGroupArn=tg["TargetGroupArn"]
                    )
                    tg_data["attributes"] = attr_response.get("Attributes", [])
                except Exception as e:
                    self.logger.warning(f"Could not get attributes for TG {tg['TargetGroupName']}: {e}")
                    tg_data["attributes"] = []
                
                target_groups.append(tg_data)
            
            return target_groups
        except Exception as e:
            self.logger.warning(f"Error collecting Target Groups: {e}")
            return []
    
    def _collect_listeners(self, client) -> List[Dict[str, Any]]:
        """Collect All Listeners"""
        try:
            all_listeners = []
            
            # Get all load balancers first
            lb_response = client.describe_load_balancers()
            for lb in lb_response.get('LoadBalancers', []):
                try:
                    listeners_response = client.describe_listeners(
                        LoadBalancerArn=lb["LoadBalancerArn"]
                    )
                    for listener in listeners_response.get("Listeners", []):
                        listener_data = {
                            "listener_arn": listener.get("ListenerArn"),
                            "load_balancer_arn": listener.get("LoadBalancerArn"),
                            "protocol": listener.get("Protocol"),
                            "port": listener.get("Port"),
                            "ssl_policy": listener.get("SslPolicy"),
                            "certificates": listener.get("Certificates", []),
                            "default_actions": listener.get("DefaultActions", []),
                            "alpn_policy": listener.get("AlpnPolicy", []),
                            "mutual_authentication": listener.get("MutualAuthentication")
                        }
                        
                        # Get rules for this listener (only for ALB)
                        try:
                            if lb.get("Type") == "application":
                                rules_response = client.describe_rules(
                                    ListenerArn=listener["ListenerArn"]
                                )
                                listener_data["rules"] = rules_response.get("Rules", [])
                            else:
                                listener_data["rules"] = []
                        except Exception as e:
                            self.logger.warning(f"Could not get rules for listener {listener['ListenerArn']}: {e}")
                            listener_data["rules"] = []
                        
                        all_listeners.append(listener_data)
                
                except Exception as e:
                    self.logger.warning(f"Could not get listeners for LB {lb['LoadBalancerArn']}: {e}")
            
            return all_listeners
        except Exception as e:
            self.logger.warning(f"Error collecting Listeners: {e}")
            return []
    
    def _collect_ssl_certificates(self, client) -> List[Dict[str, Any]]:
        """Collect SSL Certificates used by Load Balancers"""
        try:
            certificates = []
            certificate_arns = set()
            
            # Get all load balancers and their listeners to find SSL certificates
            lb_response = client.describe_load_balancers()
            for lb in lb_response.get('LoadBalancers', []):
                try:
                    listeners_response = client.describe_listeners(
                        LoadBalancerArn=lb["LoadBalancerArn"]
                    )
                    for listener in listeners_response.get("Listeners", []):
                        for cert in listener.get("Certificates", []):
                            if cert.get("CertificateArn"):
                                certificate_arns.add(cert["CertificateArn"])
                except Exception as e:
                    self.logger.warning(f"Could not get listeners for SSL cert collection {lb['LoadBalancerArn']}: {e}")
            
            # Store certificate ARNs found
            for cert_arn in certificate_arns:
                certificates.append({
                    "certificate_arn": cert_arn,
                    "is_default": False
                })
            
            return certificates
        except Exception as e:
            self.logger.warning(f"Error collecting SSL Certificates: {e}")
            return []
    
    def _collect_tags(self, elbv2_client, elb_client) -> Dict[str, List[Dict[str, Any]]]:
        """Collect Tags for all ELB resources"""
        try:
            all_tags = {
                "load_balancer_tags": [],
                "target_group_tags": []
            }
            
            # Get ELBv2 load balancer tags
            try:
                lb_response = elbv2_client.describe_load_balancers()
                lb_arns = [lb["LoadBalancerArn"] for lb in lb_response.get("LoadBalancers", [])]
                
                if lb_arns:
                    tags_response = elbv2_client.describe_tags(ResourceArns=lb_arns)
                    for tag_desc in tags_response.get("TagDescriptions", []):
                        lb_tags = {
                            "resource_arn": tag_desc.get("ResourceArn"),
                            "tags": tag_desc.get("Tags", [])
                        }
                        all_tags["load_balancer_tags"].append(lb_tags)
            except Exception as e:
                self.logger.warning(f"Error collecting ELBv2 load balancer tags: {e}")
            
            # Get target group tags
            try:
                tg_response = elbv2_client.describe_target_groups()
                tg_arns = [tg["TargetGroupArn"] for tg in tg_response.get("TargetGroups", [])]
                
                if tg_arns:
                    tags_response = elbv2_client.describe_tags(ResourceArns=tg_arns)
                    for tag_desc in tags_response.get("TagDescriptions", []):
                        tg_tags = {
                            "resource_arn": tag_desc.get("ResourceArn"),
                            "tags": tag_desc.get("Tags", [])
                        }
                        all_tags["target_group_tags"].append(tg_tags)
            except Exception as e:
                self.logger.warning(f"Error collecting target group tags: {e}")
            
            # Get Classic ELB tags
            try:
                classic_lb_response = elb_client.describe_load_balancers()
                for lb in classic_lb_response.get("LoadBalancerDescriptions", []):
                    try:
                        tags_response = elb_client.describe_tags(
                            LoadBalancerNames=[lb["LoadBalancerName"]]
                        )
                        for tag_desc in tags_response.get("TagDescriptions", []):
                            classic_lb_tags = {
                                "resource_name": tag_desc.get("LoadBalancerName"),
                                "tags": tag_desc.get("Tags", [])
                            }
                            all_tags["load_balancer_tags"].append(classic_lb_tags)
                    except Exception as e:
                        self.logger.warning(f"Could not get tags for Classic ELB {lb['LoadBalancerName']}: {e}")
            except Exception as e:
                self.logger.warning(f"Error collecting Classic ELB tags: {e}")
            
            return all_tags
        except Exception as e:
            self.logger.warning(f"Error collecting ELB Tags: {e}")
            return {}
