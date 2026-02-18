"""
IAM Collector
Collects AWS Identity and Access Management information including users, roles, policies
"""

import json
from typing import Dict, List, Any
from botocore.exceptions import ClientError, NoCredentialsError
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class IAMCollector(BaseCollector):
    """IAM service collector for identity and access management information"""
    
    category = "security"
    
    def __init__(self, profile_name: str, region_name: str):
        super().__init__(profile_name, region_name, "iam")
        self.iam_client = None
        
    def initialize_client(self) -> bool:
        """Initialize IAM client"""
        try:
            # Use the parent class initialization which sets self.client
            if not super().initialize_client():
                return False
            self.iam_client = self.client
            return True
        except Exception as e:
            logger.error(f"Failed to initialize IAM client: {str(e)}")
            return False
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect IAM data
        
        Returns:
            Dict containing IAM information
        """
        try:
            if not self.initialize_client():
                return {"error": "Failed to initialize IAM client"}
            
            iam_data = {
                "service": "iam",
                "profile": self.profile_name,
                "region": self.region_name,
                "account_id": self.account_id,
                "scan_timestamp": self.scan_timestamp,
                "users": self._collect_users(),
                "roles": self._collect_roles(),
                "groups": self._collect_groups(),
                "policies": self._collect_policies(),
                "access_keys": self._collect_access_keys(),
                "password_policy": self._get_password_policy(),
                "account_summary": self._get_account_summary()
            }
            
            logger.info(f"Successfully collected IAM data: "
                       f"{len(iam_data['users'])} users, "
                       f"{len(iam_data['roles'])} roles, "
                       f"{len(iam_data['policies'])} policies")
            return iam_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS Client Error collecting IAM data: {error_code} - {str(e)}")
            return {"error": f"AWS Client Error: {error_code}"}
        except Exception as e:
            logger.error(f"Unexpected error collecting IAM data: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _collect_users(self) -> List[Dict[str, Any]]:
        """Collect IAM users"""
        try:
            users = []
            paginator = self.iam_client.get_paginator('list_users')
            
            for page in paginator.paginate():
                for user in page.get('Users', []):
                    user_data = {
                        "user_name": user['UserName'],
                        "user_id": user['UserId'],
                        "arn": user['Arn'],
                        "path": user['Path'],
                        "create_date": user['CreateDate'].isoformat() if user.get('CreateDate') else None,
                        "password_last_used": user.get('PasswordLastUsed').isoformat() if user.get('PasswordLastUsed') else None,
                        "permissions_boundary": user.get('PermissionsBoundary'),
                        "tags": user.get('Tags', [])
                    }
                    
                    # Get attached policies
                    user_data["attached_policies"] = self._get_user_policies(user['UserName'])
                    users.append(user_data)
            
            return users
        except ClientError as e:
            logger.error(f"Error collecting IAM users: {str(e)}")
            return []
    
    def _collect_roles(self) -> List[Dict[str, Any]]:
        """Collect IAM roles"""
        try:
            roles = []
            paginator = self.iam_client.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page.get('Roles', []):
                    role_data = {
                        "role_name": role['RoleName'],
                        "role_id": role['RoleId'],
                        "arn": role['Arn'],
                        "path": role['Path'],
                        "create_date": role['CreateDate'].isoformat() if role.get('CreateDate') else None,
                        "assume_role_policy_document": role.get('AssumeRolePolicyDocument'),
                        "max_session_duration": role.get('MaxSessionDuration'),
                        "permissions_boundary": role.get('PermissionsBoundary'),
                        "tags": role.get('Tags', [])
                    }
                    
                    # Get attached policies
                    role_data["attached_policies"] = self._get_role_policies(role['RoleName'])
                    roles.append(role_data)
            
            return roles
        except ClientError as e:
            logger.error(f"Error collecting IAM roles: {str(e)}")
            return []
    
    def _collect_groups(self) -> List[Dict[str, Any]]:
        """Collect IAM groups"""
        try:
            groups = []
            paginator = self.iam_client.get_paginator('list_groups')
            
            for page in paginator.paginate():
                for group in page.get('Groups', []):
                    group_data = {
                        "group_name": group['GroupName'],
                        "group_id": group['GroupId'],
                        "arn": group['Arn'],
                        "path": group['Path'],
                        "create_date": group['CreateDate'].isoformat() if group.get('CreateDate') else None
                    }
                    
                    # Get attached policies and members
                    group_data["attached_policies"] = self._get_group_policies(group['GroupName'])
                    group_data["members"] = self._get_group_members(group['GroupName'])
                    groups.append(group_data)
            
            return groups
        except ClientError as e:
            logger.error(f"Error collecting IAM groups: {str(e)}")
            return []
    
    def _collect_policies(self) -> List[Dict[str, Any]]:
        """Collect IAM customer-managed policies"""
        try:
            policies = []
            paginator = self.iam_client.get_paginator('list_policies')
            
            for page in paginator.paginate(Scope='Local'):  # Only customer-managed policies
                for policy in page.get('Policies', []):
                    policy_data = {
                        "policy_name": policy['PolicyName'],
                        "policy_id": policy['PolicyId'],
                        "arn": policy['Arn'],
                        "path": policy['Path'],
                        "default_version_id": policy['DefaultVersionId'],
                        "attachment_count": policy.get('AttachmentCount', 0),
                        "permissions_boundary_usage_count": policy.get('PermissionsBoundaryUsageCount', 0),
                        "is_attachable": policy.get('IsAttachable', False),
                        "create_date": policy['CreateDate'].isoformat() if policy.get('CreateDate') else None,
                        "update_date": policy['UpdateDate'].isoformat() if policy.get('UpdateDate') else None
                    }
                    
                    # Get policy document
                    try:
                        version_response = self.iam_client.get_policy_version(
                            PolicyArn=policy['Arn'],
                            VersionId=policy['DefaultVersionId']
                        )
                        policy_data["policy_document"] = version_response['PolicyVersion']['Document']
                    except ClientError as e:
                        policy_data["policy_document"] = None
                        logger.warning(f"Could not get policy document for {policy['PolicyName']}: {str(e)}")
                    
                    policies.append(policy_data)
            
            return policies
        except ClientError as e:
            logger.error(f"Error collecting IAM policies: {str(e)}")
            return []
    
    def _collect_access_keys(self) -> List[Dict[str, Any]]:
        """Collect access keys for all users"""
        try:
            access_keys = []
            
            # Get users first
            paginator = self.iam_client.get_paginator('list_users')
            for page in paginator.paginate():
                for user in page.get('Users', []):
                    user_name = user['UserName']
                    
                    # Get access keys for each user
                    try:
                        keys_response = self.iam_client.list_access_keys(UserName=user_name)
                        for key in keys_response.get('AccessKeyMetadata', []):
                            access_key_data = {
                                "user_name": user_name,
                                "access_key_id": key['AccessKeyId'],
                                "status": key['Status'],
                                "create_date": key['CreateDate'].isoformat() if key.get('CreateDate') else None
                            }
                            access_keys.append(access_key_data)
                    except ClientError as e:
                        logger.warning(f"Could not get access keys for user {user_name}: {str(e)}")
            
            return access_keys
        except ClientError as e:
            logger.error(f"Error collecting access keys: {str(e)}")
            return []
    
    def _get_user_policies(self, user_name: str) -> Dict[str, List]:
        """Get attached policies for a user"""
        try:
            policies = {"managed": [], "inline": []}
            
            # Managed policies
            response = self.iam_client.list_attached_user_policies(UserName=user_name)
            policies["managed"] = response.get('AttachedPolicies', [])
            
            # Inline policies
            response = self.iam_client.list_user_policies(UserName=user_name)
            policies["inline"] = response.get('PolicyNames', [])
            
            return policies
        except ClientError:
            return {"managed": [], "inline": []}
    
    def _get_role_policies(self, role_name: str) -> Dict[str, List]:
        """Get attached policies for a role"""
        try:
            policies = {"managed": [], "inline": []}
            
            # Managed policies
            response = self.iam_client.list_attached_role_policies(RoleName=role_name)
            policies["managed"] = response.get('AttachedPolicies', [])
            
            # Inline policies
            response = self.iam_client.list_role_policies(RoleName=role_name)
            policies["inline"] = response.get('PolicyNames', [])
            
            return policies
        except ClientError:
            return {"managed": [], "inline": []}
    
    def _get_group_policies(self, group_name: str) -> Dict[str, List]:
        """Get attached policies for a group"""
        try:
            policies = {"managed": [], "inline": []}
            
            # Managed policies
            response = self.iam_client.list_attached_group_policies(GroupName=group_name)
            policies["managed"] = response.get('AttachedPolicies', [])
            
            # Inline policies
            response = self.iam_client.list_group_policies(GroupName=group_name)
            policies["inline"] = response.get('PolicyNames', [])
            
            return policies
        except ClientError:
            return {"managed": [], "inline": []}
    
    def _get_group_members(self, group_name: str) -> List[str]:
        """Get members of a group"""
        try:
            response = self.iam_client.get_group(GroupName=group_name)
            return [user['UserName'] for user in response.get('Users', [])]
        except ClientError:
            return []
    
    def _get_password_policy(self) -> Dict[str, Any]:
        """Get account password policy"""
        try:
            response = self.iam_client.get_account_password_policy()
            return response.get('PasswordPolicy', {})
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                return {"has_password_policy": False}
            else:
                return {"error": str(e)}
    
    def _get_account_summary(self) -> Dict[str, Any]:
        """Get account summary information"""
        try:
            response = self.iam_client.get_account_summary()
            return response.get('SummaryMap', {})
        except ClientError as e:
            logger.error(f"Error getting account summary: {str(e)}")
            return {"error": str(e)}