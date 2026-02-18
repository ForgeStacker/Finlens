"""
SQS Collector
Collects SQS queue data from AWS
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SQSCollector(BaseCollector):
    """Collects SQS queue information"""
    
    category = "integration"
    
    def __init__(self, profile_name: str, region_name: str):
        super().__init__(profile_name, region_name, 'sqs')
    
    def collect(self) -> Dict[str, Any]:
        """Collect SQS queue data"""
        try:
            logger.info(f"Collecting SQS queues from {self.region_name}")
            
            # List all queues
            response = self.client.list_queues()
            queue_urls = response.get('QueueUrls', [])
            
            queues = []
            for queue_url in queue_urls:
                try:
                    # Get queue attributes
                    attrs = self.client.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=['All']
                    )
                    
                    attributes = attrs.get('Attributes', {})
                    queue_name = queue_url.split('/')[-1]
                    
                    queue_data = {
                        'queue_name': queue_name,
                        'queue_url': queue_url,
                        'approximate_messages': attributes.get('ApproximateNumberOfMessages', '0'),
                        'approximate_messages_delayed': attributes.get('ApproximateNumberOfMessagesDelayed', '0'),
                        'approximate_messages_not_visible': attributes.get('ApproximateNumberOfMessagesNotVisible', '0'),
                        'created_timestamp': attributes.get('CreatedTimestamp'),
                        'delay_seconds': attributes.get('DelaySeconds'),
                        'message_retention_period': attributes.get('MessageRetentionPeriod'),
                        'max_message_size': attributes.get('MaximumMessageSize'),
                        'visibility_timeout': attributes.get('VisibilityTimeout'),
                        'receive_message_wait_time': attributes.get('ReceiveMessageWaitTimeSeconds'),
                        'fifo_queue': attributes.get('FifoQueue', 'false'),
                        'content_based_deduplication': attributes.get('ContentBasedDeduplication', 'false'),
                        'region': self.region_name
                    }
                    
                    queues.append(queue_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to get attributes for queue {queue_url}: {str(e)}")
                    continue
            
            logger.info(f"Collected {len(queues)} SQS queues from {self.region_name}")
            
            return {
                'service': 'sqs',
                'region': self.region_name,
                'resource_count': len(queues),
                'queues': queues,
                'metadata': {
                    'scan_timestamp': self.scan_timestamp,
                    'collector_version': '1.0.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting SQS data: {str(e)}")
            raise
