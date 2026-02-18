"""
Runner
Orchestrates execution of all enabled collectors
Implements CMMI Level 5 process management and quality controls
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.config_loader import FinLensConfig

# Import collectors from category folders
from backend.collectors.compute import EC2Collector, EKSCollector
from backend.collectors.compute.lambda_collector import LambdaCollector
from backend.collectors.compute.asg import ASGCollector
from backend.collectors.compute.elasticbeanstalk import ElasticBeanstalkCollector
from backend.collectors.compute.ecs import ECSCollector
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

from backend.utils.logger import get_logger, log_operation

logger = get_logger(__name__)


# Service collector registry - organized by category
SERVICE_COLLECTORS = {
    # Compute
    'ec2': EC2Collector,
    'eks': EKSCollector,
    'lambda': LambdaCollector,
    'asg': ASGCollector,
    'elasticbeanstalk': ElasticBeanstalkCollector,
    'ecs': ECSCollector,
    'ami': AMICollector,
    # Networking & Content Delivery
    'vpc': VPCCollector,
    'elb': ELBCollector,
    'elasticip': ElasticIPCollector,
    'route53': Route53Collector,
    'cloudfront': CloudFrontCollector,
    'vpcpeering': VPCPeeringCollector,
    # Database
    'rds': RDSCollector,
    'dynamodb': DynamoDBCollector,
    'elasticache': ElastiCacheCollector,
    'redshift': RedshiftCollector,
    'neptune': NeptuneCollector,
    'docdb': DocumentDBCollector,
    # Analytics & Big Data
    'athena': AthenaCollector,
    'glue': GlueCollector,
    'emr': EMRCollector,
    'kinesis': KinesisCollector,
    'opensearch': OpenSearchCollector,
    'quicksight': QuickSightCollector,
    # Application Integration
    'sqs': SQSCollector,
    'sns': SNSCollector,
    'eventbridge': EventBridgeCollector,
    'stepfunctions': StepFunctionsCollector,
    'apigateway': APIGatewayCollector,
    'ses': SESCollector,
    # Storage
    's3': S3Collector,
    'ebs': EBSCollector,
    'snapshot': SnapshotCollector,
    'efs': EFSCollector,
    'storagegateway': StorageGatewayCollector,
    'ecr': ECRCollector,
    # Security
    'iam': IAMCollector,
    'organizations': OrganizationsCollector,
    'kms': KMSCollector,
    'secretsmanager': SecretsManagerCollector,
    'acm': ACMCollector,
    'waf': WAFCollector,
    'shield': ShieldCollector,
    'guardduty': GuardDutyCollector,
    'inspector': InspectorCollector,
    # Monitoring
    'cloudwatch': CloudWatchCollector,
    # Cost Management
    'costexplorer': CostExplorerCollector,
    # AI & Machine Learning
    'comprehend': ComprehendCollector,
    'lex': LexCollector,
    'polly': PollyCollector,
    'textract': TextractCollector,
    'sagemaker': SageMakerCollector,
    'rekognition': RekognitionCollector,
    # Migration & Transfer
    'migrationhub': MigrationHubCollector,
    'datasync': DataSyncCollector,
    'snowball': SnowballCollector,
    'transfer': TransferCollector,
    'mgn': MGNCollector,
    'dms': DMSCollector,
    # DevOps Tools
    'codecommit': CodeCommitCollector,
    'codebuild': CodeBuildCollector,
    'codedeploy': CodeDeployCollector,
    'codepipeline': CodePipelineCollector,
    'cloudformation': CloudFormationCollector,
    # Management & Governance
    'cloudtrail': CloudTrailCollector,
    'config': ConfigCollector,
    'ssm': SSMCollector,
    'controltower': ControlTowerCollector,
    'servicecatalog': ServiceCatalogCollector,
    # Cost Management
    'costexplorer': CostExplorerCollector,
    'budgets': BudgetsCollector,
    'cur': CURCollector,
    'savingsplans': SavingsPlansCollector,
    'reservedinstances': ReservedInstancesCollector,
    'computeoptimizer': ComputeOptimizerCollector,
    # Add more collectors here as they are implemented
    # Storage: 'ebs', 'efs'
    # Database: 'dynamodb', 'elasticache'
    # Compute: 'lambda', 'ecs'
}


class CollectorRunner:
    """
    Orchestrates execution of service collectors
    Manages parallel/sequential execution based on configuration
    """
    
    def __init__(self, config: FinLensConfig, output_dir: Optional[Path] = None):
        """
        Initialize runner
        
        Args:
            config: FinLens configuration
            output_dir: Output directory for data files (default: ./data)
        """
        self.config = config
        
        if output_dir:
            self.output_dir = output_dir
        else:
            # Default to data/ directory in project root
            project_root = Path(__file__).parent.parent
            self.output_dir = project_root / 'data'
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: Dict[str, Any] = {
            'successful': [],
            'failed': [],
            'skipped': []
        }
    
    def run(self) -> Dict[str, Any]:
        """
        Execute all enabled collectors across profiles and regions
        
        Returns:
            Dictionary containing execution results
        """
        log_operation("SCAN", "START", f"Profiles: {len(self.config.profiles)}")
        start_time = time.time()
        
        try:
            # Get enabled services
            enabled_services = self._get_enabled_services()
            
            if not enabled_services:
                logger.warning("No services enabled for scanning")
                return self.results
            
            logger.info(f"Enabled services: {enabled_services}")
            
            # Execute for each profile
            for profile_config in self.config.profiles:
                profile_name = profile_config.name
                logger.info(f"Processing profile: {profile_name}")
                
                # Get regions to scan
                regions = self._get_regions_to_scan()
                
                if not regions:
                    logger.warning(f"No regions configured for scanning")
                    continue
                
                logger.info(f"Scanning regions: {regions}")
                
                # Execute collectors
                if self.config.scan.parallel:
                    self._run_parallel(profile_name, regions, enabled_services)
                else:
                    self._run_sequential(profile_name, regions, enabled_services)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log summary
            self._log_summary(execution_time)
            
            log_operation("SCAN", "SUCCESS", f"Duration: {execution_time:.2f}s")
            
            return self.results
            
        except Exception as e:
            log_operation("SCAN", "FAILED", str(e))
            raise
    
    def _get_enabled_services(self) -> List[str]:
        """
        Get list of services that should be scanned
        
        Returns:
            List of service names
        """
        available_services = list(SERVICE_COLLECTORS.keys())
        enabled = []
        
        for service in available_services:
            if self.config.services.should_scan_service(service):
                enabled.append(service)
        
        return enabled
    
    def _get_regions_to_scan(self) -> List[str]:
        """
        Get list of regions to scan based on configuration
        
        Returns:
            List of region names
        """
        # If include list is specified, use it
        if self.config.regions.include:
            return self.config.regions.include
        
        # Otherwise, could get all available regions and apply exclusions
        # For now, require explicit include list
        logger.warning("No regions specified in include list")
        return []
    
    def _run_sequential(
        self,
        profile_name: str,
        regions: List[str],
        services: List[str]
    ):
        """
        Run collectors sequentially (one at a time)
        
        Args:
            profile_name: AWS profile name
            regions: List of regions
            services: List of service names
        """
        logger.info("Running collectors sequentially")
        
        for region in regions:
            for service in services:
                self._execute_collector(profile_name, region, service)
    
    def _run_parallel(
        self,
        profile_name: str,
        regions: List[str],
        services: List[str]
    ):
        """
        Run collectors in parallel using thread pool
        
        Args:
            profile_name: AWS profile name
            regions: List of regions
            services: List of service names
        """
        logger.info("Running collectors in parallel")
        
        # Create tasks for each region-service combination
        tasks = [
            (profile_name, region, service)
            for region in regions
            for service in services
        ]
        
        # Execute in parallel with thread pool
        max_workers = min(10, len(tasks))  # Limit concurrent operations
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(
                    self._execute_collector,
                    profile_name,
                    region,
                    service
                ): (profile_name, region, service)
                for profile_name, region, service in tasks
            }
            
            # Wait for completion
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Task {task} generated an exception: {e}")
    
    def _execute_collector(
        self,
        profile_name: str,
        region: str,
        service: str
    ) -> bool:
        """
        Execute a single collector
        
        Args:
            profile_name: AWS profile name
            region: Region name
            service: Service name
            
        Returns:
            True if successful, False otherwise
        """
        task_id = f"{profile_name}/{region}/{service}"
        
        try:
            logger.info(f"Executing collector: {task_id}")
            
            # Check if collector exists
            if service not in SERVICE_COLLECTORS:
                logger.warning(f"No collector found for service: {service}")
                self.results['skipped'].append({
                    'profile': profile_name,
                    'region': region,
                    'service': service,
                    'reason': 'Collector not implemented'
                })
                return False
            
            # Create collector instance
            collector_class = SERVICE_COLLECTORS[service]
            collector = collector_class(profile_name, region)
            
            # Run collector
            success = collector.run(self.output_dir)
            
            if success:
                self.results['successful'].append({
                    'profile': profile_name,
                    'region': region,
                    'service': service
                })
                logger.info(f"Collector succeeded: {task_id}")
            else:
                self.results['failed'].append({
                    'profile': profile_name,
                    'region': region,
                    'service': service
                })
                logger.error(f"Collector failed: {task_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error executing collector {task_id}: {e}")
            self.results['failed'].append({
                'profile': profile_name,
                'region': region,
                'service': service,
                'error': str(e)
            })
            return False
    
    def _log_summary(self, execution_time: float):
        """
        Log execution summary
        
        Args:
            execution_time: Total execution time in seconds
        """
        successful = len(self.results['successful'])
        failed = len(self.results['failed'])
        skipped = len(self.results['skipped'])
        total = successful + failed + skipped
        
        logger.info("=" * 60)
        logger.info("SCAN SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total collectors: {total}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Skipped: {skipped}")
        logger.info(f"Execution time: {execution_time:.2f}s")
        logger.info("=" * 60)
        
        if failed > 0:
            logger.warning("Failed collectors:")
            for item in self.results['failed']:
                logger.warning(
                    f"  - {item['profile']}/{item['region']}/{item['service']}"
                )
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get execution results
        
        Returns:
            Results dictionary
        """
        return self.results


def run_scan(config: FinLensConfig, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to run scan
    
    Args:
        config: FinLens configuration
        output_dir: Output directory for data files
        
    Returns:
        Execution results
    """
    runner = CollectorRunner(config, output_dir)
    return runner.run()
