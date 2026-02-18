"""
Compute Services Collectors
"""

from .ec2 import EC2Collector
from .eks import EKSCollector
from .lambda_collector import LambdaCollector
from .asg import ASGCollector
from .elasticbeanstalk import ElasticBeanstalkCollector
from .ecs import ECSCollector
from .ami import AMICollector

__all__ = ['EC2Collector', 'EKSCollector', 'LambdaCollector', 'ASGCollector', 'ElasticBeanstalkCollector', 'ECSCollector', 'AMICollector']
