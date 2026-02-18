"""
S3 Collector
Collects AWS S3 bucket information including metadata, policies, and configurations
"""

import json
from typing import Dict, List, Any
from botocore.exceptions import ClientError, NoCredentialsError
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class S3Collector(BaseCollector):
    """S3 service collector for bucket information and configurations"""
    
    category = "storage"
    
    def __init__(self, profile_name: str, region_name: str):
        super().__init__(profile_name, region_name, "s3")
        self.s3_client = None
        
    def initialize_client(self) -> bool:
        """Initialize S3 client"""
        try:
            # Use the parent class initialization which sets self.client
            if not super().initialize_client():
                return False
            self.s3_client = self.client
            return True
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            return False
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect S3 bucket data
        
        Returns:
            Dict containing S3 bucket information
        """
        try:
            if not self.initialize_client():
                return {"error": "Failed to initialize S3 client"}
            
            s3_data = {
                "service": "s3",
                "profile": self.profile_name,
                "region": self.region_name,
                "account_id": self.account_id,
                "scan_timestamp": self.scan_timestamp,
                "buckets": self._collect_buckets(),
                "bucket_policies": {},
                "bucket_encryption": {},
                "bucket_versioning": {},
                "bucket_public_access": {}
            }
            
            # Collect detailed information for each bucket
            for bucket in s3_data["buckets"]:
                bucket_name = bucket["name"]
                s3_data["bucket_policies"][bucket_name] = self._get_bucket_policy(bucket_name)
                s3_data["bucket_encryption"][bucket_name] = self._get_bucket_encryption(bucket_name)
                s3_data["bucket_versioning"][bucket_name] = self._get_bucket_versioning(bucket_name)
                s3_data["bucket_public_access"][bucket_name] = self._get_bucket_public_access_block(bucket_name)
            
            logger.info(f"Successfully collected data for {len(s3_data['buckets'])} S3 buckets")
            return s3_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS Client Error collecting S3 data: {error_code} - {str(e)}")
            return {"error": f"AWS Client Error: {error_code}"}
        except Exception as e:
            logger.error(f"Unexpected error collecting S3 data: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _collect_buckets(self) -> List[Dict[str, Any]]:
        """Collect basic bucket information"""
        try:
            response = self.s3_client.list_buckets()
            buckets = []
            
            for bucket in response.get('Buckets', []):
                bucket_info = {
                    "name": bucket['Name'],
                    "creation_date": bucket['CreationDate'].isoformat() if bucket.get('CreationDate') else None
                }
                
                # Get bucket location
                try:
                    location_response = self.s3_client.get_bucket_location(Bucket=bucket['Name'])
                    bucket_info["region"] = location_response.get('LocationConstraint') or 'us-east-1'
                except ClientError:
                    bucket_info["region"] = "unknown"
                
                # Get bucket size and object count (approximate)
                bucket_info.update(self._get_bucket_metrics(bucket['Name']))
                
                buckets.append(bucket_info)
            
            return buckets
        except ClientError as e:
            logger.error(f"Error listing buckets: {str(e)}")
            return []
    
    def _get_bucket_policy(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket policy"""
        try:
            response = self.s3_client.get_bucket_policy(Bucket=bucket_name)
            return {
                "has_policy": True,
                "policy": json.loads(response['Policy'])
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                return {"has_policy": False, "policy": None}
            else:
                return {"has_policy": "unknown", "error": str(e)}
    
    def _get_bucket_encryption(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket encryption configuration"""
        try:
            response = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
            return {
                "encrypted": True,
                "configuration": response.get('ServerSideEncryptionConfiguration', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                return {"encrypted": False, "configuration": None}
            else:
                return {"encrypted": "unknown", "error": str(e)}
    
    def _get_bucket_versioning(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket versioning status"""
        try:
            response = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
            return {
                "status": response.get('Status', 'Disabled'),
                "mfa_delete": response.get('MfaDelete', 'Disabled')
            }
        except ClientError as e:
            return {"status": "unknown", "error": str(e)}
    
    def _get_bucket_public_access_block(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket public access block configuration"""
        try:
            response = self.s3_client.get_public_access_block(Bucket=bucket_name)
            return {
                "has_public_access_block": True,
                "configuration": response.get('PublicAccessBlockConfiguration', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                return {"has_public_access_block": False, "configuration": None}
            else:
                return {"has_public_access_block": "unknown", "error": str(e)}
    
    def _get_bucket_metrics(self, bucket_name: str) -> Dict[str, Any]:
        """Get bucket size and object count metrics (basic implementation)"""
        try:
            # For a basic implementation, we'll just return placeholder values
            # In a production system, you might use CloudWatch metrics or paginate through objects
            return {
                "estimated_size_bytes": None,
                "estimated_object_count": None,
                "note": "Metrics require CloudWatch or object enumeration"
            }
        except Exception as e:
            logger.warning(f"Could not retrieve metrics for bucket {bucket_name}: {str(e)}")
            return {"estimated_size_bytes": None, "estimated_object_count": None}