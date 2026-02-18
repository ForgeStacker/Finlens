"""
AWS Client Utility
Manages AWS session creation and client instantiation
Following CMMI Level 5 security and reliability standards
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from typing import Optional, Dict, Any
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AWSClientManager:
    """
    Manages AWS session and client creation
    Implements singleton pattern for session reuse
    """
    
    def __init__(self):
        """Initialize AWS Client Manager"""
        self._sessions: Dict[str, boto3.Session] = {}
        self._clients: Dict[str, Any] = {}
    
    def create_session(
        self, 
        profile_name: str, 
        region_name: Optional[str] = None
    ) -> Optional[boto3.Session]:
        """
        Create AWS session for given profile and region
        
        Args:
            profile_name: AWS profile name from ~/.aws/credentials
            region_name: AWS region name (optional)
            
        Returns:
            boto3.Session object or None if failed
            
        Raises:
            ProfileNotFound: If profile doesn't exist
            NoCredentialsError: If credentials not configured
        """
        session_key = f"{profile_name}:{region_name or 'default'}"
        
        # Return cached session if exists
        if session_key in self._sessions:
            logger.debug(f"Reusing session for {session_key}")
            return self._sessions[session_key]
        
        try:
            logger.info(f"Creating AWS session - Profile: {profile_name}, Region: {region_name}")
            
            session = boto3.Session(
                profile_name=profile_name,
                region_name=region_name
            )
            
            # Validate session by attempting to get caller identity
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            
            logger.info(
                f"Session created successfully - "
                f"Account: {identity['Account']}, "
                f"UserId: {identity['UserId']}"
            )
            
            # Cache session
            self._sessions[session_key] = session
            return session
            
        except ProfileNotFound:
            logger.error(f"AWS profile '{profile_name}' not found in ~/.aws/credentials")
            raise
        except NoCredentialsError:
            logger.error("No AWS credentials configured. Please run 'aws configure'")
            raise
        except ClientError as e:
            logger.error(f"AWS client error during session creation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating AWS session: {e}")
            raise
    
    def get_client(
        self,
        service_name: str,
        profile_name: str,
        region_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get AWS service client for specific service
        
        Args:
            service_name: AWS service name (e.g., 'ec2', 'vpc')
            profile_name: AWS profile name
            region_name: AWS region name (optional)
            
        Returns:
            boto3 client object or None if failed
        """
        client_key = f"{profile_name}:{region_name or 'default'}:{service_name}"
        
        # Return cached client if exists
        if client_key in self._clients:
            logger.debug(f"Reusing client for {client_key}")
            return self._clients[client_key]
        
        try:
            session = self.create_session(profile_name, region_name)
            if not session:
                return None
            
            logger.debug(f"Creating {service_name} client for {profile_name} in {region_name}")
            client = session.client(service_name)
            
            # Cache client
            self._clients[client_key] = client
            return client
            
        except Exception as e:
            logger.error(f"Failed to create {service_name} client: {e}")
            return None
    
    def get_available_regions(
        self, 
        service_name: str,
        profile_name: str = 'default'
    ) -> list:
        """
        Get list of available regions for a service
        
        Args:
            service_name: AWS service name
            profile_name: AWS profile name
            
        Returns:
            List of region names
        """
        try:
            session = self.create_session(profile_name)
            if not session:
                return []
            
            regions = session.get_available_regions(service_name)
            logger.debug(f"Available regions for {service_name}: {len(regions)}")
            return regions
            
        except Exception as e:
            logger.error(f"Failed to get available regions: {e}")
            return []
    
    def validate_credentials(self, profile_name: str) -> bool:
        """
        Validate AWS credentials for a profile
        
        Args:
            profile_name: AWS profile name
            
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            session = self.create_session(profile_name)
            if session:
                logger.info(f"Credentials validated for profile: {profile_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Credential validation failed for {profile_name}: {e}")
            return False
    
    def clear_cache(self):
        """Clear all cached sessions and clients"""
        self._sessions.clear()
        self._clients.clear()
        logger.info("AWS client cache cleared")


# Global instance
_aws_client_manager = AWSClientManager()


def get_aws_client(
    service_name: str,
    profile_name: str,
    region_name: Optional[str] = None
) -> Optional[Any]:
    """
    Convenience function to get AWS client
    
    Args:
        service_name: AWS service name
        profile_name: AWS profile name
        region_name: AWS region name
        
    Returns:
        boto3 client or None
    """
    return _aws_client_manager.get_client(service_name, profile_name, region_name)


def validate_aws_credentials(profile_name: str) -> bool:
    """
    Convenience function to validate credentials
    
    Args:
        profile_name: AWS profile name
        
    Returns:
        True if valid, False otherwise
    """
    return _aws_client_manager.validate_credentials(profile_name)
