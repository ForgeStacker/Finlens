"""
Elastic Beanstalk Collector for FinLens
Collects comprehensive Elastic Beanstalk data including applications, environments, versions, and configurations
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class ElasticBeanstalkCollector(BaseCollector):
    """Collector for Elastic Beanstalk data"""
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "elasticbeanstalk"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for Elastic Beanstalk data"""
        try:
            self.logger.info(f"[ELASTICBEANSTALK_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Use the initialized client
            client = self.client
            self.logger.info("ELASTICBEANSTALK client initialized successfully")
            
            # Collect Elastic Beanstalk data
            self.logger.info("Collecting elasticbeanstalk data...")
            data = {
                "applications": self._collect_applications(client),
                "environments": self._collect_environments(client),
                "application_versions": self._collect_application_versions(client),
                "configuration_templates": self._collect_configuration_templates(client),
                "platform_versions": self._collect_platform_versions(client),
                "events": self._collect_events(client),
                "tags": self._collect_tags(client),
                "account_attributes": self._collect_account_attributes(client)
            }
            
            # Count total resources
            total_resources = (
                len(data["applications"]) +
                len(data["environments"]) +
                len(data["application_versions"]) +
                len(data["configuration_templates"])
            )
            
            self.logger.info(f"Collected {total_resources} Elastic Beanstalk resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting Elastic Beanstalk data: {str(e)}")
            return {}
    
    def _collect_applications(self, client) -> List[Dict[str, Any]]:
        """Collect Elastic Beanstalk Applications"""
        try:
            applications = []
            
            response = client.describe_applications()
            for app in response.get('Applications', []):
                app_data = {
                    "application_name": app.get("ApplicationName"),
                    "application_arn": app.get("ApplicationArn"),
                    "description": app.get("Description"),
                    "date_created": app.get("DateCreated").isoformat() if app.get("DateCreated") else None,
                    "date_updated": app.get("DateUpdated").isoformat() if app.get("DateUpdated") else None,
                    "versions": app.get("Versions", []),
                    "configuration_templates": app.get("ConfigurationTemplates", []),
                    "resource_lifecycle_config": app.get("ResourceLifecycleConfig")
                }
                
                # Get application resource lifecycle configuration
                try:
                    lifecycle_response = client.describe_application_resource_lifecycle(
                        ApplicationName=app["ApplicationName"]
                    )
                    app_data["resource_lifecycle_configuration"] = lifecycle_response.get("ResourceLifecycleConfig")
                except Exception as e:
                    self.logger.warning(f"Could not get resource lifecycle for app {app['ApplicationName']}: {e}")
                
                applications.append(app_data)
            
            return applications
        except Exception as e:
            self.logger.warning(f"Error collecting Elastic Beanstalk Applications: {e}")
            return []
    
    def _collect_environments(self, client) -> List[Dict[str, Any]]:
        """Collect Elastic Beanstalk Environments"""
        try:
            environments = []
            
            response = client.describe_environments()
            for env in response.get('Environments', []):
                env_data = {
                    "environment_name": env.get("EnvironmentName"),
                    "environment_id": env.get("EnvironmentId"),
                    "environment_arn": env.get("EnvironmentArn"),
                    "application_name": env.get("ApplicationName"),
                    "version_label": env.get("VersionLabel"),
                    "solution_stack_name": env.get("SolutionStackName"),
                    "platform_arn": env.get("PlatformArn"),
                    "template_name": env.get("TemplateName"),
                    "description": env.get("Description"),
                    "endpoint_url": env.get("EndpointURL"),
                    "cname": env.get("CNAME"),
                    "date_created": env.get("DateCreated").isoformat() if env.get("DateCreated") else None,
                    "date_updated": env.get("DateUpdated").isoformat() if env.get("DateUpdated") else None,
                    "status": env.get("Status"),
                    "abort_able_operation_in_progress": env.get("AbortableOperationInProgress"),
                    "health": env.get("Health"),
                    "health_status": env.get("HealthStatus"),
                    "resources": env.get("Resources"),
                    "tier": env.get("Tier"),
                    "environment_links": env.get("EnvironmentLinks", []),
                    "environment_arn": env.get("EnvironmentArn"),
                    "operations_role": env.get("OperationsRole")
                }
                
                # Get environment configuration
                try:
                    config_response = client.describe_configuration_settings(
                        ApplicationName=env["ApplicationName"],
                        EnvironmentName=env["EnvironmentName"]
                    )
                    env_data["configuration_settings"] = config_response.get("ConfigurationSettings", [])
                except Exception as e:
                    self.logger.warning(f"Could not get configuration for env {env['EnvironmentName']}: {e}")
                    env_data["configuration_settings"] = []
                
                # Get environment resources
                try:
                    resources_response = client.describe_environment_resources(
                        EnvironmentName=env["EnvironmentName"]
                    )
                    env_data["environment_resources"] = resources_response.get("EnvironmentResources")
                except Exception as e:
                    self.logger.warning(f"Could not get resources for env {env['EnvironmentName']}: {e}")
                    env_data["environment_resources"] = {}
                
                # Get environment health
                try:
                    health_response = client.describe_environment_health(
                        EnvironmentName=env["EnvironmentName"],
                        AttributeNames=['All']
                    )
                    env_data["environment_health"] = {
                        "health_status": health_response.get("HealthStatus"),
                        "status": health_response.get("Status"),
                        "color": health_response.get("Color"),
                        "causes": health_response.get("Causes", []),
                        "application_metrics": health_response.get("ApplicationMetrics"),
                        "instances_health": health_response.get("InstancesHealth"),
                        "refreshed_at": health_response.get("RefreshedAt").isoformat() if health_response.get("RefreshedAt") else None
                    }
                except Exception as e:
                    self.logger.warning(f"Could not get health for env {env['EnvironmentName']}: {e}")
                    env_data["environment_health"] = {}
                
                # Get instances health
                try:
                    instances_response = client.describe_instances_health(
                        EnvironmentName=env["EnvironmentName"],
                        AttributeNames=['All']
                    )
                    env_data["instances_health"] = instances_response.get("InstanceHealthList", [])
                except Exception as e:
                    self.logger.warning(f"Could not get instances health for env {env['EnvironmentName']}: {e}")
                    env_data["instances_health"] = []
                
                environments.append(env_data)
            
            return environments
        except Exception as e:
            self.logger.warning(f"Error collecting Elastic Beanstalk Environments: {e}")
            return []
    
    def _collect_application_versions(self, client) -> List[Dict[str, Any]]:
        """Collect Application Versions"""
        try:
            versions = []
            
            response = client.describe_application_versions()
            for version in response.get('ApplicationVersions', []):
                version_data = {
                    "application_name": version.get("ApplicationName"),
                    "application_version_arn": version.get("ApplicationVersionArn"),
                    "version_label": version.get("VersionLabel"),
                    "description": version.get("Description"),
                    "date_created": version.get("DateCreated").isoformat() if version.get("DateCreated") else None,
                    "date_updated": version.get("DateUpdated").isoformat() if version.get("DateUpdated") else None,
                    "source_bundle": version.get("SourceBundle"),
                    "build_arn": version.get("BuildArn"),
                    "source_build_information": version.get("SourceBuildInformation"),
                    "status": version.get("Status")
                }
                versions.append(version_data)
            
            return versions
        except Exception as e:
            self.logger.warning(f"Error collecting Application Versions: {e}")
            return []
    
    def _collect_configuration_templates(self, client) -> List[Dict[str, Any]]:
        """Collect Configuration Templates"""
        try:
            templates = []
            
            # Get all applications first to list their templates
            apps_response = client.describe_applications()
            for app in apps_response.get('Applications', []):
                try:
                    templates_response = client.describe_configuration_settings(
                        ApplicationName=app["ApplicationName"]
                    )
                    for template in templates_response.get("ConfigurationSettings", []):
                        if template.get("TemplateName"):  # Only configuration templates, not environment configs
                            template_data = {
                                "application_name": template.get("ApplicationName"),
                                "template_name": template.get("TemplateName"),
                                "solution_stack_name": template.get("SolutionStackName"),
                                "platform_arn": template.get("PlatformArn"),
                                "description": template.get("Description"),
                                "environment_name": template.get("EnvironmentName"),
                                "deployment_status": template.get("DeploymentStatus"),
                                "date_created": template.get("DateCreated").isoformat() if template.get("DateCreated") else None,
                                "date_updated": template.get("DateUpdated").isoformat() if template.get("DateUpdated") else None,
                                "option_settings": template.get("OptionSettings", [])
                            }
                            templates.append(template_data)
                except Exception as e:
                    self.logger.warning(f"Could not get templates for app {app['ApplicationName']}: {e}")
            
            return templates
        except Exception as e:
            self.logger.warning(f"Error collecting Configuration Templates: {e}")
            return []
    
    def _collect_platform_versions(self, client) -> List[Dict[str, Any]]:
        """Collect Platform Versions"""
        try:
            platforms = []
            
            response = client.describe_platform_versions()
            for platform in response.get('PlatformSummaryList', []):
                platform_data = {
                    "platform_arn": platform.get("PlatformArn"),
                    "platform_owner": platform.get("PlatformOwner"),
                    "platform_status": platform.get("PlatformStatus"),
                    "platform_category": platform.get("PlatformCategory"),
                    "operating_system_name": platform.get("OperatingSystemName"),
                    "operating_system_version": platform.get("OperatingSystemVersion"),
                    "supported_tier_list": platform.get("SupportedTierList", []),
                    "supported_addon_list": platform.get("SupportedAddonList", []),
                    "platform_lifecycle_state": platform.get("PlatformLifecycleState"),
                    "platform_branch_name": platform.get("PlatformBranchName"),
                    "platform_branch_lifecycle_state": platform.get("PlatformBranchLifecycleState")
                }
                
                # Get detailed platform information
                try:
                    detail_response = client.describe_platform_versions(
                        PlatformArns=[platform["PlatformArn"]]
                    )
                    if detail_response.get("PlatformSummaryList"):
                        detail = detail_response["PlatformSummaryList"][0]
                        platform_data.update({
                            "description": detail.get("Description"),
                            "maintainer": detail.get("Maintainer"),
                            "framework_name": detail.get("FrameworkName"),
                            "framework_version": detail.get("FrameworkVersion"),
                            "programming_language_name": detail.get("ProgrammingLanguageName"),
                            "programming_language_version": detail.get("ProgrammingLanguageVersion")
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get details for platform {platform['PlatformArn']}: {e}")
                
                platforms.append(platform_data)
            
            return platforms
        except Exception as e:
            self.logger.warning(f"Error collecting Platform Versions: {e}")
            return []
    
    def _collect_events(self, client) -> List[Dict[str, Any]]:
        """Collect Recent Events"""
        try:
            events = []
            
            response = client.describe_events(
                MaxRecords=1000  # Get recent events
            )
            
            for event in response.get('Events', []):
                event_data = {
                    "event_date": event.get("EventDate").isoformat() if event.get("EventDate") else None,
                    "application_name": event.get("ApplicationName"),
                    "version_label": event.get("VersionLabel"),
                    "template_name": event.get("TemplateName"),
                    "environment_name": event.get("EnvironmentName"),
                    "platform_arn": event.get("PlatformArn"),
                    "request_id": event.get("RequestId"),
                    "severity": event.get("Severity"),
                    "message": event.get("Message")
                }
                events.append(event_data)
            
            return events
        except Exception as e:
            self.logger.warning(f"Error collecting Events: {e}")
            return []
    
    def _collect_tags(self, client) -> Dict[str, List[Dict[str, Any]]]:
        """Collect Tags for all resources"""
        try:
            all_tags = {
                "application_tags": [],
                "environment_tags": []
            }
            
            # Get application tags
            try:
                apps_response = client.describe_applications()
                for app in apps_response.get('Applications', []):
                    try:
                        tags_response = client.list_tags_for_resource(
                            ResourceArn=app["ApplicationArn"]
                        )
                        app_tags = {
                            "resource_arn": app["ApplicationArn"],
                            "resource_name": app["ApplicationName"],
                            "tags": tags_response.get("ResourceTags", [])
                        }
                        all_tags["application_tags"].append(app_tags)
                    except Exception as e:
                        self.logger.warning(f"Could not get tags for app {app['ApplicationName']}: {e}")
            except Exception as e:
                self.logger.warning(f"Error collecting application tags: {e}")
            
            # Get environment tags
            try:
                envs_response = client.describe_environments()
                for env in envs_response.get('Environments', []):
                    try:
                        tags_response = client.list_tags_for_resource(
                            ResourceArn=env["EnvironmentArn"]
                        )
                        env_tags = {
                            "resource_arn": env["EnvironmentArn"],
                            "resource_name": env["EnvironmentName"],
                            "tags": tags_response.get("ResourceTags", [])
                        }
                        all_tags["environment_tags"].append(env_tags)
                    except Exception as e:
                        self.logger.warning(f"Could not get tags for env {env['EnvironmentName']}: {e}")
            except Exception as e:
                self.logger.warning(f"Error collecting environment tags: {e}")
            
            return all_tags
        except Exception as e:
            self.logger.warning(f"Error collecting Tags: {e}")
            return {}
    
    def _collect_account_attributes(self, client) -> Dict[str, Any]:
        """Collect Account Attributes and Available Solutions"""
        try:
            attributes = {}
            
            # Get available solution stacks
            try:
                stacks_response = client.list_available_solution_stacks()
                attributes["available_solution_stacks"] = stacks_response.get("SolutionStacks", [])
                attributes["solution_stack_details"] = stacks_response.get("SolutionStackDetails", [])
            except Exception as e:
                self.logger.warning(f"Could not get solution stacks: {e}")
                attributes["available_solution_stacks"] = []
                attributes["solution_stack_details"] = []
            
            # Get platform branches
            try:
                branches_response = client.list_platform_branches()
                attributes["platform_branches"] = branches_response.get("PlatformBranchSummaryList", [])
            except Exception as e:
                self.logger.warning(f"Could not get platform branches: {e}")
                attributes["platform_branches"] = []
            
            return attributes
        except Exception as e:
            self.logger.warning(f"Error collecting Account Attributes: {e}")
            return {}