"""
Migration & Transfer Collectors
AWS Migration and Transfer service collectors
"""

from .migrationhub import MigrationHubCollector
from .datasync import DataSyncCollector
from .snowball import SnowballCollector
from .transfer import TransferCollector
from .mgn import MGNCollector
from .dms import DMSCollector

__all__ = [
    'MigrationHubCollector',
    'DataSyncCollector',
    'SnowballCollector',
    'TransferCollector',
    'MGNCollector',
    'DMSCollector',
]
