import React, { type ComponentType } from 'react';
import { Server } from 'lucide-react';

// Import only the AWS icons we actually have
import ec2Icon from '/src/assets/aws-icons/Arch_Amazon-EC2_64.svg';
import eksIcon from '/src/assets/aws-icons/Arch_Amazon-EKS_64.svg';
import lambdaIcon from '/src/assets/aws-icons/Arch_AWS-Lambda_64.svg';
import ecsIcon from '/src/assets/aws-icons/Arch_Amazon-ECS_64.svg';
import ecrIcon from '/src/assets/aws-icons/Arch_Amazon-ECR_64.svg';
import computeOptimizerIcon from '/src/assets/aws-icons/Arch_AWS-Compute-Optimizer_64.svg';
import rdsIcon from '/src/assets/aws-icons/Arch_Amazon-RDS_64.svg';
import dynamodbIcon from '/src/assets/aws-icons/Arch_Amazon-DynamoDB_64.svg';
import redshiftIcon from '/src/assets/aws-icons/Arch_Amazon-Redshift_64.svg';
import s3Icon from '/src/assets/aws-icons/Arch_Amazon-S3_64.svg';
import ebsIcon from '/src/assets/aws-icons/Arch_Amazon-EBS_64.svg';
import vpcIcon from '/src/assets/aws-icons/Arch_Amazon-VPC_64.svg';
import cloudfrontIcon from '/src/assets/aws-icons/Arch_Amazon-CloudFront_64.svg';
import route53Icon from '/src/assets/aws-icons/Arch_Amazon-Route-53_64.svg';
import elbIcon from '/src/assets/aws-icons/Arch_Elastic-Load-Balancing_64.svg';
import iamIcon from '/src/assets/aws-icons/Arch_AWS-IAM_64.svg';
import secretsManagerIcon from '/src/assets/aws-icons/Arch_AWS-Secrets-Manager_64.svg';
import securityHubIcon from '/src/assets/aws-icons/Arch_AWS-Security-Hub_64.svg';
import costExplorerIcon from '/src/assets/aws-icons/Arch_AWS-Cost-Explorer_64.svg';
import billingConductorIcon from '/src/assets/aws-icons/Arch_AWS-Billing-Conductor_64.svg';
import cloudwatchIcon from '/src/assets/aws-icons/Arch_Amazon-CloudWatch_64.svg';
import cloudtrailIcon from '/src/assets/aws-icons/Arch_AWS-CloudTrail_64.svg';
import athenaIcon from '/src/assets/aws-icons/Arch_Amazon-Athena_64.svg';
import glueIcon from '/src/assets/aws-icons/Arch_AWS-Glue_64.svg';
import kinesisIcon from '/src/assets/aws-icons/Arch_Amazon-Kinesis_64.svg';
import emrIcon from '/src/assets/aws-icons/Arch_Amazon-EMR_64.svg';
import opensearchIcon from '/src/assets/aws-icons/Arch_Amazon-OpenSearch-Service_64.svg';
import rekognitionIcon from '/src/assets/aws-icons/Arch_Amazon-Rekognition_64.svg';
import comprehendIcon from '/src/assets/aws-icons/Arch_Amazon-Comprehend_64.svg';
import textractIcon from '/src/assets/aws-icons/Arch_Amazon-Textract_64.svg';
import pollyIcon from '/src/assets/aws-icons/Arch_Amazon-Polly_64.svg';
import lexIcon from '/src/assets/aws-icons/Arch_Amazon-Lex_64.svg';
import sagemakerIcon from '/src/assets/aws-icons/Arch_Amazon-SageMaker_64.svg';
import snsIcon from '/src/assets/aws-icons/Arch_Amazon-SNS_64.svg';
import sqsIcon from '/src/assets/aws-icons/Arch_Amazon-SQS_64.svg';
import eventbridgeIcon from '/src/assets/aws-icons/Arch_Amazon-EventBridge_64.svg';
import stepfunctionsIcon from '/src/assets/aws-icons/Arch_AWS-Step-Functions_64.svg';
import codecommitIcon from '/src/assets/aws-icons/Arch_AWS-CodeCommit_64.svg';
import codebuildIcon from '/src/assets/aws-icons/Arch_AWS-CodeBuild_64.svg';
import codepipelineIcon from '/src/assets/aws-icons/Arch_AWS-CodePipeline_64.svg';
import codedeployIcon from '/src/assets/aws-icons/Arch_AWS-CodeDeploy_64.svg';
import datasyncIcon from '/src/assets/aws-icons/Arch_AWS-DataSync_64.svg';
import migrationhubIcon from '/src/assets/aws-icons/Arch_AWS-Migration-Hub_64.svg';
import kmsIcon from '/src/assets/aws-icons/Arch_AWS-KMS_64.svg';
import guardDutyIcon from '/src/assets/aws-icons/Arch_Amazon-GuardDuty_64.svg';
import cloudFormationIcon from '/src/assets/aws-icons/Arch_AWS-CloudFormation_64.svg';
import configIcon from '/src/assets/aws-icons/Arch_AWS-Config_64.svg';
import ssmIcon from '/src/assets/aws-icons/Arch_AWS-SSM_64.svg';
import trustedAdvisorIcon from '/src/assets/aws-icons/Arch_AWS-Trusted-Advisor_64.svg';
import wafIcon from '/src/assets/aws-icons/Arch_AWS-WAF_64.svg';
import acmIcon from '/src/assets/aws-icons/Arch_AWS-ACM_64.svg';
import apiGatewayIcon from '/src/assets/aws-icons/Arch_Amazon-API-Gateway_64.svg';
import serviceCatalogIcon from '/src/assets/aws-icons/Arch_AWS-Service-Catalog_64.svg';
import efsIcon from '/src/assets/aws-icons/Arch_Amazon-EFS_64.svg';
import elasticacheIcon from '/src/assets/aws-icons/Arch_Amazon-ElastiCache_64.svg';
import documentdbIcon from '/src/assets/aws-icons/Arch_Amazon-DocumentDB_64.svg';
import neptuneIcon from '/src/assets/aws-icons/Arch_Amazon-Neptune_64.svg';
import organizationsIcon from '/src/assets/aws-icons/Arch_AWS-Organizations_64.svg';
import sesIcon from '/src/assets/aws-icons/Arch_Amazon-SES_64.svg';
// Additional icons
import asgIcon from '/src/assets/aws-icons/Arch_Amazon-EC2-Auto-Scaling_64.svg';
import amiIcon from '/src/assets/aws-icons/Arch_Amazon-EC2-Image-Builder_64.svg';
import elasticBeanstalkIcon from '/src/assets/aws-icons/Arch_AWS-Elastic-Beanstalk_64.svg';
import fargateIcon from '/src/assets/aws-icons/Arch_AWS-Fargate_64.svg';
import budgetsIcon from '/src/assets/aws-icons/Arch_AWS-Budgets_64.svg';
import curIcon from '/src/assets/aws-icons/Arch_AWS-Cost-and-Usage-Report_64.svg';
import reservedInstancesIcon from '/src/assets/aws-icons/Arch_Reserved-Instance-Reporting_64.svg';
import savingsPlansIcon from '/src/assets/aws-icons/Arch_Savings-Plans_64.svg';
import auroraIcon from '/src/assets/aws-icons/Arch_Amazon-Aurora_64.svg';
import dmsIcon from '/src/assets/aws-icons/Arch_AWS-Database-Migration-Service_64.svg';
import controlTowerIcon from '/src/assets/aws-icons/Arch_AWS-Control-Tower_64.svg';
import inspectorIcon from '/src/assets/aws-icons/Arch_Amazon-Inspector_64.svg';
import mgnIcon from '/src/assets/aws-icons/Arch_AWS-Application-Migration-Service_64.svg';
import directConnectIcon from '/src/assets/aws-icons/Arch_AWS-Direct-Connect_64.svg';
import transitGatewayIcon from '/src/assets/aws-icons/Arch_AWS-Transit-Gateway_64.svg';
import mskIcon from '/src/assets/aws-icons/Arch_Amazon-MSK_64.svg';

// Map AWS service names to their icon files
const serviceIconMap: Record<string, string> = {
  // Compute
  'ec2': ec2Icon,
  'ami': amiIcon,
  'asg': asgIcon,
  'autoscaling': asgIcon,
  'ec2autoscaling': asgIcon,
  'elasticbeanstalk': elasticBeanstalkIcon,
  'elasticip': ec2Icon,
  'elasticips': ec2Icon,
  'eks': eksIcon,
  'lambda': lambdaIcon,
  'ecs': ecsIcon,
  'ecr': ecrIcon,
  'fargate': fargateIcon,
  'computeoptimizer': computeOptimizerIcon,
  
  // Database
  'rds': rdsIcon,
  'aurora': auroraIcon,
  'dynamodb': dynamodbIcon,
  'redshift': redshiftIcon,
  'elasticache': elasticacheIcon,
  'documentdb': documentdbIcon,
  'docdb': documentdbIcon,
  'neptune': neptuneIcon,
  'dms': dmsIcon,
  'databsemigrationservice': dmsIcon,
  
  // Storage
  's3': s3Icon,
  'ebs': ebsIcon,
  'efs': efsIcon,
  
  // Networking
  'vpc': vpcIcon,
  'vpcpeering': vpcIcon,
  'cloudfront': cloudfrontIcon,
  'route53': route53Icon,
  'routes3': route53Icon,
  'elb': elbIcon,
  'elbv2': elbIcon,
  'elasticloadbalancing': elbIcon,
  'apigateway': apiGatewayIcon,
  'directconnect': directConnectIcon,
  'transitgateway': transitGatewayIcon,
  
  // Security
  'iam': iamIcon,
  'kms': kmsIcon,
  'secretsmanager': secretsManagerIcon,
  'securityhub': securityHubIcon,
  'guardduty': guardDutyIcon,
  'waf': wafIcon,
  'acm': acmIcon,
  'inspector': inspectorIcon,
  
  // Analytics
  'athena': athenaIcon,
  'glue': glueIcon,
  'kinesis': kinesisIcon,
  'emr': emrIcon,
  'opensearch': opensearchIcon,
  'opensearchservice': opensearchIcon,
  
  // AI/ML
  'sagemaker': sagemakerIcon,
  'rekognition': rekognitionIcon,
  'comprehend': comprehendIcon,
  'textract': textractIcon,
  'polly': pollyIcon,
  'lex': lexIcon,
  
  // Management & Governance
  'cloudwatch': cloudwatchIcon,
  'cloudwatchlogs': cloudwatchIcon,
  'cloudwatch_logs': cloudwatchIcon,
  'cloudwatchevents': eventbridgeIcon,
  'cloudwatchevent': eventbridgeIcon,
  'cloudtrail': cloudtrailIcon,
  'cloudformation': cloudFormationIcon,
  'config': configIcon,
  'awsconfig': configIcon,
  'ssm': ssmIcon,
  'trustedadvisor': trustedAdvisorIcon,
  'servicecatalog': serviceCatalogIcon,
  'organizations': organizationsIcon,
  'controltower': controlTowerIcon,
  
  // Integration
  'sns': snsIcon,
  'sqs': sqsIcon,
  'eventbridge': eventbridgeIcon,
  'stepfunctions': stepfunctionsIcon,
  'ses': sesIcon,
  
  // DevOps Tools
  'codecommit': codecommitIcon,
  'codebuild': codebuildIcon,
  'codepipeline': codepipelineIcon,
  'codedeploy': codedeployIcon,
  
  // Migration & Transfer
  'datasync': datasyncIcon,
  'migrationhub': migrationhubIcon,
  'mgn': mgnIcon,
  'applicationmigrationservice': mgnIcon,
  
  // Cost Management
  'costexplorer': costExplorerIcon,
  'billing': billingConductorIcon,
  'budgets': budgetsIcon,
  'cur': curIcon,
  'costandusagereport': curIcon,
  'reservedinstances': reservedInstancesIcon,
  'savingsplans': savingsPlansIcon,
  
  // Streaming & Messaging
  'msk': mskIcon,
  'kafka': mskIcon,
  'amazonmanagedstreamingforapachekafka': mskIcon,
};

// Category icon mapping
const categoryIconMap: Record<string, string> = {
  'compute': ec2Icon,
  'database': rdsIcon,
  'storage': s3Icon,
  'networking': vpcIcon,
  'security': iamIcon,
  'analytics': athenaIcon,
  'ai_ml': sagemakerIcon,
  'management_governance': cloudwatchIcon,
  'integration': eventbridgeIcon,
  'devops_tools': codecommitIcon,
  'migration_transfer': datasyncIcon,
  'cost_management': costExplorerIcon,
  'general': ec2Icon,
};

type FallbackIconComponent = ComponentType<{ className?: string; size?: string | number }>;

interface AwsIconProps {
  service?: string;
  category?: string;
  size?: number;
  className?: string;
  fallbackIcon?: FallbackIconComponent; // Lucide React components share this signature
}

export function AwsIcon({ 
  service, 
  category, 
  size = 24, 
  className = "",
  fallbackIcon 
}: AwsIconProps) {
  // Determine which icon to use
  const iconPath = getAwsIconPath(service, category);
  
  // If no AWS icon is available, use fallback
  if (!iconPath) {
    const FallbackComponent: FallbackIconComponent = fallbackIcon || Server;
    return <FallbackComponent className={className} size={size} />;
  }
  
  return (
    <img
      src={iconPath}
      alt={`AWS ${service || category} icon`}
      className={className}
      style={{ width: size, height: size }}
      onError={(e) => {
        // If SVG fails to load, replace with fallback icon
        const target = e.target as HTMLImageElement;
        target.style.display = 'none';
        // Create fallback icon element here if needed
      }}
    />
  );
}

// Helper function to get icon path programmatically for internal use
function getAwsIconPath(service?: string, category?: string): string | null {
  const normalizedService = service?.toLowerCase();
  const normalizedCategory = category?.toLowerCase();
  return normalizedService ? serviceIconMap[normalizedService] :
    (normalizedCategory ? categoryIconMap[normalizedCategory] : null);
}