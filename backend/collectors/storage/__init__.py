"""
Storage Services Collectors
"""

from .s3 import S3Collector
from .ebs import EBSCollector
from .snapshot import SnapshotCollector
from .efs import EFSCollector
from .storagegateway import StorageGatewayCollector
from .ecr import ECRCollector

__all__ = [
    'S3Collector',
    'EBSCollector', 
    'SnapshotCollector',
    'EFSCollector',
    'StorageGatewayCollector',
    'ECRCollector'
]
