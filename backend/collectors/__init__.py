"""
Collectors package - AWS service data collectors organized by category
"""

from backend.collectors.base import BaseCollector

from backend.collectors.compute import EC2Collector, EKSCollector
from backend.collectors.compute.lambda_collector import LambdaCollector
from backend.collectors.compute.asg import ASGCollector
from backend.collectors.compute.ecs import ECSCollector
from backend.collectors.compute.elasticbeanstalk import ElasticBeanstalkCollector
from backend.collectors.compute.ami import AMICollector
from backend.collectors.networking import VPCCollector
from backend.collectors.networking.elb import ELBCollector
from backend.collectors.networking.elasticip import ElasticIPCollector
from backend.collectors.networking.route53 import Route53Collector
from backend.collectors.networking.cloudfront import CloudFrontCollector
from backend.collectors.networking.vpcpeering import VPCPeeringCollector
from backend.collectors.database import RDSCollector, DynamoDBCollector, ElastiCacheCollector, RedshiftCollector, NeptuneCollector, DocumentDBCollector
from backend.collectors.storage import S3Collector, EBSCollector, SnapshotCollector
from backend.collectors.storage.efs import EFSCollector
from backend.collectors.storage.storagegateway import StorageGatewayCollector
from backend.collectors.storage.ecr import ECRCollector
from backend.collectors.security import (
    IAMCollector,
    OrganizationsCollector,
    KMSCollector,
    SecretsManagerCollector,
    ACMCollector,
    WAFCollector,
    ShieldCollector,
    GuardDutyCollector,
    InspectorCollector
)
from backend.collectors.monitoring_logging import CloudWatchCollector
from backend.collectors.analytics import (
    AthenaCollector,
    GlueCollector,
    EMRCollector,
    KinesisCollector,
    OpenSearchCollector,
    QuickSightCollector
)
from backend.collectors.integration import (
    SQSCollector,
    SNSCollector,
    EventBridgeCollector,
    StepFunctionsCollector,
    APIGatewayCollector,
    SESCollector
)
from backend.collectors.ai_ml import (
    ComprehendCollector,
    LexCollector,
    PollyCollector,
    TextractCollector,
    SageMakerCollector,
    RekognitionCollector
)
from backend.collectors.migration_transfer import (
    MigrationHubCollector,
    DataSyncCollector,
    SnowballCollector,
    TransferCollector,
    MGNCollector,
    DMSCollector
)
from backend.collectors.devops_tools import (
    CodeCommitCollector,
    CodeBuildCollector,
    CodeDeployCollector,
    CodePipelineCollector,
    CloudFormationCollector
)
from backend.collectors.management_governance import (
    CloudTrailCollector,
    ConfigCollector,
    SSMCollector,
    ControlTowerCollector,
    ServiceCatalogCollector
)
from backend.collectors.cost_management import (
    CostExplorerCollector,
    BudgetsCollector,
    CURCollector,
    SavingsPlansCollector,
    ReservedInstancesCollector,
    ComputeOptimizerCollector
)

__all__ = [
    'BaseCollector',
    # Compute
    'EC2Collector',
    'EKSCollector',
    'LambdaCollector',
    'ASGCollector',
    'ECSCollector', 
    'ElasticBeanstalkCollector',
    'AMICollector',
    # Networking
    'VPCCollector',
    'ELBCollector',
    'ElasticIPCollector',
    'Route53Collector',
    'CloudFrontCollector',
    'VPCPeeringCollector',
    # Database
    'RDSCollector',
    'DynamoDBCollector',
    'ElastiCacheCollector',
    'RedshiftCollector',
    'NeptuneCollector',
    'DocumentDBCollector',
    # Storage
    'S3Collector',
    'EBSCollector',
    'SnapshotCollector',
    'EFSCollector',
    'StorageGatewayCollector',
    'ECRCollector',
    # Security
    'IAMCollector',
    'OrganizationsCollector',
    'KMSCollector',
    'SecretsManagerCollector',
    'ACMCollector',
    'WAFCollector',
    'ShieldCollector',
    'GuardDutyCollector',
    'InspectorCollector',
    # Monitoring
    'CloudWatchCollector',
    # Analytics
    'AthenaCollector',
    'GlueCollector',
    'EMRCollector',
    'KinesisCollector',
    'OpenSearchCollector',
    'QuickSightCollector',
    # Integration
    'SQSCollector',
    'SNSCollector',
    'EventBridgeCollector',
    'StepFunctionsCollector',
    'APIGatewayCollector',
    'SESCollector',
    # AI & ML
    'ComprehendCollector',
    'LexCollector',
    'PollyCollector',
    'TextractCollector',
    'SageMakerCollector',
    'RekognitionCollector',
    # Migration & Transfer
    'MigrationHubCollector',
    'DataSyncCollector',
    'SnowballCollector',
    'TransferCollector',
    'MGNCollector',
    'DMSCollector',
    # DevOps Tools
    'CodeCommitCollector',
    'CodeBuildCollector',
    'CodeDeployCollector',
    'CodePipelineCollector',
    'CloudFormationCollector',
    # Management & Governance
    'CloudTrailCollector',
    'ConfigCollector',
    'SSMCollector',
    'ControlTowerCollector',
    'ServiceCatalogCollector',
    # Cost Management
    'CostExplorerCollector',
    'BudgetsCollector',
    'CURCollector',
    'SavingsPlansCollector',
    'ReservedInstancesCollector',
    'ComputeOptimizerCollector'
]
