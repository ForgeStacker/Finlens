"""
CloudWatch Collector
Collects AWS CloudWatch metrics, alarms, and log groups information
"""

import json
from typing import Dict, List, Any
from botocore.exceptions import ClientError, NoCredentialsError
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class CloudWatchCollector(BaseCollector):
    """CloudWatch service collector for monitoring metrics, alarms, and logs"""
    
    category = "monitoring_logging"
    
    def __init__(self, profile_name: str, region_name: str):
        super().__init__(profile_name, region_name, "cloudwatch")
        self.cloudwatch_client = None
        self.logs_client = None
        
    def initialize_client(self) -> bool:
        """Initialize CloudWatch clients"""
        try:
            # Use the parent class initialization which sets self.client
            if not super().initialize_client():
                return False
            self.cloudwatch_client = self.client
            
            # Create logs client separately
            from backend.utils.aws_client import get_aws_client
            self.logs_client = get_aws_client(
                "logs", self.profile_name, self.region_name
            )
            if not self.logs_client:
                logger.error("Failed to create CloudWatch Logs client")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Failed to initialize CloudWatch clients: {str(e)}")
            return False
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect CloudWatch data
        
        Returns:
            Dict containing CloudWatch information
        """
        try:
            if not self.initialize_client():
                return {"error": "Failed to initialize CloudWatch clients"}
            
            cloudwatch_data = {
                "service": "cloudwatch",
                "profile": self.profile_name,
                "region": self.region_name,
                "account_id": self.account_id,
                "scan_timestamp": self.scan_timestamp,
                "alarms": self._collect_alarms(),
                "metrics": self._collect_metrics(),
                "log_groups": self._collect_log_groups(),
                "dashboards": self._collect_dashboards(),
                "composite_alarms": self._collect_composite_alarms()
            }
            
            logger.info(f"Successfully collected CloudWatch data: "
                       f"{len(cloudwatch_data['alarms'])} alarms, "
                       f"{len(cloudwatch_data['log_groups'])} log groups, "
                       f"{len(cloudwatch_data['dashboards'])} dashboards")
            return cloudwatch_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS Client Error collecting CloudWatch data: {error_code} - {str(e)}")
            return {"error": f"AWS Client Error: {error_code}"}
        except Exception as e:
            logger.error(f"Unexpected error collecting CloudWatch data: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _collect_alarms(self) -> List[Dict[str, Any]]:
        """Collect CloudWatch alarms"""
        try:
            alarms = []
            paginator = self.cloudwatch_client.get_paginator('describe_alarms')
            
            for page in paginator.paginate():
                for alarm in page.get('MetricAlarms', []):
                    alarm_data = {
                        "alarm_name": alarm['AlarmName'],
                        "alarm_arn": alarm['AlarmArn'],
                        "alarm_description": alarm.get('AlarmDescription'),
                        "state_value": alarm['StateValue'],
                        "state_reason": alarm.get('StateReason'),
                        "state_updated_timestamp": alarm.get('StateUpdatedTimestamp').isoformat() if alarm.get('StateUpdatedTimestamp') else None,
                        "metric_name": alarm.get('MetricName'),
                        "namespace": alarm.get('Namespace'),
                        "statistic": alarm.get('Statistic'),
                        "extended_statistic": alarm.get('ExtendedStatistic'),
                        "dimensions": alarm.get('Dimensions', []),
                        "period": alarm.get('Period'),
                        "evaluation_periods": alarm.get('EvaluationPeriods'),
                        "datapoints_to_alarm": alarm.get('DatapointsToAlarm'),
                        "threshold": alarm.get('Threshold'),
                        "comparison_operator": alarm.get('ComparisonOperator'),
                        "treat_missing_data": alarm.get('TreatMissingData'),
                        "evaluate_low_sample_count_percentile": alarm.get('EvaluateLowSampleCountPercentile'),
                        "actions_enabled": alarm.get('ActionsEnabled'),
                        "ok_actions": alarm.get('OKActions', []),
                        "alarm_actions": alarm.get('AlarmActions', []),
                        "insufficient_data_actions": alarm.get('InsufficientDataActions', []),
                        "unit": alarm.get('Unit')
                    }
                    alarms.append(alarm_data)
            
            return alarms
        except ClientError as e:
            logger.error(f"Error collecting CloudWatch alarms: {str(e)}")
            return []
    
    def _collect_composite_alarms(self) -> List[Dict[str, Any]]:
        """Collect CloudWatch composite alarms"""
        try:
            composite_alarms = []
            paginator = self.cloudwatch_client.get_paginator('describe_alarms')
            
            for page in paginator.paginate():
                for alarm in page.get('CompositeAlarms', []):
                    alarm_data = {
                        "alarm_name": alarm['AlarmName'],
                        "alarm_arn": alarm['AlarmArn'],
                        "alarm_description": alarm.get('AlarmDescription'),
                        "state_value": alarm['StateValue'],
                        "state_reason": alarm.get('StateReason'),
                        "state_updated_timestamp": alarm.get('StateUpdatedTimestamp').isoformat() if alarm.get('StateUpdatedTimestamp') else None,
                        "alarm_rule": alarm.get('AlarmRule'),
                        "actions_enabled": alarm.get('ActionsEnabled'),
                        "ok_actions": alarm.get('OKActions', []),
                        "alarm_actions": alarm.get('AlarmActions', []),
                        "insufficient_data_actions": alarm.get('InsufficientDataActions', []),
                        "actions_suppressor": alarm.get('ActionsSuppressor'),
                        "actions_suppressor_wait_period": alarm.get('ActionsSuppressorWaitPeriod'),
                        "actions_suppressor_extension_period": alarm.get('ActionsSuppressorExtensionPeriod')
                    }
                    composite_alarms.append(alarm_data)
            
            return composite_alarms
        except ClientError as e:
            logger.error(f"Error collecting CloudWatch composite alarms: {str(e)}")
            return []
    
    def _collect_metrics(self) -> List[Dict[str, Any]]:
        """Collect available CloudWatch metrics (limited to avoid large responses)"""
        try:
            metrics = []
            namespaces_to_check = [
                'AWS/EC2', 'AWS/RDS', 'AWS/S3', 'AWS/Lambda', 'AWS/ELB',
                'AWS/ApplicationELB', 'AWS/NetworkELB', 'AWS/EKS', 'AWS/ECS'
            ]
            
            for namespace in namespaces_to_check:
                try:
                    paginator = self.cloudwatch_client.get_paginator('list_metrics')
                    page_count = 0
                    for page in paginator.paginate(Namespace=namespace):
                        for metric in page.get('Metrics', []):
                            metric_data = {
                                "namespace": metric['Namespace'],
                                "metric_name": metric['MetricName'],
                                "dimensions": metric.get('Dimensions', [])
                            }
                            metrics.append(metric_data)
                        
                        # Limit pages to avoid too much data
                        page_count += 1
                        if page_count >= 3:  # Limit to first 3 pages per namespace
                            break
                            
                except ClientError as e:
                    logger.warning(f"Error collecting metrics for namespace {namespace}: {str(e)}")
                    continue
            
            return metrics[:500]  # Limit to 500 metrics to avoid overwhelming data
        except ClientError as e:
            logger.error(f"Error collecting CloudWatch metrics: {str(e)}")
            return []
    
    def _collect_log_groups(self) -> List[Dict[str, Any]]:
        """Collect CloudWatch log groups"""
        try:
            log_groups = []
            paginator = self.logs_client.get_paginator('describe_log_groups')
            
            for page in paginator.paginate():
                for log_group in page.get('logGroups', []):
                    log_group_data = {
                        "log_group_name": log_group['logGroupName'],
                        "log_group_arn": log_group.get('arn'),
                        "creation_time": log_group.get('creationTime'),
                        "retention_in_days": log_group.get('retentionInDays'),
                        "metric_filter_count": log_group.get('metricFilterCount', 0),
                        "stored_bytes": log_group.get('storedBytes', 0),
                        "kms_key_id": log_group.get('kmsKeyId'),
                        "log_group_class": log_group.get('logGroupClass')
                    }
                    
                    # Get metric filters for this log group
                    log_group_data["metric_filters"] = self._get_log_group_metric_filters(log_group['logGroupName'])
                    
                    # Get log streams count (first few)
                    log_group_data["log_streams"] = self._get_log_streams_summary(log_group['logGroupName'])
                    
                    log_groups.append(log_group_data)
            
            return log_groups
        except ClientError as e:
            logger.error(f"Error collecting CloudWatch log groups: {str(e)}")
            return []
    
    def _collect_dashboards(self) -> List[Dict[str, Any]]:
        """Collect CloudWatch dashboards"""
        try:
            dashboards = []
            paginator = self.cloudwatch_client.get_paginator('list_dashboards')
            
            for page in paginator.paginate():
                for dashboard in page.get('DashboardEntries', []):
                    dashboard_data = {
                        "dashboard_name": dashboard['DashboardName'],
                        "dashboard_arn": dashboard['DashboardArn'],
                        "last_modified": dashboard.get('LastModified').isoformat() if dashboard.get('LastModified') else None,
                        "size": dashboard.get('Size')
                    }
                    
                    # Get dashboard body (configuration)
                    try:
                        response = self.cloudwatch_client.get_dashboard(DashboardName=dashboard['DashboardName'])
                        dashboard_data["dashboard_body"] = json.loads(response['DashboardBody'])
                    except (ClientError, json.JSONDecodeError) as e:
                        logger.warning(f"Could not get dashboard body for {dashboard['DashboardName']}: {str(e)}")
                        dashboard_data["dashboard_body"] = None
                    
                    dashboards.append(dashboard_data)
            
            return dashboards
        except ClientError as e:
            logger.error(f"Error collecting CloudWatch dashboards: {str(e)}")
            return []
    
    def _get_log_group_metric_filters(self, log_group_name: str) -> List[Dict[str, Any]]:
        """Get metric filters for a log group"""
        try:
            metric_filters = []
            paginator = self.logs_client.get_paginator('describe_metric_filters')
            
            for page in paginator.paginate(logGroupName=log_group_name):
                for filter_info in page.get('metricFilters', []):
                    filter_data = {
                        "filter_name": filter_info['filterName'],
                        "filter_pattern": filter_info.get('filterPattern'),
                        "metric_transformations": filter_info.get('metricTransformations', []),
                        "creation_time": filter_info.get('creationTime')
                    }
                    metric_filters.append(filter_data)
            
            return metric_filters
        except ClientError:
            return []
    
    def _get_log_streams_summary(self, log_group_name: str, limit: int = 10) -> Dict[str, Any]:
        """Get summary of log streams for a log group"""
        try:
            response = self.logs_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy='LastEventTime',
                descending=True,
                limit=limit
            )
            
            streams_info = {
                "total_streams_checked": len(response.get('logStreams', [])),
                "streams_sample": []
            }
            
            for stream in response.get('logStreams', []):
                stream_info = {
                    "stream_name": stream['logStreamName'],
                    "creation_time": stream.get('creationTime'),
                    "last_event_time": stream.get('lastEventTime'),
                    "last_ingestion_time": stream.get('lastIngestionTime'),
                    "upload_sequence_token": stream.get('uploadSequenceToken'),
                    "stored_bytes": stream.get('storedBytes', 0)
                }
                streams_info["streams_sample"].append(stream_info)
            
            return streams_info
        except ClientError:
            return {"total_streams_checked": 0, "streams_sample": []}