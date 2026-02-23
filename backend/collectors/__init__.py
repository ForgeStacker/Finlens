"""Aggregated registry for all AWS service collectors."""
from __future__ import annotations

# ---- Original collectors (backend-new) ----
from .apigateway import collect_apigateway_all, collect_apigateway_v2
from .cloudfront import collect_cloudfront
from .cloudwatch import collect_cloudwatch
from .cloudwatch_logs import collect_cloudwatch_logs
from .cloudwatchevent import collect_cloudwatchevent
from .dms import collect_dms
from .docdb import collect_docdb
from .dynamodb import collect_dynamodb
from .ec2 import collect_ec2
from .ecr import collect_ecr
from .eks import collect_eks
from .elasticache import collect_elasticache
from .elb import collect_elb
from .glue import collect_glue
from .iam import collect_iam
from .kafka import collect_kafka
from .kinesis import collect_kinesis
from .kms import collect_kms
from .lambda_service import collect_lambda
from .msk import collect_msk
from .rds import collect_rds
from .route53 import collect_route53
from .s3 import collect_s3
from .sagemaker import collect_sagemaker
from .secrets import collect_secrets
from .sns import collect_sns
from .sqs import collect_sqs
from .vpc import collect_vpc
from .waf import collect_waf

# ---- New collectors (ported from old backend) ----
# AI/ML
from .comprehend import collect_comprehend
from .lex import collect_lex
from .polly import collect_polly
from .rekognition import collect_rekognition
from .textract import collect_textract

# Analytics
from .athena import collect_athena
from .emr import collect_emr
from .opensearch import collect_opensearch
from .quicksight import collect_quicksight

# Compute
from .ami import collect_ami
from .asg import collect_asg
from .ecs import collect_ecs
from .elasticbeanstalk import collect_elasticbeanstalk

# Cost Management
from .budgets import collect_budgets
from .computeoptimizer import collect_computeoptimizer
from .costexplorer_collector import collect_costexplorer
from .cur import collect_cur
from .reservedinstances import collect_reservedinstances
from .savingsplans import collect_savingsplans

# Database
from .neptune import collect_neptune
from .redshift import collect_redshift

# DevOps
from .cloudformation import collect_cloudformation
from .codebuild import collect_codebuild
from .codecommit import collect_codecommit
from .codedeploy import collect_codedeploy
from .codepipeline import collect_codepipeline

# Integration
from .ses import collect_ses
from .stepfunctions import collect_stepfunctions

# Management & Governance
from .awsconfig import collect_awsconfig
from .cloudtrail import collect_cloudtrail
from .controltower import collect_controltower
from .servicecatalog import collect_servicecatalog
from .ssm import collect_ssm

# Migration & Transfer
from .datasync import collect_datasync
from .mgn import collect_mgn
from .migrationhub import collect_migrationhub
from .snowball import collect_snowball
from .transfer import collect_transfer

# Networking
from .elasticip import collect_elasticip
from .vpcpeering import collect_vpcpeering

# Security
from .acm import collect_acm
from .guardduty import collect_guardduty
from .inspector import collect_inspector
from .organizations import collect_organizations
from .shield import collect_shield

# Storage
from .ebs import collect_ebs
from .efs import collect_efs
from .snapshot import collect_snapshots
from .storagegateway import collect_storagegateway


COLLECTOR_FUNCTIONS = {
    # ---------- Original ----------
    "API Gateway": collect_apigateway_all,
    "CloudFront": collect_cloudfront,
    "CloudWatchAlarm": collect_cloudwatch,
    "CloudWatchLogs": collect_cloudwatch_logs,
    "CloudWatchEvent": collect_cloudwatchevent,
    "DMS": collect_dms,
    "DatabaseMigrationService": collect_dms,
    "DocumentDB": collect_docdb,
    "DynamoDB": collect_dynamodb,
    "EC2": collect_ec2,
    "ECR": collect_ecr,
    "EKS": collect_eks,
    "ELB": collect_elb,
    "ElastiCache": collect_elasticache,
    "Glue": collect_glue,
    "IAM": collect_iam,
    "Kinesis": collect_kinesis,
    "KMS": collect_kms,
    "Lambda": collect_lambda,
    "Kafka": collect_kafka,
    "MSK": collect_msk,
    "RDS": collect_rds,
    "Route53": collect_route53,
    "S3": collect_s3,
    "SageMaker": collect_sagemaker,
    "SecretsManager": collect_secrets,
    "SNS": collect_sns,
    "SQS": collect_sqs,
    "VPC": collect_vpc,
    "WAF": collect_waf,
    # ---------- AI/ML ----------
    "Comprehend": collect_comprehend,
    "Lex": collect_lex,
    "Polly": collect_polly,
    "Rekognition": collect_rekognition,
    "Textract": collect_textract,
    # ---------- Analytics ----------
    "Athena": collect_athena,
    "EMR": collect_emr,
    "OpenSearch": collect_opensearch,
    "QuickSight": collect_quicksight,
    # ---------- Compute ----------
    "AMI": collect_ami,
    "ASG": collect_asg,
    "ECS": collect_ecs,
    "ElasticBeanstalk": collect_elasticbeanstalk,
    # ---------- Cost Management ----------
    "Budgets": collect_budgets,
    "ComputeOptimizer": collect_computeoptimizer,
    "CostExplorer": collect_costexplorer,
    "CUR": collect_cur,
    "ReservedInstances": collect_reservedinstances,
    "SavingsPlans": collect_savingsplans,
    # ---------- Database ----------
    "Neptune": collect_neptune,
    "Redshift": collect_redshift,
    # ---------- DevOps ----------
    "CloudFormation": collect_cloudformation,
    "CodeBuild": collect_codebuild,
    "CodeCommit": collect_codecommit,
    "CodeDeploy": collect_codedeploy,
    "CodePipeline": collect_codepipeline,
    # ---------- Integration ----------
    "SES": collect_ses,
    "StepFunctions": collect_stepfunctions,
    # ---------- Management & Governance ----------
    "AWSConfig": collect_awsconfig,
    "CloudTrail": collect_cloudtrail,
    "ControlTower": collect_controltower,
    "ServiceCatalog": collect_servicecatalog,
    "SSM": collect_ssm,
    # ---------- Migration & Transfer ----------
    "DataSync": collect_datasync,
    "MGN": collect_mgn,
    "MigrationHub": collect_migrationhub,
    "Snowball": collect_snowball,
    "Transfer": collect_transfer,
    # ---------- Networking ----------
    "ElasticIP": collect_elasticip,
    "VPCPeering": collect_vpcpeering,
    # ---------- Security ----------
    "ACM": collect_acm,
    "GuardDuty": collect_guardduty,
    "Inspector": collect_inspector,
    "Organizations": collect_organizations,
    "Shield": collect_shield,
    # ---------- Storage ----------
    "EBS": collect_ebs,
    "EFS": collect_efs,
    "Snapshots": collect_snapshots,
    "StorageGateway": collect_storagegateway,
}

__all__ = [
    "COLLECTOR_FUNCTIONS",
    "collect_apigateway_all",
    "collect_apigateway_v2",
    "collect_cloudfront",
    "collect_cloudwatch",
    "collect_cloudwatchevent",
    "collect_dms",
    "collect_docdb",
    "collect_dynamodb",
    "collect_ec2",
    "collect_ecr",
    "collect_eks",
    "collect_elasticache",
    "collect_elb",
    "collect_glue",
    "collect_iam",
    "collect_kafka",
    "collect_kinesis",
    "collect_kms",
    "collect_lambda",
    "collect_msk",
    "collect_rds",
    "collect_route53",
    "collect_s3",
    "collect_sagemaker",
    "collect_secrets",
    "collect_sns",
    "collect_sqs",
    "collect_vpc",
    "collect_waf",
]
