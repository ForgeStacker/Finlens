"""
SNS Collector
Collects SNS topic data from AWS
"""

from typing import Dict, List, Any
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SNSCollector(BaseCollector):
    """Collects SNS topic information"""
    
    category = "integration"
    
    def __init__(self, profile_name: str, region_name: str):
        super().__init__(profile_name, region_name, 'sns')
    
    def collect(self) -> Dict[str, Any]:
        """Collect SNS topic data"""
        try:
            logger.info(f"Collecting SNS topics from {self.region_name}")
            
            topics = []
            paginator = self.client.get_paginator('list_topics')
            
            for page in paginator.paginate():
                for topic in page.get('Topics', []):
                    topic_arn = topic['TopicArn']
                    
                    try:
                        # Get topic attributes
                        attrs = self.client.get_topic_attributes(TopicArn=topic_arn)
                        attributes = attrs.get('Attributes', {})
                        
                        # Get subscriptions count
                        subs = self.client.list_subscriptions_by_topic(TopicArn=topic_arn)
                        subscriptions_count = len(subs.get('Subscriptions', []))
                        
                        topic_name = topic_arn.split(':')[-1]
                        
                        topic_data = {
                            'topic_name': topic_name,
                            'topic_arn': topic_arn,
                            'display_name': attributes.get('DisplayName', ''),
                            'subscriptions_count': subscriptions_count,
                            'owner': attributes.get('Owner'),
                            'policy': attributes.get('Policy', 'Not configured'),
                            'delivery_policy': attributes.get('DeliveryPolicy', 'Not configured'),
                            'fifo_topic': attributes.get('FifoTopic', 'false'),
                            'content_based_deduplication': attributes.get('ContentBasedDeduplication', 'false'),
                            'region': self.region_name
                        }
                        
                        topics.append(topic_data)
                        
                    except Exception as e:
                        logger.warning(f"Failed to get attributes for topic {topic_arn}: {str(e)}")
                        continue
            
            logger.info(f"Collected {len(topics)} SNS topics from {self.region_name}")
            
            return {
                'service': 'sns',
                'region': self.region_name,
                'resource_count': len(topics),
                'topics': topics,
                'metadata': {
                    'scan_timestamp': self.scan_timestamp,
                    'collector_version': '1.0.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting SNS data: {str(e)}")
            raise
