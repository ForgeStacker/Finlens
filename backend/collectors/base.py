"""
Base Collector
Abstract base class for all AWS service collectors
Implements CMMI Level 5 standardization and quality controls
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from backend.utils.logger import get_logger, log_operation
from backend.utils.aws_client import get_aws_client

logger = get_logger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for AWS service collectors
    All service collectors must inherit from this class
    """
    
    # Class-level category attribute (to be set by subclasses)
    category: str = "general"
    
    def __init__(
        self,
        profile_name: str,
        region_name: str,
        service_name: str
    ):
        """
        Initialize collector
        
        Args:
            profile_name: AWS profile name
            region_name: AWS region name
            service_name: AWS service name (e.g., 'ec2', 'vpc')
        """
        self.profile_name = profile_name
        self.region_name = region_name
        self.service_name = service_name
        self.client = None
        self.session = None
        self.account_id = None
        self.scan_timestamp = datetime.utcnow().isoformat()
        
    def initialize_client(self) -> bool:
        """
        Initialize AWS client for the service
        
        Returns:
            True if successful, False otherwise
        """
        try:
            log_operation(
                f"{self.service_name.upper()}_COLLECTOR",
                "START",
                f"Profile: {self.profile_name}, Region: {self.region_name}"
            )
            
            # Create boto3 session
            import boto3
            self.session = boto3.Session(
                profile_name=self.profile_name,
                region_name=self.region_name
            )
            
            # Get account ID
            try:
                sts = self.session.client('sts')
                self.account_id = sts.get_caller_identity()['Account']
            except:
                self.account_id = 'unknown'
            
            self.client = get_aws_client(
                self.service_name,
                self.profile_name,
                self.region_name
            )
            
            if not self.client:
                logger.error(
                    f"Failed to create {self.service_name} client "
                    f"for {self.profile_name} in {self.region_name}"
                )
                return False
            
            logger.info(f"{self.service_name.upper()} client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing {self.service_name} client: {e}")
            return False
    
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """
        Collect data from AWS service
        Must be implemented by subclasses
        
        Returns:
            Dictionary containing collected data in standardized format
        """
        pass
    
    def _build_response_structure(
        self,
        resources: List[Dict[str, Any]],
        summary: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build standardized response structure
        
        Args:
            resources: List of resource dictionaries
            summary: Optional summary statistics
            metadata: Optional additional metadata
            
        Returns:
            Standardized response dictionary
        """
        response = {
            "schema_version": "1.0.0",
            "generated_at": self.scan_timestamp,
            "service": {
                "service_name": self.service_name,
                "region": self.region_name,
                "profile": self.profile_name,
            },
            "summary": summary or {
                "resource_count": len(resources),
                "scan_status": "success"
            },
            "resources": resources
        }
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    def save_to_file(self, data: Dict[str, Any], output_dir: Path) -> bool:
        """
        Save collected data to JSON file
        
        Args:
            data: Data to save
            output_dir: Output directory path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create output directory structure
            # data/{profile}/regions/{region}/services/{category}/{service}.json
            category_dir = (
                output_dir
                / self.profile_name
                / 'regions'
                / self.region_name
                / 'services'
                / self.category
            )
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Use collector_name if available (for VPC, etc), otherwise use service_name
            file_name = getattr(self, 'collector_name', self.service_name)
            output_file = category_dir / f"{file_name}.json"
            
            logger.info(f"Saving {file_name} data to: {output_file}")
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            log_operation(
                f"{file_name.upper()}_SAVE",
                "SUCCESS",
                f"File: {output_file}"
            )
            
            return True
            
        except Exception as e:
            file_name = getattr(self, 'collector_name', self.service_name)
            log_operation(
                f"{file_name.upper()}_SAVE",
                "FAILED",
                str(e)
            )
            return False
    
    def run(self, output_dir: Path) -> bool:
        """
        Execute full collection workflow
        
        Args:
            output_dir: Directory to save output files
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize client
            if not self.initialize_client():
                return False
            
            # Collect data
            logger.info(f"Collecting {self.service_name} data...")
            data = self.collect()
            
            if not data:
                logger.warning(f"No data collected for {self.service_name}")
                # Still save empty structure
                data = self._build_response_structure([])
            
            # Save to file
            success = self.save_to_file(data, output_dir)
            
            if success:
                log_operation(
                    f"{self.service_name.upper()}_COLLECTOR",
                    "SUCCESS",
                    f"Resources: {len(data.get('resources', []))}"
                )
            else:
                log_operation(
                    f"{self.service_name.upper()}_COLLECTOR",
                    "FAILED",
                    "Could not save data"
                )
            
            return success
            
        except Exception as e:
            log_operation(
                f"{self.service_name.upper()}_COLLECTOR",
                "FAILED",
                str(e)
            )
            return False
    
    def _handle_api_error(self, operation: str, error: Exception) -> None:
        """
        Handle AWS API errors consistently
        
        Args:
            operation: Name of the operation that failed
            error: Exception that occurred
        """
        logger.error(
            f"AWS API error in {self.service_name}.{operation}: "
            f"{type(error).__name__} - {str(error)}"
        )
    
    def _paginate_results(
        self,
        method_name: str,
        result_key: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Helper method to paginate AWS API results
        
        Args:
            method_name: Name of the boto3 client method
            result_key: Key in response containing the list of items
            **kwargs: Additional arguments to pass to the method
            
        Returns:
            List of all paginated results
        """
        results = []
        
        try:
            paginator = self.client.get_paginator(method_name)
            
            for page in paginator.paginate(**kwargs):
                if result_key in page:
                    results.extend(page[result_key])
            
            logger.debug(
                f"Paginated {len(results)} items from {method_name}"
            )
            
        except Exception as e:
            self._handle_api_error(method_name, e)
        
        return results
