"""
Analytics & Big Data Services Collectors
"""

from .athena import AthenaCollector
from .glue import GlueCollector
from .emr import EMRCollector
from .kinesis import KinesisCollector
from .opensearch import OpenSearchCollector
from .quicksight import QuickSightCollector

__all__ = [
    'AthenaCollector',
    'GlueCollector',
    'EMRCollector',
    'KinesisCollector',
    'OpenSearchCollector',
    'QuickSightCollector'
]
