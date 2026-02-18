"""
ECS (Elastic Container Service) Collector for FinLens
Collects comprehensive ECS data including clusters, services, tasks, task definitions, and container insights
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class ECSCollector(BaseCollector):
    """Collector for ECS data"""
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "ecs"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for ECS data"""
        try:
            self.logger.info(f"[ECS_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Use the initialized client
            client = self.client
            self.logger.info("ECS client initialized successfully")
            
            # Collect ECS data
            self.logger.info("Collecting ecs data...")
            data = {
                "clusters": self._collect_clusters(client),
                "services": self._collect_services(client),
                "tasks": self._collect_tasks(client),
                "task_definitions": self._collect_task_definitions(client),
                "container_instances": self._collect_container_instances(client),
                "capacity_providers": self._collect_capacity_providers(client),
                "account_settings": self._collect_account_settings(client),
                "tags": self._collect_tags(client)
            }
            
            # Count total resources
            total_resources = (
                len(data["clusters"]) +
                len(data["services"]) +
                len(data["tasks"]) +
                len(data["task_definitions"]) +
                len(data["container_instances"])
            )
            
            self.logger.info(f"Collected {total_resources} ECS resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting ECS data: {str(e)}")
            return {}
    
    def _collect_clusters(self, client) -> List[Dict[str, Any]]:
        """Collect ECS Clusters"""
        try:
            clusters = []
            
            # Get cluster ARNs
            cluster_arns_response = client.list_clusters()
            cluster_arns = cluster_arns_response.get('clusterArns', [])
            
            if cluster_arns:
                # Get detailed cluster information
                clusters_response = client.describe_clusters(
                    clusters=cluster_arns,
                    include=['ATTACHMENTS', 'CONFIGURATIONS', 'SETTINGS', 'STATISTICS', 'TAGS']
                )
                
                for cluster in clusters_response.get('clusters', []):
                    cluster_data = {
                        "cluster_name": cluster.get("clusterName"),
                        "cluster_arn": cluster.get("clusterArn"),
                        "status": cluster.get("status"),
                        "running_tasks_count": cluster.get("runningTasksCount"),
                        "pending_tasks_count": cluster.get("pendingTasksCount"),
                        "active_services_count": cluster.get("activeServicesCount"),
                        "statistics": cluster.get("statistics", []),
                        "tags": cluster.get("tags", []),
                        "settings": cluster.get("settings", []),
                        "configuration": cluster.get("configuration"),
                        "capacity_providers": cluster.get("capacityProviders", []),
                        "default_capacity_provider_strategy": cluster.get("defaultCapacityProviderStrategy", []),
                        "attachments": cluster.get("attachments", []),
                        "attachments_status": cluster.get("attachmentsStatus")
                    }
                    
                    # Get services in cluster
                    try:
                        services_response = client.list_services(cluster=cluster["clusterArn"])
                        cluster_data["services_arns"] = services_response.get("serviceArns", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get services for cluster {cluster['clusterName']}: {e}")
                        cluster_data["services_arns"] = []
                    
                    # Get tasks in cluster
                    try:
                        tasks_response = client.list_tasks(cluster=cluster["clusterArn"])
                        cluster_data["tasks_arns"] = tasks_response.get("taskArns", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get tasks for cluster {cluster['clusterName']}: {e}")
                        cluster_data["tasks_arns"] = []
                    
                    # Get container instances in cluster
                    try:
                        instances_response = client.list_container_instances(cluster=cluster["clusterArn"])
                        cluster_data["container_instances_arns"] = instances_response.get("containerInstanceArns", [])
                    except Exception as e:
                        self.logger.warning(f"Could not get container instances for cluster {cluster['clusterName']}: {e}")
                        cluster_data["container_instances_arns"] = []
                    
                    clusters.append(cluster_data)
            
            return clusters
        except Exception as e:
            self.logger.warning(f"Error collecting ECS Clusters: {e}")
            return []
    
    def _collect_services(self, client) -> List[Dict[str, Any]]:
        """Collect ECS Services"""
        try:
            all_services = []
            
            # Get all clusters first
            clusters_response = client.list_clusters()
            cluster_arns = clusters_response.get('clusterArns', [])
            
            for cluster_arn in cluster_arns:
                try:
                    # Get services in cluster
                    services_response = client.list_services(cluster=cluster_arn)
                    service_arns = services_response.get('serviceArns', [])
                    
                    if service_arns:
                        # Get detailed service information
                        services_detail_response = client.describe_services(
                            cluster=cluster_arn,
                            services=service_arns
                        )
                        
                        for service in services_detail_response.get('services', []):
                            service_data = {
                                "service_name": service.get("serviceName"),
                                "service_arn": service.get("serviceArn"),
                                "cluster_arn": service.get("clusterArn"),
                                "load_balancers": service.get("loadBalancers", []),
                                "service_registries": service.get("serviceRegistries", []),
                                "status": service.get("status"),
                                "running_count": service.get("runningCount"),
                                "pending_count": service.get("pendingCount"),
                                "desired_count": service.get("desiredCount"),
                                "task_definition": service.get("taskDefinition"),
                                "deployment_configuration": service.get("deploymentConfiguration"),
                                "task_sets": service.get("taskSets", []),
                                "deployments": service.get("deployments", []),
                                "role_arn": service.get("roleArn"),
                                "events": service.get("events", []),
                                "created_at": service.get("createdAt").isoformat() if service.get("createdAt") else None,
                                "platform_version": service.get("platformVersion"),
                                "platform_family": service.get("platformFamily"),
                                "network_configuration": service.get("networkConfiguration"),
                                "health_check_grace_period_seconds": service.get("healthCheckGracePeriodSeconds"),
                                "scheduling_strategy": service.get("schedulingStrategy"),
                                "deployment_controller": service.get("deploymentController"),
                                "tags": service.get("tags", []),
                                "created_by": service.get("createdBy"),
                                "enable_ecs_managed_tags": service.get("enableECSManagedTags"),
                                "propagate_tags": service.get("propagateTags"),
                                "enable_execute_command": service.get("enableExecuteCommand"),
                                "capacity_provider_strategy": service.get("capacityProviderStrategy", []),
                                "placement_constraints": service.get("placementConstraints", []),
                                "placement_strategy": service.get("placementStrategy", [])
                            }
                            
                            # Get service events
                            try:
                                events_response = client.describe_services(
                                    cluster=cluster_arn,
                                    services=[service["serviceArn"]]
                                )
                                if events_response.get("services"):
                                    service_data["detailed_events"] = events_response["services"][0].get("events", [])
                            except Exception as e:
                                self.logger.warning(f"Could not get detailed events for service {service['serviceName']}: {e}")
                            
                            all_services.append(service_data)
                
                except Exception as e:
                    self.logger.warning(f"Could not get services for cluster {cluster_arn}: {e}")
            
            return all_services
        except Exception as e:
            self.logger.warning(f"Error collecting ECS Services: {e}")
            return []
    
    def _collect_tasks(self, client) -> List[Dict[str, Any]]:
        """Collect ECS Tasks"""
        try:
            all_tasks = []
            
            # Get all clusters first
            clusters_response = client.list_clusters()
            cluster_arns = clusters_response.get('clusterArns', [])
            
            for cluster_arn in cluster_arns:
                try:
                    # Get tasks in cluster
                    tasks_response = client.list_tasks(cluster=cluster_arn)
                    task_arns = tasks_response.get('taskArns', [])
                    
                    # Limit to avoid too much data - get only recent tasks
                    task_arns = task_arns[:50]  # Limit to 50 most recent tasks per cluster
                    
                    if task_arns:
                        # Get detailed task information
                        tasks_detail_response = client.describe_tasks(
                            cluster=cluster_arn,
                            tasks=task_arns
                        )
                        
                        for task in tasks_detail_response.get('tasks', []):
                            task_data = {
                                "task_arn": task.get("taskArn"),
                                "cluster_arn": task.get("clusterArn"),
                                "task_definition_arn": task.get("taskDefinitionArn"),
                                "container_instance_arn": task.get("containerInstanceArn"),
                                "overrides": task.get("overrides"),
                                "last_status": task.get("lastStatus"),
                                "desired_status": task.get("desiredStatus"),
                                "cpu": task.get("cpu"),
                                "memory": task.get("memory"),
                                "containers": task.get("containers", []),
                                "started_at": task.get("startedAt").isoformat() if task.get("startedAt") else None,
                                "stopped_at": task.get("stoppedAt").isoformat() if task.get("stoppedAt") else None,
                                "stopped_reason": task.get("stoppedReason"),
                                "stop_code": task.get("stopCode"),
                                "connectivity": task.get("connectivity"),
                                "connectivity_at": task.get("connectivityAt").isoformat() if task.get("connectivityAt") else None,
                                "pull_started_at": task.get("pullStartedAt").isoformat() if task.get("pullStartedAt") else None,
                                "pull_stopped_at": task.get("pullStoppedAt").isoformat() if task.get("pullStoppedAt") else None,
                                "execution_stopped_at": task.get("executionStoppedAt").isoformat() if task.get("executionStoppedAt") else None,
                                "created_at": task.get("createdAt").isoformat() if task.get("createdAt") else None,
                                "group": task.get("group"),
                                "launch_type": task.get("launchType"),
                                "platform_version": task.get("platformVersion"),
                                "platform_family": task.get("platformFamily"),
                                "attachments": task.get("attachments", []),
                                "health_status": task.get("healthStatus"),
                                "tags": task.get("tags", []),
                                "started_by": task.get("startedBy"),
                                "version": task.get("version"),
                                "stopped_reason": task.get("stoppedReason"),
                                "capacity_provider_name": task.get("capacityProviderName"),
                                "attributes": task.get("attributes", []),
                                "availability_zone": task.get("availabilityZone"),
                                "ephemeral_storage": task.get("ephemeralStorage")
                            }
                            all_tasks.append(task_data)
                
                except Exception as e:
                    self.logger.warning(f"Could not get tasks for cluster {cluster_arn}: {e}")
            
            return all_tasks
        except Exception as e:
            self.logger.warning(f"Error collecting ECS Tasks: {e}")
            return []
    
    def _collect_task_definitions(self, client) -> List[Dict[str, Any]]:
        """Collect ECS Task Definitions"""
        try:
            task_definitions = []
            
            # Get all task definition families
            families_response = client.list_task_definition_families(
                status='ALL',
                maxResults=100
            )
            
            for family in families_response.get('families', []):
                try:
                    # Get all task definition revisions for this family
                    revisions_response = client.list_task_definitions(
                        familyPrefix=family,
                        status='ALL',
                        maxResults=10  # Limit revisions to avoid too much data
                    )
                    
                    for task_def_arn in revisions_response.get('taskDefinitionArns', []):
                        try:
                            # Get detailed task definition
                            task_def_response = client.describe_task_definition(
                                taskDefinition=task_def_arn,
                                include=['TAGS']
                            )
                            
                            task_def = task_def_response.get('taskDefinition', {})
                            task_def_data = {
                                "task_definition_arn": task_def.get("taskDefinitionArn"),
                                "family": task_def.get("family"),
                                "task_role_arn": task_def.get("taskRoleArn"),
                                "execution_role_arn": task_def.get("executionRoleArn"),
                                "network_mode": task_def.get("networkMode"),
                                "revision": task_def.get("revision"),
                                "volumes": task_def.get("volumes", []),
                                "status": task_def.get("status"),
                                "requires_attributes": task_def.get("requiresAttributes", []),
                                "placement_constraints": task_def.get("placementConstraints", []),
                                "compatibilities": task_def.get("compatibilities", []),
                                "requires_compatibilities": task_def.get("requiresCompatibilities", []),
                                "cpu": task_def.get("cpu"),
                                "memory": task_def.get("memory"),
                                "inference_accelerators": task_def.get("inferenceAccelerators", []),
                                "pid_mode": task_def.get("pidMode"),
                                "ipc_mode": task_def.get("ipcMode"),
                                "proxy_configuration": task_def.get("proxyConfiguration"),
                                "registered_at": task_def.get("registeredAt").isoformat() if task_def.get("registeredAt") else None,
                                "deregistered_at": task_def.get("deregisteredAt").isoformat() if task_def.get("deregisteredAt") else None,
                                "registered_by": task_def.get("registeredBy"),
                                "ephemeral_storage": task_def.get("ephemeralStorage"),
                                "runtime_platform": task_def.get("runtimePlatform"),
                                "container_definitions": task_def.get("containerDefinitions", []),
                                "tags": task_def_response.get("tags", [])
                            }
                            task_definitions.append(task_def_data)
                            
                        except Exception as e:
                            self.logger.warning(f"Could not get task definition {task_def_arn}: {e}")
                
                except Exception as e:
                    self.logger.warning(f"Could not get task definitions for family {family}: {e}")
            
            return task_definitions
        except Exception as e:
            self.logger.warning(f"Error collecting Task Definitions: {e}")
            return []
    
    def _collect_container_instances(self, client) -> List[Dict[str, Any]]:
        """Collect ECS Container Instances"""
        try:
            all_instances = []
            
            # Get all clusters first
            clusters_response = client.list_clusters()
            cluster_arns = clusters_response.get('clusterArns', [])
            
            for cluster_arn in cluster_arns:
                try:
                    # Get container instances in cluster
                    instances_response = client.list_container_instances(cluster=cluster_arn)
                    instance_arns = instances_response.get('containerInstanceArns', [])
                    
                    if instance_arns:
                        # Get detailed container instance information
                        instances_detail_response = client.describe_container_instances(
                            cluster=cluster_arn,
                            containerInstances=instance_arns
                        )
                        
                        for instance in instances_detail_response.get('containerInstances', []):
                            instance_data = {
                                "container_instance_arn": instance.get("containerInstanceArn"),
                                "ec2_instance_id": instance.get("ec2InstanceId"),
                                "cluster_arn": cluster_arn,
                                "capacity_provider_name": instance.get("capacityProviderName"),
                                "version": instance.get("version"),
                                "version_info": instance.get("versionInfo"),
                                "remaining_resources": instance.get("remainingResources", []),
                                "registered_resources": instance.get("registeredResources", []),
                                "status": instance.get("status"),
                                "status_reason": instance.get("statusReason"),
                                "agent_connected": instance.get("agentConnected"),
                                "running_tasks_count": instance.get("runningTasksCount"),
                                "pending_tasks_count": instance.get("pendingTasksCount"),
                                "agent_update_status": instance.get("agentUpdateStatus"),
                                "attributes": instance.get("attributes", []),
                                "registered_at": instance.get("registeredAt").isoformat() if instance.get("registeredAt") else None,
                                "attachments": instance.get("attachments", []),
                                "tags": instance.get("tags", []),
                                "health_status": instance.get("healthStatus")
                            }
                            all_instances.append(instance_data)
                
                except Exception as e:
                    self.logger.warning(f"Could not get container instances for cluster {cluster_arn}: {e}")
            
            return all_instances
        except Exception as e:
            self.logger.warning(f"Error collecting Container Instances: {e}")
            return []
    
    def _collect_capacity_providers(self, client) -> List[Dict[str, Any]]:
        """Collect ECS Capacity Providers"""
        try:
            capacity_providers = []
            
            # Get all capacity providers
            providers_response = client.describe_capacity_providers()
            
            for provider in providers_response.get('capacityProviders', []):
                provider_data = {
                    "capacity_provider_arn": provider.get("capacityProviderArn"),
                    "name": provider.get("name"),
                    "status": provider.get("status"),
                    "auto_scaling_group_provider": provider.get("autoScalingGroupProvider"),
                    "update_status": provider.get("updateStatus"),
                    "update_status_reason": provider.get("updateStatusReason"),
                    "tags": provider.get("tags", [])
                }
                capacity_providers.append(provider_data)
            
            return capacity_providers
        except Exception as e:
            self.logger.warning(f"Error collecting Capacity Providers: {e}")
            return []
    
    def _collect_account_settings(self, client) -> List[Dict[str, Any]]:
        """Collect ECS Account Settings"""
        try:
            settings = []
            
            # List of setting names to check
            setting_names = [
                'serviceLongArnFormat',
                'taskLongArnFormat',
                'containerInstanceLongArnFormat',
                'awsvpcTrunking',
                'containerInsights',
                'dualStackIPv6',
                'fargateFIPSMode',
                'tagResourceAuthorization',
                'fargateTaskRetirementWaitPeriod',
                'guardDutyActivate'
            ]
            
            for setting_name in setting_names:
                try:
                    setting_response = client.list_account_settings(name=setting_name)
                    for setting in setting_response.get('settings', []):
                        setting_data = {
                            "name": setting.get("name"),
                            "value": setting.get("value"),
                            "principal_arn": setting.get("principalArn"),
                            "type": setting.get("type")
                        }
                        settings.append(setting_data)
                except Exception as e:
                    self.logger.warning(f"Could not get account setting {setting_name}: {e}")
            
            return settings
        except Exception as e:
            self.logger.warning(f"Error collecting Account Settings: {e}")
            return []
    
    def _collect_tags(self, client) -> Dict[str, List[Dict[str, Any]]]:
        """Collect Tags for ECS resources"""
        try:
            all_tags = {
                "cluster_tags": [],
                "service_tags": [],
                "task_definition_tags": []
            }
            
            # Get cluster tags
            try:
                clusters_response = client.list_clusters()
                for cluster_arn in clusters_response.get('clusterArns', []):
                    try:
                        tags_response = client.list_tags_for_resource(resourceArn=cluster_arn)
                        cluster_tags = {
                            "resource_arn": cluster_arn,
                            "tags": tags_response.get("tags", [])
                        }
                        all_tags["cluster_tags"].append(cluster_tags)
                    except Exception as e:
                        self.logger.warning(f"Could not get tags for cluster {cluster_arn}: {e}")
            except Exception as e:
                self.logger.warning(f"Error collecting cluster tags: {e}")
            
            return all_tags
        except Exception as e:
            self.logger.warning(f"Error collecting Tags: {e}")
            return {}