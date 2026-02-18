"""
Glue Collector
Collects AWS Glue databases, tables, jobs, and crawlers
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class GlueCollector(BaseCollector):
    """Collector for AWS Glue resources"""
    
    category = "analytics"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Glue collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'glue')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Glue resources
        
        Returns:
            Dictionary containing Glue resources
        """
        logger.info(f"Collecting glue data from {self.region_name}")
        
        try:
            databases = self._collect_databases()
            jobs = self._collect_jobs()
            crawlers = self._collect_crawlers()
            dev_endpoints = self._collect_dev_endpoints()
            
            return {
                'service': 'glue',
                'region': self.region_name,
                'account_id': self.account_id,
                'profile': self.profile_name,
                'databases': databases,
                'jobs': jobs,
                'crawlers': crawlers,
                'dev_endpoints': dev_endpoints,
                'summary': {
                    'database_count': len(databases),
                    'job_count': len(jobs),
                    'crawler_count': len(crawlers),
                    'dev_endpoint_count': len(dev_endpoints)
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting glue data: {e}")
            raise
    
    def _collect_databases(self) -> List[Dict[str, Any]]:
        """Collect Glue databases"""
        databases = []
        
        try:
            paginator = self.client.get_paginator('get_databases')
            
            for page in paginator.paginate():
                for db in page.get('DatabaseList', []):
                    database_data = {
                        'name': db.get('Name'),
                        'description': db.get('Description', ''),
                        'location_uri': db.get('LocationUri', ''),
                        'create_time': str(db.get('CreateTime', '')),
                        'parameters': db.get('Parameters', {}),
                        'catalog_id': db.get('CatalogId'),
                        'tables': []
                    }
                    
                    # Get tables for this database
                    try:
                        table_paginator = self.client.get_paginator('get_tables')
                        for table_page in table_paginator.paginate(DatabaseName=db.get('Name')):
                            for table in table_page.get('TableList', []):
                                database_data['tables'].append({
                                    'name': table.get('Name'),
                                    'storage_descriptor': {
                                        'location': table.get('StorageDescriptor', {}).get('Location', ''),
                                        'input_format': table.get('StorageDescriptor', {}).get('InputFormat', ''),
                                        'output_format': table.get('StorageDescriptor', {}).get('OutputFormat', '')
                                    },
                                    'partition_keys': table.get('PartitionKeys', []),
                                    'table_type': table.get('TableType'),
                                    'create_time': str(table.get('CreateTime', ''))
                                })
                    except Exception as e:
                        logger.warning(f"Could not get tables for database {db.get('Name')}: {e}")
                    
                    databases.append(database_data)
            
            logger.info(f"Collected {len(databases)} Glue databases from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Glue databases: {e}")
        
        return databases
    
    def _collect_jobs(self) -> List[Dict[str, Any]]:
        """Collect Glue jobs"""
        jobs = []
        
        try:
            paginator = self.client.get_paginator('get_jobs')
            
            for page in paginator.paginate():
                for job in page.get('Jobs', []):
                    jobs.append({
                        'name': job.get('Name'),
                        'description': job.get('Description', ''),
                        'role': job.get('Role'),
                        'created_on': str(job.get('CreatedOn', '')),
                        'last_modified_on': str(job.get('LastModifiedOn', '')),
                        'execution_property': job.get('ExecutionProperty', {}),
                        'command': {
                            'name': job.get('Command', {}).get('Name'),
                            'script_location': job.get('Command', {}).get('ScriptLocation', '')
                        },
                        'max_retries': job.get('MaxRetries'),
                        'timeout': job.get('Timeout'),
                        'glue_version': job.get('GlueVersion'),
                        'number_of_workers': job.get('NumberOfWorkers'),
                        'worker_type': job.get('WorkerType')
                    })
            
            logger.info(f"Collected {len(jobs)} Glue jobs from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Glue jobs: {e}")
        
        return jobs
    
    def _collect_crawlers(self) -> List[Dict[str, Any]]:
        """Collect Glue crawlers"""
        crawlers = []
        
        try:
            paginator = self.client.get_paginator('get_crawlers')
            
            for page in paginator.paginate():
                for crawler in page.get('Crawlers', []):
                    crawlers.append({
                        'name': crawler.get('Name'),
                        'role': crawler.get('Role'),
                        'state': crawler.get('State'),
                        'database_name': crawler.get('DatabaseName'),
                        'description': crawler.get('Description', ''),
                        'targets': crawler.get('Targets', {}),
                        'schedule': crawler.get('Schedule', {}).get('ScheduleExpression', ''),
                        'classifiers': crawler.get('Classifiers', []),
                        'creation_time': str(crawler.get('CreationTime', '')),
                        'last_updated': str(crawler.get('LastUpdated', '')),
                        'last_crawl': crawler.get('LastCrawl', {}),
                        'version': crawler.get('Version')
                    })
            
            logger.info(f"Collected {len(crawlers)} Glue crawlers from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Glue crawlers: {e}")
        
        return crawlers
    
    def _collect_dev_endpoints(self) -> List[Dict[str, Any]]:
        """Collect Glue development endpoints"""
        endpoints = []
        
        try:
            paginator = self.client.get_paginator('get_dev_endpoints')
            
            for page in paginator.paginate():
                for endpoint in page.get('DevEndpoints', []):
                    endpoints.append({
                        'endpoint_name': endpoint.get('EndpointName'),
                        'role_arn': endpoint.get('RoleArn'),
                        'status': endpoint.get('Status'),
                        'public_address': endpoint.get('PublicAddress', ''),
                        'private_address': endpoint.get('PrivateAddress', ''),
                        'number_of_nodes': endpoint.get('NumberOfNodes'),
                        'worker_type': endpoint.get('WorkerType'),
                        'glue_version': endpoint.get('GlueVersion'),
                        'created_timestamp': str(endpoint.get('CreatedTimestamp', '')),
                        'last_modified_timestamp': str(endpoint.get('LastModifiedTimestamp', ''))
                    })
            
            logger.info(f"Collected {len(endpoints)} Glue dev endpoints from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Glue dev endpoints: {e}")
        
        return endpoints
