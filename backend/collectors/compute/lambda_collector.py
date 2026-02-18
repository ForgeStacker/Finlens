import boto3
from backend.collectors.base import BaseCollector

class LambdaCollector(BaseCollector):
    def __init__(self, profile, region):
        super().__init__(profile, region, 'lambda')
        self.client = boto3.client('lambda', region_name=region)

    def collect(self):
        # Collect all Lambda functions
        paginator = self.client.get_paginator('list_functions')
        functions = []
        detailed_functions = []
        for page in paginator.paginate():
            functions.extend(page['Functions'])
        for fn in functions:
            arn = fn['FunctionArn']
            # Get configuration
            config = self.client.get_function_configuration(FunctionName=arn)
            # Get tags
            tags = self.client.list_tags(Resource=arn)
            # Get event source mappings
            event_sources = self.client.list_event_source_mappings(FunctionName=arn)
            # Get aliases
            aliases = self.client.list_aliases(FunctionName=arn)
            # Get versions
            versions = self.client.list_versions_by_function(FunctionName=arn)
            # Get policy
            try:
                policy = self.client.get_policy(FunctionName=arn)
            except self.client.exceptions.ResourceNotFoundException:
                policy = None
            # Get concurrency
            try:
                concurrency = self.client.get_function_concurrency(FunctionName=arn)
            except Exception:
                concurrency = None
            # Get code
            code = self.client.get_function(FunctionName=arn)
            # Get environment
            environment = config.get('Environment', {})
            # Get layers
            layers = config.get('Layers', [])
            # Get permissions
            try:
                permissions = self.client.get_policy(FunctionName=arn)
            except Exception:
                permissions = None
            # Get VPC config
            vpc_config = config.get('VpcConfig', {})
            # Get event invoke config
            try:
                event_invoke_config = self.client.get_function_event_invoke_config(FunctionName=arn)
            except Exception:
                event_invoke_config = None
            detailed_functions.append({
                'function': fn,
                'configuration': config,
                'tags': tags,
                'event_sources': event_sources,
                'aliases': aliases,
                'versions': versions,
                'policy': policy,
                'concurrency': concurrency,
                'code': code,
                'environment': environment,
                'layers': layers,
                'permissions': permissions,
                'vpc_config': vpc_config,
                'event_invoke_config': event_invoke_config
            })
        return {'functions': detailed_functions}
