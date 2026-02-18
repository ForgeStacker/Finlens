"""
Auto Scaling Groups (ASG) Collector for FinLens
Collects comprehensive ASG data including configurations, policies, instances, and scaling activities
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class ASGCollector(BaseCollector):
    """Collector for Auto Scaling Groups data"""
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "autoscaling"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for ASG data"""
        try:
            self.logger.info(f"[ASG_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Use the initialized client
            client = self.client
            self.logger.info("ASG client initialized successfully")
            
            # Collect ASG data
            self.logger.info("Collecting asg data...")
            data = {
                "auto_scaling_groups": self._collect_auto_scaling_groups(client),
                "launch_configurations": self._collect_launch_configurations(client),
                "launch_templates": self._collect_launch_templates(client),
                "scaling_policies": self._collect_scaling_policies(client),
                "scheduled_actions": self._collect_scheduled_actions(client),
                "lifecycle_hooks": self._collect_lifecycle_hooks(client),
                "warm_pools": self._collect_warm_pools(client),
                "notification_configurations": self._collect_notification_configurations(client),
                "tags": self._collect_asg_tags(client),
                "metrics": self._collect_metrics(client)
            }
            
            # Count total resources
            total_resources = (
                len(data["auto_scaling_groups"]) +
                len(data["launch_configurations"]) +
                len(data["scaling_policies"]) +
                len(data["scheduled_actions"]) +
                len(data["lifecycle_hooks"])
            )
            
            self.logger.info(f"Collected {total_resources} ASG resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting ASG data: {str(e)}")
            return {}
    
    def _collect_auto_scaling_groups(self, client) -> List[Dict[str, Any]]:
        """Collect Auto Scaling Groups"""
        try:
            asg_groups = []
            paginator = client.get_paginator('describe_auto_scaling_groups')
            
            for page in paginator.paginate():
                for asg in page['AutoScalingGroups']:
                    asg_data = {
                        "auto_scaling_group_name": asg.get("AutoScalingGroupName"),
                        "auto_scaling_group_arn": asg.get("AutoScalingGroupARN"),
                        "launch_configuration_name": asg.get("LaunchConfigurationName"),
                        "launch_template": asg.get("LaunchTemplate"),
                        "mixed_instances_policy": asg.get("MixedInstancesPolicy"),
                        "min_size": asg.get("MinSize"),
                        "max_size": asg.get("MaxSize"),
                        "desired_capacity": asg.get("DesiredCapacity"),
                        "predicted_capacity": asg.get("PredictedCapacity"),
                        "default_cooldown": asg.get("DefaultCooldown"),
                        "availability_zones": asg.get("AvailabilityZones", []),
                        "load_balancer_names": asg.get("LoadBalancerNames", []),
                        "target_group_arns": asg.get("TargetGroupARNs", []),
                        "health_check_type": asg.get("HealthCheckType"),
                        "health_check_grace_period": asg.get("HealthCheckGracePeriod"),
                        "instances": asg.get("Instances", []),
                        "created_time": asg.get("CreatedTime").isoformat() if asg.get("CreatedTime") else None,
                        "suspended_processes": asg.get("SuspendedProcesses", []),
                        "placement_group": asg.get("PlacementGroup"),
                        "vpc_zone_identifier": asg.get("VPCZoneIdentifier"),
                        "enabled_metrics": asg.get("EnabledMetrics", []),
                        "status": asg.get("Status"),
                        "tags": asg.get("Tags", []),
                        "termination_policies": asg.get("TerminationPolicies", []),
                        "new_instances_protected_from_scale_in": asg.get("NewInstancesProtectedFromScaleIn"),
                        "service_linked_role_arn": asg.get("ServiceLinkedRoleARN"),
                        "max_instance_lifetime": asg.get("MaxInstanceLifetime"),
                        "capacity_rebalance": asg.get("CapacityRebalance"),
                        "warm_pool_configuration": asg.get("WarmPoolConfiguration"),
                        "warm_pool_size": asg.get("WarmPoolSize"),
                        "context": asg.get("Context"),
                        "desired_capacity_type": asg.get("DesiredCapacityType"),
                        "default_instance_warmup": asg.get("DefaultInstanceWarmup"),
                        "traffic_sources": asg.get("TrafficSources", [])
                    }
                    
                    # Get scaling activities
                    try:
                        activities_response = client.describe_scaling_activities(
                            AutoScalingGroupName=asg["AutoScalingGroupName"],
                            MaxRecords=50
                        )
                        asg_data["scaling_activities"] = activities_response.get("Activities", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get scaling activities for ASG {asg['AutoScalingGroupName']}: {e}")
                        asg_data["scaling_activities"] = []
                    
                    # Get instance refresh status
                    try:
                        refresh_response = client.describe_instance_refreshes(
                            AutoScalingGroupName=asg["AutoScalingGroupName"],
                            MaxRecords=10
                        )
                        asg_data["instance_refreshes"] = refresh_response.get("InstanceRefreshes", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get instance refreshes for ASG {asg['AutoScalingGroupName']}: {e}")
                        asg_data["instance_refreshes"] = []
                    
                    asg_groups.append(asg_data)
            
            return asg_groups
        except Exception as e:
            self.logger.warning(f"Error collecting Auto Scaling Groups: {e}")
            return []
    
    def _collect_launch_configurations(self, client) -> List[Dict[str, Any]]:
        """Collect Launch Configurations"""
        try:
            launch_configs = []
            paginator = client.get_paginator('describe_launch_configurations')
            
            for page in paginator.paginate():
                for lc in page['LaunchConfigurations']:
                    config_data = {
                        "launch_configuration_name": lc.get("LaunchConfigurationName"),
                        "launch_configuration_arn": lc.get("LaunchConfigurationARN"),
                        "image_id": lc.get("ImageId"),
                        "key_name": lc.get("KeyName"),
                        "security_groups": lc.get("SecurityGroups", []),
                        "classic_link_vpc_id": lc.get("ClassicLinkVPCId"),
                        "classic_link_vpc_security_groups": lc.get("ClassicLinkVPCSecurityGroups", []),
                        "user_data": lc.get("UserData"),
                        "instance_type": lc.get("InstanceType"),
                        "kernel_id": lc.get("KernelId"),
                        "ramdisk_id": lc.get("RamdiskId"),
                        "block_device_mappings": lc.get("BlockDeviceMappings", []),
                        "instance_monitoring": lc.get("InstanceMonitoring"),
                        "spot_price": lc.get("SpotPrice"),
                        "iam_instance_profile": lc.get("IamInstanceProfile"),
                        "created_time": lc.get("CreatedTime").isoformat() if lc.get("CreatedTime") else None,
                        "ebs_optimized": lc.get("EbsOptimized"),
                        "associate_public_ip_address": lc.get("AssociatePublicIpAddress"),
                        "placement_tenancy": lc.get("PlacementTenancy"),
                        "metadata_options": lc.get("MetadataOptions")
                    }
                    launch_configs.append(config_data)
            
            return launch_configs
        except Exception as e:
            self.logger.warning(f"Error collecting Launch Configurations: {e}")
            return []
    
    def _collect_launch_templates(self, client) -> List[Dict[str, Any]]:
        """Collect Launch Templates used by ASGs"""
        try:
            # Get EC2 client for launch templates
            ec2_client = self.session.client('ec2')
            templates = []
            
            response = ec2_client.describe_launch_templates()
            for template in response.get("LaunchTemplates", []):
                template_data = {
                    "launch_template_id": template.get("LaunchTemplateId"),
                    "launch_template_name": template.get("LaunchTemplateName"),
                    "create_time": template.get("CreateTime").isoformat() if template.get("CreateTime") else None,
                    "created_by": template.get("CreatedBy"),
                    "default_version_number": template.get("DefaultVersionNumber"),
                    "latest_version_number": template.get("LatestVersionNumber"),
                    "tags": template.get("Tags", [])
                }
                
                # Get template versions
                try:
                    versions_response = ec2_client.describe_launch_template_versions(
                        LaunchTemplateId=template["LaunchTemplateId"]
                    )
                    template_data["versions"] = versions_response.get("LaunchTemplateVersions", [])
                except Exception as e:
                    self.logger.warning(f"Could not get versions for template {template['LaunchTemplateId']}: {e}")
                    template_data["versions"] = []
                
                templates.append(template_data)
            
            return templates
        except Exception as e:
            self.logger.warning(f"Error collecting Launch Templates: {e}")
            return []
    
    def _collect_scaling_policies(self, client) -> List[Dict[str, Any]]:
        """Collect Scaling Policies"""
        try:
            policies = []
            paginator = client.get_paginator('describe_policies')
            
            for page in paginator.paginate():
                for policy in page['ScalingPolicies']:
                    policy_data = {
                        "auto_scaling_group_name": policy.get("AutoScalingGroupName"),
                        "policy_name": policy.get("PolicyName"),
                        "policy_arn": policy.get("PolicyARN"),
                        "policy_type": policy.get("PolicyType"),
                        "adjustment_type": policy.get("AdjustmentType"),
                        "min_adjustment_step": policy.get("MinAdjustmentStep"),
                        "min_adjustment_magnitude": policy.get("MinAdjustmentMagnitude"),
                        "scaling_adjustment": policy.get("ScalingAdjustment"),
                        "cooldown": policy.get("Cooldown"),
                        "step_adjustments": policy.get("StepAdjustments", []),
                        "metric_type": policy.get("MetricType"),
                        "target_tracking_configuration": policy.get("TargetTrackingConfiguration"),
                        "enabled": policy.get("Enabled"),
                        "predictive_scaling_configuration": policy.get("PredictiveScalingConfiguration"),
                        "alarms": policy.get("Alarms", [])
                    }
                    policies.append(policy_data)
            
            return policies
        except Exception as e:
            self.logger.warning(f"Error collecting Scaling Policies: {e}")
            return []
    
    def _collect_scheduled_actions(self, client) -> List[Dict[str, Any]]:
        """Collect Scheduled Actions"""
        try:
            actions = []
            paginator = client.get_paginator('describe_scheduled_actions')
            
            for page in paginator.paginate():
                for action in page['ScheduledUpdateGroupActions']:
                    action_data = {
                        "auto_scaling_group_name": action.get("AutoScalingGroupName"),
                        "scheduled_action_name": action.get("ScheduledActionName"),
                        "scheduled_action_arn": action.get("ScheduledActionARN"),
                        "time": action.get("Time").isoformat() if action.get("Time") else None,
                        "start_time": action.get("StartTime").isoformat() if action.get("StartTime") else None,
                        "end_time": action.get("EndTime").isoformat() if action.get("EndTime") else None,
                        "recurrence": action.get("Recurrence"),
                        "min_size": action.get("MinSize"),
                        "max_size": action.get("MaxSize"),
                        "desired_capacity": action.get("DesiredCapacity"),
                        "time_zone": action.get("TimeZone")
                    }
                    actions.append(action_data)
            
            return actions
        except Exception as e:
            self.logger.warning(f"Error collecting Scheduled Actions: {e}")
            return []
    
    def _collect_lifecycle_hooks(self, client) -> List[Dict[str, Any]]:
        """Collect Lifecycle Hooks"""
        try:
            hooks = []
            
            # Get all ASGs first
            asg_response = client.describe_auto_scaling_groups()
            for asg in asg_response['AutoScalingGroups']:
                try:
                    hooks_response = client.describe_lifecycle_hooks(
                        AutoScalingGroupName=asg['AutoScalingGroupName']
                    )
                    for hook in hooks_response.get('LifecycleHooks', []):
                        hook_data = {
                            "lifecycle_hook_name": hook.get("LifecycleHookName"),
                            "auto_scaling_group_name": hook.get("AutoScalingGroupName"),
                            "lifecycle_transition": hook.get("LifecycleTransition"),
                            "notification_target_arn": hook.get("NotificationTargetARN"),
                            "role_arn": hook.get("RoleARN"),
                            "notification_metadata": hook.get("NotificationMetadata"),
                            "heartbeat_timeout": hook.get("HeartbeatTimeout"),
                            "global_timeout": hook.get("GlobalTimeout"),
                            "default_result": hook.get("DefaultResult")
                        }
                        hooks.append(hook_data)
                except Exception as e:
                    self.logger.warning(f"Could not get lifecycle hooks for ASG {asg['AutoScalingGroupName']}: {e}")
            
            return hooks
        except Exception as e:
            self.logger.warning(f"Error collecting Lifecycle Hooks: {e}")
            return []
    
    def _collect_warm_pools(self, client) -> List[Dict[str, Any]]:
        """Collect Warm Pools"""
        try:
            warm_pools = []
            
            # Get all ASGs first
            asg_response = client.describe_auto_scaling_groups()
            for asg in asg_response['AutoScalingGroups']:
                try:
                    wp_response = client.describe_warm_pool(
                        AutoScalingGroupName=asg['AutoScalingGroupName']
                    )
                    if 'WarmPoolConfiguration' in wp_response:
                        warm_pool_data = {
                            "auto_scaling_group_name": asg['AutoScalingGroupName'],
                            "warm_pool_configuration": wp_response['WarmPoolConfiguration'],
                            "instances": wp_response.get('Instances', [])
                        }
                        warm_pools.append(warm_pool_data)
                except client.exceptions.ResourceContentionFault:
                    # No warm pool for this ASG
                    pass
                except Exception as e:
                    self.logger.warning(f"Could not get warm pool for ASG {asg['AutoScalingGroupName']}: {e}")
            
            return warm_pools
        except Exception as e:
            self.logger.warning(f"Error collecting Warm Pools: {e}")
            return []
    
    def _collect_notification_configurations(self, client) -> List[Dict[str, Any]]:
        """Collect Notification Configurations"""
        try:
            notifications = []
            
            response = client.describe_notification_configurations()
            for notification in response.get('NotificationConfigurations', []):
                notification_data = {
                    "auto_scaling_group_name": notification.get("AutoScalingGroupName"),
                    "topic_arn": notification.get("TopicARN"),
                    "notification_type": notification.get("NotificationType")
                }
                notifications.append(notification_data)
            
            return notifications
        except Exception as e:
            self.logger.warning(f"Error collecting Notification Configurations: {e}")
            return []
    
    def _collect_asg_tags(self, client) -> List[Dict[str, Any]]:
        """Collect ASG Tags"""
        try:
            tags = []
            
            response = client.describe_tags()
            for tag in response.get('Tags', []):
                tag_data = {
                    "resource_id": tag.get("ResourceId"),
                    "resource_type": tag.get("ResourceType"),
                    "key": tag.get("Key"),
                    "value": tag.get("Value"),
                    "propagate_at_launch": tag.get("PropagateAtLaunch")
                }
                tags.append(tag_data)
            
            return tags
        except Exception as e:
            self.logger.warning(f"Error collecting ASG Tags: {e}")
            return []
    
    def _collect_metrics(self, client) -> Dict[str, Any]:
        """Collect ASG Metrics Configuration"""
        try:
            metrics_data = {
                "account_limits": {},
                "metric_collection_types": []
            }
            
            # Get account limits
            try:
                limits_response = client.describe_account_limits()
                metrics_data["account_limits"] = {
                    "max_number_of_auto_scaling_groups": limits_response.get("MaxNumberOfAutoScalingGroups"),
                    "max_number_of_launch_configurations": limits_response.get("MaxNumberOfLaunchConfigurations"),
                    "number_of_auto_scaling_groups": limits_response.get("NumberOfAutoScalingGroups"),
                    "number_of_launch_configurations": limits_response.get("NumberOfLaunchConfigurations")
                }
            except Exception as e:
                self.logger.warning(f"Could not get account limits: {e}")
            
            # Get metric collection types
            try:
                metrics_response = client.describe_metric_collection_types()
                metrics_data["metric_collection_types"] = metrics_response.get("Metrics", [])
                metrics_data["granularities"] = metrics_response.get("Granularities", [])
            except Exception as e:
                self.logger.warning(f"Could not get metric collection types: {e}")
            
            return metrics_data
        except Exception as e:
            self.logger.warning(f"Error collecting Metrics: {e}")
            return {}