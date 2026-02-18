"""
Athena Collector
Collects AWS Athena workgroups and query executions
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AthenaCollector(BaseCollector):
    """Collector for AWS Athena resources"""
    
    category = "analytics"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Athena collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'athena')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Athena workgroups and queries
        
        Returns:
            Dictionary containing Athena resources
        """
        logger.info(f"Collecting athena data from {self.region_name}")
        
        try:
            workgroups = self._collect_workgroups()
            named_queries = self._collect_named_queries()
            data_catalogs = self._collect_data_catalogs()
            
            return {
                'service': 'athena',
                'region': self.region_name,
                'account_id': self.account_id,
                'profile': self.profile_name,
                'workgroups': workgroups,
                'named_queries': named_queries,
                'data_catalogs': data_catalogs,
                'summary': {
                    'workgroup_count': len(workgroups),
                    'named_query_count': len(named_queries),
                    'data_catalog_count': len(data_catalogs)
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting athena data: {e}")
            raise
    
    def _collect_workgroups(self) -> List[Dict[str, Any]]:
        """Collect Athena workgroups"""
        workgroups = []
        
        try:
            # List all workgroups
            response = self.client.list_work_groups()
            
            for wg in response.get('WorkGroups', []):
                workgroup_name = wg.get('Name')
                
                try:
                    # Get detailed workgroup information
                    detail = self.client.get_work_group(WorkGroup=workgroup_name)
                    workgroup_data = detail.get('WorkGroup', {})
                    
                    workgroups.append({
                        'name': workgroup_name,
                        'state': workgroup_data.get('State'),
                        'description': workgroup_data.get('Description', ''),
                        'creation_time': str(workgroup_data.get('CreationTime', '')),
                        'configuration': workgroup_data.get('Configuration', {}),
                        'tags': self._get_workgroup_tags(workgroup_name)
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get details for workgroup {workgroup_name}: {e}")
                    workgroups.append({
                        'name': workgroup_name,
                        'state': wg.get('State'),
                        'error': str(e)
                    })
            
            logger.info(f"Collected {len(workgroups)} Athena workgroups from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Athena workgroups: {e}")
        
        return workgroups
    
    def _collect_named_queries(self) -> List[Dict[str, Any]]:
        """Collect Athena named queries"""
        queries = []
        
        try:
            # List all named queries
            response = self.client.list_named_queries()
            query_ids = response.get('NamedQueryIds', [])
            
            if query_ids:
                # Get batch details
                batch_response = self.client.batch_get_named_query(NamedQueryIds=query_ids[:50])
                
                for query in batch_response.get('NamedQueries', []):
                    queries.append({
                        'query_id': query.get('NamedQueryId'),
                        'name': query.get('Name'),
                        'description': query.get('Description', ''),
                        'database': query.get('Database'),
                        'query_string': query.get('QueryString', '')[:200],  # Truncate for brevity
                        'workgroup': query.get('WorkGroup')
                    })
            
            logger.info(f"Collected {len(queries)} Athena named queries from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Athena named queries: {e}")
        
        return queries
    
    def _collect_data_catalogs(self) -> List[Dict[str, Any]]:
        """Collect Athena data catalogs"""
        catalogs = []
        
        try:
            # List all data catalogs
            response = self.client.list_data_catalogs()
            
            for catalog in response.get('DataCatalogsSummary', []):
                catalog_name = catalog.get('CatalogName')
                
                try:
                    # Get detailed catalog information
                    detail = self.client.get_data_catalog(Name=catalog_name)
                    catalog_data = detail.get('DataCatalog', {})
                    
                    catalogs.append({
                        'name': catalog_name,
                        'type': catalog_data.get('Type'),
                        'description': catalog_data.get('Description', ''),
                        'parameters': catalog_data.get('Parameters', {})
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get details for catalog {catalog_name}: {e}")
                    catalogs.append({
                        'name': catalog_name,
                        'type': catalog.get('Type'),
                        'error': str(e)
                    })
            
            logger.info(f"Collected {len(catalogs)} Athena data catalogs from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing Athena data catalogs: {e}")
        
        return catalogs
    
    def _get_workgroup_tags(self, workgroup_name: str) -> Dict[str, str]:
        """Get tags for a workgroup"""
        try:
            response = self.client.list_tags_for_resource(
                ResourceARN=f"arn:aws:athena:{self.region_name}:{self.account_id}:workgroup/{workgroup_name}"
            )
            tags = {tag['Key']: tag['Value'] for tag in response.get('Tags', [])}
            return tags
        except Exception as e:
            logger.warning(f"Could not get tags for workgroup {workgroup_name}: {e}")
            return {}
