"""
DynamoDB Collector for FinLens
Collects comprehensive DynamoDB tables, indexes, and configuration data
"""

import json
from typing import Dict, List, Any, Optional
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

class DynamoDBCollector(BaseCollector):
    """Collector for DynamoDB data"""
    
    category = "database"
    
    def __init__(self, profile_name: str, region_name: str, service_name: str = "dynamodb"):
        super().__init__(profile_name, region_name, service_name)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def collect(self) -> Dict[str, Any]:
        """Main collection method for DynamoDB data"""
        try:
            self.logger.info(f"[DYNAMODB_COLLECTOR] START - Profile: {self.profile_name}, Region: {self.region_name}")
            
            # Initialize session manually
            import boto3
            self.session = boto3.Session(
                profile_name=self.profile_name,
                region_name=self.region_name
            )
            dynamodb_client = self.session.client('dynamodb', region_name=self.region_name)
            self.logger.info("DynamoDB client initialized successfully")
            
            self.logger.info("Collecting dynamodb data...")
            data = {
                "tables": self._collect_tables(dynamodb_client),
                "backups": self._collect_backups(dynamodb_client),
                "global_tables": self._collect_global_tables(dynamodb_client),
                "exports": self._collect_exports(dynamodb_client),
                "imports": self._collect_imports(dynamodb_client)
            }
            
            # Count total resources
            total_resources = len(data["tables"]) + len(data["backups"]) + len(data["global_tables"])
            
            self.logger.info(f"Collected {total_resources} DynamoDB resources from {self.region_name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting DynamoDB data: {str(e)}")
            return {}
    
    def _collect_tables(self, client) -> List[Dict[str, Any]]:
        """Collect DynamoDB tables"""
        try:
            tables = []
            
            # List all tables
            response = client.list_tables()
            table_names = response.get('TableNames', [])
            
            for table_name in table_names:
                try:
                    # Get table details
                    table_response = client.describe_table(TableName=table_name)
                    table_info = table_response.get('Table', {})
                    
                    table_data = {
                        "table_name": table_info.get("TableName"),
                        "table_status": table_info.get("TableStatus"),
                        "creation_date_time": table_info.get("CreationDateTime").isoformat() if table_info.get("CreationDateTime") else None,
                        "table_size_bytes": table_info.get("TableSizeBytes"),
                        "item_count": table_info.get("ItemCount"),
                        "table_arn": table_info.get("TableArn"),
                        "table_id": table_info.get("TableId"),
                        "key_schema": table_info.get("KeySchema", []),
                        "attribute_definitions": table_info.get("AttributeDefinitions", []),
                        "billing_mode": table_info.get("BillingModeSummary", {}).get("BillingMode"),
                        "provisioned_throughput": table_info.get("ProvisionedThroughput", {}),
                        "global_secondary_indexes": table_info.get("GlobalSecondaryIndexes", []),
                        "local_secondary_indexes": table_info.get("LocalSecondaryIndexes", []),
                        "stream_specification": table_info.get("StreamSpecification", {}),
                        "latest_stream_arn": table_info.get("LatestStreamArn"),
                        "latest_stream_label": table_info.get("LatestStreamLabel"),
                        "sse_description": table_info.get("SSEDescription", {}),
                        "tags": table_info.get("Tags", []),
                        "table_class_summary": table_info.get("TableClassSummary", {}),
                        "deletion_protection_enabled": table_info.get("DeletionProtectionEnabled")
                    }
                    
                    # Get table tags
                    try:
                        tags_response = client.list_tags_of_resource(ResourceArn=table_info["TableArn"])
                        table_data["tags"] = tags_response.get("Tags", [])
                    except Exception as e:
                        self.logger.debug(f"Could not get tags for table {table_name}: {e}")
                    
                    # Get continuous backups status
                    try:
                        backup_response = client.describe_continuous_backups(TableName=table_name)
                        table_data["continuous_backups"] = backup_response.get("ContinuousBackupsDescription", {})
                    except Exception as e:
                        self.logger.debug(f"Could not get backup info for table {table_name}: {e}")
                        table_data["continuous_backups"] = {}
                    
                    # Get time to live description
                    try:
                        ttl_response = client.describe_time_to_live(TableName=table_name)
                        table_data["time_to_live"] = ttl_response.get("TimeToLiveDescription", {})
                    except Exception as e:
                        self.logger.debug(f"Could not get TTL info for table {table_name}: {e}")
                        table_data["time_to_live"] = {}
                    
                    tables.append(table_data)
                    
                except Exception as e:
                    self.logger.warning(f"Error collecting details for table {table_name}: {e}")
            
            return tables
        except Exception as e:
            self.logger.warning(f"Error collecting DynamoDB tables: {e}")
            return []
    
    def _collect_backups(self, client) -> List[Dict[str, Any]]:
        """Collect DynamoDB backups"""
        try:
            backups = []
            
            response = client.list_backups()
            for backup in response.get('BackupSummaries', []):
                backup_data = {
                    "backup_arn": backup.get("BackupArn"),
                    "backup_name": backup.get("BackupName"),
                    "backup_status": backup.get("BackupStatus"),
                    "backup_type": backup.get("BackupType"),
                    "backup_creation_date_time": backup.get("BackupCreationDateTime").isoformat() if backup.get("BackupCreationDateTime") else None,
                    "backup_expiry_date_time": backup.get("BackupExpiryDateTime").isoformat() if backup.get("BackupExpiryDateTime") else None,
                    "table_name": backup.get("TableName"),
                    "table_id": backup.get("TableId"),
                    "table_arn": backup.get("TableArn"),
                    "backup_size_bytes": backup.get("BackupSizeBytes")
                }
                backups.append(backup_data)
            
            return backups
        except Exception as e:
            self.logger.warning(f"Error collecting DynamoDB backups: {e}")
            return []
    
    def _collect_global_tables(self, client) -> List[Dict[str, Any]]:
        """Collect DynamoDB global tables"""
        try:
            global_tables = []
            
            response = client.list_global_tables()
            for global_table in response.get('GlobalTables', []):
                global_table_data = {
                    "global_table_name": global_table.get("GlobalTableName"),
                    "replication_group": global_table.get("ReplicationGroup", [])
                }
                
                # Get detailed global table information
                try:
                    detail_response = client.describe_global_table(
                        GlobalTableName=global_table["GlobalTableName"]
                    )
                    global_table_data.update(detail_response.get("GlobalTableDescription", {}))
                except Exception as e:
                    self.logger.debug(f"Could not get global table details for {global_table['GlobalTableName']}: {e}")
                
                global_tables.append(global_table_data)
            
            return global_tables
        except Exception as e:
            self.logger.warning(f"Error collecting DynamoDB global tables: {e}")
            return []
    
    def _collect_exports(self, client) -> List[Dict[str, Any]]:
        """Collect DynamoDB exports"""
        try:
            exports = []
            
            response = client.list_exports()
            for export in response.get('ExportSummaries', []):
                export_data = {
                    "export_arn": export.get("ExportArn"),
                    "export_status": export.get("ExportStatus"),
                    "export_type": export.get("ExportType"),
                    "export_format": export.get("ExportFormat")
                }
                exports.append(export_data)
            
            return exports
        except Exception as e:
            self.logger.warning(f"Error collecting DynamoDB exports: {e}")
            return []
    
    def _collect_imports(self, client) -> List[Dict[str, Any]]:
        """Collect DynamoDB imports"""
        try:
            imports = []
            
            response = client.list_imports()
            for import_item in response.get('ImportSummaries', []):
                import_data = {
                    "import_arn": import_item.get("ImportArn"),
                    "import_status": import_item.get("ImportStatus"),
                    "table_arn": import_item.get("TableArn"),
                    "cloud_watch_log_group_arn": import_item.get("CloudWatchLogGroupArn"),
                    "input_format": import_item.get("InputFormat"),
                    "start_time": import_item.get("StartTime").isoformat() if import_item.get("StartTime") else None,
                    "end_time": import_item.get("EndTime").isoformat() if import_item.get("EndTime") else None
                }
                imports.append(import_data)
            
            return imports
        except Exception as e:
            self.logger.warning(f"Error collecting DynamoDB imports: {e}")
            return []