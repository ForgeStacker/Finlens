"""
Kinesis Collector
Collects AWS Kinesis streams, Firehose delivery streams, and Analytics applications
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class KinesisCollector(BaseCollector):
    """Collector for AWS Kinesis resources"""
    
    category = "analytics"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Kinesis collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'kinesis')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Kinesis resources
        
        Returns:
            Dictionary containing Kinesis resources
        """
        logger.info(f"Collecting kinesis data from {self.region_name}")
        
        try:
            streams = self._collect_data_streams()
            firehose_streams = self._collect_firehose_streams()
            analytics_apps = self._collect_analytics_applications()
            
            return {
                'service': 'kinesis',
                'region': self.region_name,
                'account_id': self.account_id,
                'profile': self.profile_name,
                'data_streams': streams,
                'firehose_streams': firehose_streams,
                'analytics_applications': analytics_apps,
                'summary': {
                    'data_stream_count': len(streams),
                    'firehose_stream_count': len(firehose_streams),
                    'analytics_application_count': len(analytics_apps),
                    'active_streams': sum(1 for s in streams if s.get('status') == 'ACTIVE')
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting kinesis data: {e}")
            raise
    
    def _collect_data_streams(self) -> List[Dict[str, Any]]:
        """Collect Kinesis Data Streams"""
        streams = []
        
        try:
            paginator = self.client.get_paginator('list_streams')
            
            for page in paginator.paginate():
                for stream_name in page.get('StreamNames', []):
                    try:
                        # Get stream description
                        response = self.client.describe_stream(StreamName=stream_name)
                        stream_desc = response.get('StreamDescription', {})
                        
                        # Get stream summary for enhanced monitoring metrics
                        try:
                            summary_response = self.client.describe_stream_summary(StreamName=stream_name)
                            summary = summary_response.get('StreamDescriptionSummary', {})
                        except:
                            summary = {}
                        
                        streams.append({
                            'stream_name': stream_name,
                            'stream_arn': stream_desc.get('StreamARN'),
                            'status': stream_desc.get('StreamStatus'),
                            'retention_period_hours': stream_desc.get('RetentionPeriodHours'),
                            'created': str(stream_desc.get('StreamCreationTimestamp', '')),
                            'encryption_type': stream_desc.get('EncryptionType'),
                            'key_id': stream_desc.get('KeyId', ''),
                            'shard_count': len(stream_desc.get('Shards', [])),
                            'shards': [
                                {
                                    'shard_id': shard.get('ShardId'),
                                    'parent_shard_id': shard.get('ParentShardId', ''),
                                    'hash_key_range': shard.get('HashKeyRange', {}),
                                    'sequence_number_range': shard.get('SequenceNumberRange', {})
                                }
                                for shard in stream_desc.get('Shards', [])[:10]  # Limit to first 10
                            ],
                            'enhanced_monitoring': stream_desc.get('EnhancedMonitoring', []),
                            'open_shard_count': summary.get('OpenShardCount', 0),
                            'consumer_count': summary.get('ConsumerCount', 0),
                            'tags': self._get_stream_tags(stream_name)
                        })
                        
                    except Exception as e:
                        logger.warning(f"Could not get details for stream {stream_name}: {e}")
                        streams.append({
                            'stream_name': stream_name,
                            'error': str(e)
                        })
            
            logger.info(f"Collected {len(streams)} Kinesis Data Streams from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Kinesis Data Streams: {e}")
        
        return streams
    
    def _collect_firehose_streams(self) -> List[Dict[str, Any]]:
        """Collect Kinesis Firehose delivery streams"""
        firehose_streams = []
        
        try:
            # Get Firehose client
            firehose_client = self.session.client('firehose', region_name=self.region_name)
            
            # List delivery streams
            response = firehose_client.list_delivery_streams(Limit=100)
            
            for stream_name in response.get('DeliveryStreamNames', []):
                try:
                    # Get stream description
                    desc_response = firehose_client.describe_delivery_stream(
                        DeliveryStreamName=stream_name
                    )
                    stream_desc = desc_response.get('DeliveryStreamDescription', {})
                    
                    firehose_streams.append({
                        'delivery_stream_name': stream_name,
                        'delivery_stream_arn': stream_desc.get('DeliveryStreamARN'),
                        'delivery_stream_type': stream_desc.get('DeliveryStreamType'),
                        'status': stream_desc.get('DeliveryStreamStatus'),
                        'version_id': stream_desc.get('VersionId'),
                        'created': str(stream_desc.get('CreateTimestamp', '')),
                        'last_update': str(stream_desc.get('LastUpdateTimestamp', '')),
                        'source': stream_desc.get('Source', {}),
                        'destinations': [
                            {
                                'destination_id': dest.get('DestinationId'),
                                's3_destination': dest.get('S3DestinationDescription', {}).get('BucketARN', '') if dest.get('S3DestinationDescription') else '',
                                'extended_s3_destination': dest.get('ExtendedS3DestinationDescription', {}).get('BucketARN', '') if dest.get('ExtendedS3DestinationDescription') else '',
                                'redshift_destination': dest.get('RedshiftDestinationDescription', {}).get('ClusterJDBCURL', '') if dest.get('RedshiftDestinationDescription') else '',
                                'elasticsearch_destination': dest.get('ElasticsearchDestinationDescription', {}).get('DomainARN', '') if dest.get('ElasticsearchDestinationDescription') else ''
                            }
                            for dest in stream_desc.get('Destinations', [])
                        ],
                        'has_more_destinations': stream_desc.get('HasMoreDestinations', False),
                        'tags': self._get_firehose_tags(firehose_client, stream_name)
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get details for Firehose stream {stream_name}: {e}")
                    firehose_streams.append({
                        'delivery_stream_name': stream_name,
                        'error': str(e)
                    })
            
            logger.info(f"Collected {len(firehose_streams)} Kinesis Firehose streams from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Kinesis Firehose streams: {e}")
        
        return firehose_streams
    
    def _collect_analytics_applications(self) -> List[Dict[str, Any]]:
        """Collect Kinesis Data Analytics applications"""
        applications = []
        
        try:
            # Get Kinesis Analytics V2 client
            analytics_client = self.session.client('kinesisanalyticsv2', region_name=self.region_name)
            
            # List applications
            response = analytics_client.list_applications(Limit=50)
            
            for app_summary in response.get('ApplicationSummaries', []):
                app_name = app_summary.get('ApplicationName')
                
                try:
                    # Get application details
                    desc_response = analytics_client.describe_application(
                        ApplicationName=app_name
                    )
                    app_detail = desc_response.get('ApplicationDetail', {})
                    
                    applications.append({
                        'application_name': app_name,
                        'application_arn': app_detail.get('ApplicationARN'),
                        'application_status': app_detail.get('ApplicationStatus'),
                        'runtime_environment': app_detail.get('RuntimeEnvironment'),
                        'version_id': app_detail.get('ApplicationVersionId'),
                        'created': str(app_detail.get('CreateTimestamp', '')),
                        'last_update': str(app_detail.get('LastUpdateTimestamp', '')),
                        'description': app_detail.get('ApplicationDescription', ''),
                        'service_execution_role': app_detail.get('ServiceExecutionRole', ''),
                        'application_configuration_description': {
                            'sql_application': bool(app_detail.get('ApplicationConfigurationDescription', {}).get('SqlApplicationConfigurationDescription')),
                            'flink_application': bool(app_detail.get('ApplicationConfigurationDescription', {}).get('FlinkApplicationConfigurationDescription')),
                            'environment_properties': app_detail.get('ApplicationConfigurationDescription', {}).get('EnvironmentPropertyDescriptions', {})
                        }
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get details for Analytics application {app_name}: {e}")
                    applications.append({
                        'application_name': app_name,
                        'application_status': app_summary.get('ApplicationStatus'),
                        'error': str(e)
                    })
            
            logger.info(f"Collected {len(applications)} Kinesis Analytics applications from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Kinesis Analytics applications: {e}")
        
        return applications
    
    def _get_stream_tags(self, stream_name: str) -> Dict[str, str]:
        """Get tags for a Kinesis stream"""
        try:
            response = self.client.list_tags_for_stream(StreamName=stream_name)
            tags = {tag['Key']: tag['Value'] for tag in response.get('Tags', [])}
            return tags
        except Exception as e:
            logger.warning(f"Could not get tags for stream {stream_name}: {e}")
            return {}
    
    def _get_firehose_tags(self, firehose_client, stream_name: str) -> Dict[str, str]:
        """Get tags for a Firehose delivery stream"""
        try:
            response = firehose_client.list_tags_for_delivery_stream(
                DeliveryStreamName=stream_name
            )
            tags = {tag['Key']: tag['Value'] for tag in response.get('Tags', [])}
            return tags
        except Exception as e:
            logger.warning(f"Could not get tags for Firehose stream {stream_name}: {e}")
            return {}
