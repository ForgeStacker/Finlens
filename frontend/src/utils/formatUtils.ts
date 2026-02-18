/**
 * Utility functions for formatting text and service names
 */

/**
 * Formats a service name by adding spaces between words and applying proper title case.
 * Follows patterns like "Secrets Manager", "Trusted Advisor", "Cost Explorer".
 * 
 * Examples:
 * - "secretsmanager" -> "Secrets Manager"
 * - "trustedadvisor" -> "Trusted Advisor"  
 * - "costexplorer" -> "Cost Explorer"
 * - "cloudformation" -> "Cloud Formation"
 * - "codepipeline" -> "Code Pipeline"
 * - "computeoptimizer" -> "Compute Optimizer"
 * - "reservedinstances" -> "Reserved Instances"
 * - "CLOUDEXPLORER" -> "Cloud Explorer"
 * - "EC2" -> "EC2"
 * - "dynamoDB" -> "Dynamo DB"
 */
export function formatServiceName(serviceName: string): string {
  if (!serviceName) return '';
  
  // Special cases for common AWS service patterns - direct replacements
  const directReplacements: Record<string, string> = {
    'secretsmanager': 'Secrets Manager',
    'trustedadvisor': 'Trusted Advisor',
    'costexplorer': 'Cost Explorer',
    'computeoptimizer': 'Compute Optimizer',
    'reservedinstances': 'Reserved Instances',
    'savingsplans': 'Savings Plans',
    'cloudtrail': 'Cloud Trail',
    'controltower': 'Control Tower',
    'servicecatalog': 'Service Catalog',
    'cloudformation': 'Cloud Formation',
    'codebuild': 'Code Build',
    'codecommit': 'Code Commit',
    'codedeploy': 'Code Deploy',
    'codepipeline': 'Code Pipeline',
    'cloudwatch': 'Cloud Watch',
    'cloudfront': 'Cloud Front',
    'elasticbeanstalk': 'Elastic Beanstalk',
    'elasticache': 'Elastic Cache',
    'elasticip': 'Elastic IP',
    'dynamodb': 'Dynamo DB',
    'documentdb': 'Document DB',
    'docdb': 'Document DB',
    'opensearch': 'Open Search',
    'quicksight': 'Quick Sight',
    'eventbridge': 'Event Bridge',
    'stepfunctions': 'Step Functions',
    'apigateway': 'API Gateway',
    'vpcpeering': 'VPC Peering',
    'migrationhub': 'Migration Hub',
    'datasync': 'Data Sync',
    'sagemaker': 'Sage Maker'
  };
  
  // Special abbreviations that should remain as-is
  const specialAbbreviations: Record<string, string> = {
    'ec2': 'EC2',
    'rds': 'RDS', 
    'vpc': 'VPC',
    's3': 'S3',
    'iam': 'IAM',
    'kms': 'KMS',
    'sns': 'SNS',
    'sqs': 'SQS',
    'eks': 'EKS',
    'ecs': 'ECS',
    'ssm': 'SSM',
    'acm': 'ACM',
    'waf': 'WAF',
    'cur': 'CUR',
    'mgn': 'MGN',
    'dms': 'DMS',
    'emr': 'EMR'
  };
  
  const lowerServiceName = serviceName.toLowerCase();
  
  // Check for direct replacements first
  if (directReplacements[lowerServiceName]) {
    return directReplacements[lowerServiceName];
  }
  
  // Check for special abbreviations
  if (specialAbbreviations[lowerServiceName]) {
    return specialAbbreviations[lowerServiceName];
  }
  
  // For other cases, apply general formatting rules
  return serviceName
    // First handle snake_case and kebab-case: replace underscores and hyphens with spaces
    .replace(/[_-]/g, ' ')
    // Insert space before capital letters that follow lowercase letters
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    // Insert space between groups of capital letters and following lowercase
    .replace(/([A-Z])([A-Z][a-z])/g, '$1 $2')
    // Handle sequences of lowercase followed by multiple capitals
    .replace(/([a-z])([A-Z]{2,})/g, '$1 $2')
    // Clean up multiple spaces
    .replace(/\s+/g, ' ')
    // Trim and convert to proper title case
    .trim()
    .split(' ')
    .map(word => {
      const lowerWord = word.toLowerCase();
      // Keep special abbreviations as defined above
      if (specialAbbreviations[lowerWord]) {
        return specialAbbreviations[lowerWord];
      }
      // For other words, capitalize first letter and lowercase the rest
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(' ');
}

/**
 * Formats service name for display in breadcrumbs or headers (uppercase style)
 */
export function formatServiceNameUppercase(serviceName: string): string {
  return formatServiceName(serviceName).toUpperCase();
}