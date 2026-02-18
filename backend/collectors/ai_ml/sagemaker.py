"""
SageMaker Collector
Collects AWS SageMaker resources including endpoints, models, and notebooks
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SageMakerCollector(BaseCollector):
    """Collector for AWS SageMaker resources"""
    
    category = "ai_ml"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize SageMaker collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'sagemaker')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect SageMaker resources
        
        Returns:
            Dictionary containing SageMaker data
        """
        try:
            logger.info(f"Collecting SageMaker resources from {self.region_name}")
            
            resources = []
            
            # Collect endpoints
            endpoints = self._collect_endpoints()
            resources.extend(endpoints)
            
            # Collect models
            models = self._collect_models()
            resources.extend(models)
            
            # Collect notebook instances
            notebooks = self._collect_notebooks()
            resources.extend(notebooks)
            
            # Collect training jobs
            training_jobs = self._collect_training_jobs()
            resources.extend(training_jobs)
            
            logger.info(f"Collected {len(resources)} SageMaker resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'endpoints': len(endpoints),
                'models': len(models),
                'notebooks': len(notebooks),
                'training_jobs': len(training_jobs)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting SageMaker resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_endpoints(self) -> List[Dict[str, Any]]:
        """Collect SageMaker endpoints"""
        endpoints = []
        try:
            response = self.client.list_endpoints()
            
            for endpoint in response.get('Endpoints', []):
                endpoint_name = endpoint.get('EndpointName')
                
                # Get endpoint details
                try:
                    detail = self.client.describe_endpoint(EndpointName=endpoint_name)
                    
                    endpoints.append({
                        'resource_id': detail.get('EndpointArn'),
                        'resource_type': 'sagemaker-endpoint',
                        'resource_name': endpoint_name,
                        'region': self.region_name,
                        'status': endpoint.get('EndpointStatus'),
                        'creation_time': endpoint.get('CreationTime'),
                        'last_modified': endpoint.get('LastModifiedTime'),
                        'endpoint_config_name': detail.get('EndpointConfigName'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting endpoint details for {endpoint_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting SageMaker endpoints: {e}")
        
        return endpoints
    
    def _collect_models(self) -> List[Dict[str, Any]]:
        """Collect SageMaker models"""
        models = []
        try:
            response = self.client.list_models()
            
            for model in response.get('Models', []):
                model_name = model.get('ModelName')
                
                # Get model details
                try:
                    detail = self.client.describe_model(ModelName=model_name)
                    
                    models.append({
                        'resource_id': model.get('ModelArn'),
                        'resource_type': 'sagemaker-model',
                        'resource_name': model_name,
                        'region': self.region_name,
                        'creation_time': model.get('CreationTime'),
                        'execution_role_arn': detail.get('ExecutionRoleArn'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting model details for {model_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting SageMaker models: {e}")
        
        return models
    
    def _collect_notebooks(self) -> List[Dict[str, Any]]:
        """Collect SageMaker notebook instances"""
        notebooks = []
        try:
            response = self.client.list_notebook_instances()
            
            for notebook in response.get('NotebookInstances', []):
                notebook_name = notebook.get('NotebookInstanceName')
                
                # Get notebook details
                try:
                    detail = self.client.describe_notebook_instance(NotebookInstanceName=notebook_name)
                    
                    notebooks.append({
                        'resource_id': notebook.get('NotebookInstanceArn'),
                        'resource_type': 'sagemaker-notebook',
                        'resource_name': notebook_name,
                        'region': self.region_name,
                        'status': notebook.get('NotebookInstanceStatus'),
                        'instance_type': notebook.get('InstanceType'),
                        'creation_time': notebook.get('CreationTime'),
                        'last_modified': notebook.get('LastModifiedTime'),
                        'url': notebook.get('Url'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting notebook details for {notebook_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting SageMaker notebooks: {e}")
        
        return notebooks
    
    def _collect_training_jobs(self) -> List[Dict[str, Any]]:
        """Collect recent SageMaker training jobs"""
        training_jobs = []
        try:
            response = self.client.list_training_jobs(MaxResults=50)
            
            for job in response.get('TrainingJobSummaries', []):
                training_jobs.append({
                    'resource_id': job.get('TrainingJobArn'),
                    'resource_type': 'sagemaker-training-job',
                    'resource_name': job.get('TrainingJobName'),
                    'region': self.region_name,
                    'status': job.get('TrainingJobStatus'),
                    'creation_time': job.get('CreationTime'),
                    'training_start_time': job.get('TrainingStartTime'),
                    'training_end_time': job.get('TrainingEndTime'),
                    'last_modified': job.get('LastModifiedTime'),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting SageMaker training jobs: {e}")
        
        return training_jobs
