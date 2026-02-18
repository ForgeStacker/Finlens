"""
QuickSight Collector
Collects AWS QuickSight dashboards, analyses, and datasets
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class QuickSightCollector(BaseCollector):
    """Collector for AWS QuickSight resources"""
    
    category = "analytics"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize QuickSight collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'quicksight')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect QuickSight resources
        
        Returns:
            Dictionary containing QuickSight resources
        """
        logger.info(f"Collecting quicksight data from {self.region_name}")
        
        try:
            dashboards = self._collect_dashboards()
            analyses = self._collect_analyses()
            datasets = self._collect_datasets()
            data_sources = self._collect_data_sources()
            
            return {
                'service': 'quicksight',
                'region': self.region_name,
                'account_id': self.account_id,
                'profile': self.profile_name,
                'dashboards': dashboards,
                'analyses': analyses,
                'datasets': datasets,
                'data_sources': data_sources,
                'summary': {
                    'dashboard_count': len(dashboards),
                    'analysis_count': len(analyses),
                    'dataset_count': len(datasets),
                    'data_source_count': len(data_sources)
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting quicksight data: {e}")
            raise
    
    def _collect_dashboards(self) -> List[Dict[str, Any]]:
        """Collect QuickSight dashboards"""
        dashboards = []
        
        try:
            # List dashboards
            response = self.client.list_dashboards(AwsAccountId=self.account_id)
            
            for dashboard_summary in response.get('DashboardSummaryList', []):
                dashboard_id = dashboard_summary.get('DashboardId')
                
                try:
                    # Get dashboard details
                    desc_response = self.client.describe_dashboard(
                        AwsAccountId=self.account_id,
                        DashboardId=dashboard_id
                    )
                    dashboard = desc_response.get('Dashboard', {})
                    
                    dashboards.append({
                        'dashboard_id': dashboard_id,
                        'name': dashboard.get('Name'),
                        'arn': dashboard.get('Arn'),
                        'version': dashboard.get('Version', {}).get('VersionNumber'),
                        'status': dashboard.get('Version', {}).get('Status'),
                        'created_time': str(dashboard.get('CreatedTime', '')),
                        'last_updated_time': str(dashboard.get('LastUpdatedTime', '')),
                        'last_published_time': str(dashboard.get('LastPublishedTime', '')),
                        'description': dashboard.get('Version', {}).get('Description', ''),
                        'theme_arn': dashboard.get('Version', {}).get('ThemeArn', ''),
                        'sheets': [
                            {
                                'sheet_id': sheet.get('SheetId'),
                                'name': sheet.get('Name')
                            }
                            for sheet in dashboard.get('Version', {}).get('Sheets', [])
                        ]
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get details for dashboard {dashboard_id}: {e}")
                    dashboards.append({
                        'dashboard_id': dashboard_id,
                        'name': dashboard_summary.get('Name'),
                        'error': str(e)
                    })
            
            logger.info(f"Collected {len(dashboards)} QuickSight dashboards from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing QuickSight dashboards: {e}")
        
        return dashboards
    
    def _collect_analyses(self) -> List[Dict[str, Any]]:
        """Collect QuickSight analyses"""
        analyses = []
        
        try:
            # List analyses
            response = self.client.list_analyses(AwsAccountId=self.account_id)
            
            for analysis_summary in response.get('AnalysisSummaryList', []):
                analysis_id = analysis_summary.get('AnalysisId')
                
                try:
                    # Get analysis details
                    desc_response = self.client.describe_analysis(
                        AwsAccountId=self.account_id,
                        AnalysisId=analysis_id
                    )
                    analysis = desc_response.get('Analysis', {})
                    
                    analyses.append({
                        'analysis_id': analysis_id,
                        'name': analysis.get('Name'),
                        'arn': analysis.get('Arn'),
                        'status': analysis.get('Status'),
                        'created_time': str(analysis.get('CreatedTime', '')),
                        'last_updated_time': str(analysis.get('LastUpdatedTime', '')),
                        'theme_arn': analysis.get('ThemeArn', ''),
                        'sheets': [
                            {
                                'sheet_id': sheet.get('SheetId'),
                                'name': sheet.get('Name')
                            }
                            for sheet in analysis.get('Sheets', [])
                        ]
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get details for analysis {analysis_id}: {e}")
                    analyses.append({
                        'analysis_id': analysis_id,
                        'name': analysis_summary.get('Name'),
                        'error': str(e)
                    })
            
            logger.info(f"Collected {len(analyses)} QuickSight analyses from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing QuickSight analyses: {e}")
        
        return analyses
    
    def _collect_datasets(self) -> List[Dict[str, Any]]:
        """Collect QuickSight datasets"""
        datasets = []
        
        try:
            # List datasets
            response = self.client.list_data_sets(AwsAccountId=self.account_id)
            
            for dataset_summary in response.get('DataSetSummaries', []):
                dataset_id = dataset_summary.get('DataSetId')
                
                try:
                    # Get dataset details
                    desc_response = self.client.describe_data_set(
                        AwsAccountId=self.account_id,
                        DataSetId=dataset_id
                    )
                    dataset = desc_response.get('DataSet', {})
                    
                    datasets.append({
                        'dataset_id': dataset_id,
                        'name': dataset.get('Name'),
                        'arn': dataset.get('Arn'),
                        'import_mode': dataset.get('ImportMode'),
                        'created_time': str(dataset.get('CreatedTime', '')),
                        'last_updated_time': str(dataset.get('LastUpdatedTime', '')),
                        'physical_table_map': list(dataset.get('PhysicalTableMap', {}).keys()),
                        'logical_table_map': list(dataset.get('LogicalTableMap', {}).keys()),
                        'output_columns': [
                            {
                                'name': col.get('Name'),
                                'type': col.get('Type')
                            }
                            for col in dataset.get('OutputColumns', [])[:10]  # Limit to first 10
                        ],
                        'row_level_permission_data_set': dataset.get('RowLevelPermissionDataSet', {})
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get details for dataset {dataset_id}: {e}")
                    datasets.append({
                        'dataset_id': dataset_id,
                        'name': dataset_summary.get('Name'),
                        'error': str(e)
                    })
            
            logger.info(f"Collected {len(datasets)} QuickSight datasets from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing QuickSight datasets: {e}")
        
        return datasets
    
    def _collect_data_sources(self) -> List[Dict[str, Any]]:
        """Collect QuickSight data sources"""
        data_sources = []
        
        try:
            # List data sources
            response = self.client.list_data_sources(AwsAccountId=self.account_id)
            
            for ds_summary in response.get('DataSources', []):
                ds_id = ds_summary.get('DataSourceId')
                
                try:
                    # Get data source details
                    desc_response = self.client.describe_data_source(
                        AwsAccountId=self.account_id,
                        DataSourceId=ds_id
                    )
                    data_source = desc_response.get('DataSource', {})
                    
                    data_sources.append({
                        'data_source_id': ds_id,
                        'name': data_source.get('Name'),
                        'arn': data_source.get('Arn'),
                        'type': data_source.get('Type'),
                        'status': data_source.get('Status'),
                        'created_time': str(data_source.get('CreatedTime', '')),
                        'last_updated_time': str(data_source.get('LastUpdatedTime', '')),
                        'vpc_connection_properties': data_source.get('VpcConnectionProperties', {}),
                        'ssl_properties': data_source.get('SslProperties', {}),
                        'error_info': data_source.get('ErrorInfo', {})
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not get details for data source {ds_id}: {e}")
                    data_sources.append({
                        'data_source_id': ds_id,
                        'name': ds_summary.get('Name'),
                        'error': str(e)
                    })
            
            logger.info(f"Collected {len(data_sources)} QuickSight data sources from {self.region_name}")
            
        except Exception as e:
            logger.error(f"Error listing QuickSight data sources: {e}")
        
        return data_sources
