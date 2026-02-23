"""Collect IAM user metadata for inventory output."""
from __future__ import annotations

import pandas as pd
from botocore.exceptions import ClientError


def collect_iam(session, cost_map) -> pd.DataFrame:  # cost_map kept for signature compatibility
    iam = session.client("iam")
    users: list[dict] = []

    paginator = iam.get_paginator("list_users")
    for page in paginator.paginate():
        for user in page.get("Users", []):
            user_name = user.get("UserName", "")

            # Console access: presence of a login profile
            console_access = "Enabled"
            try:
                iam.get_login_profile(UserName=user_name)
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") == "NoSuchEntity":
                    console_access = "Disabled"
                else:
                    console_access = f"Error: {exc.response.get('Error', {}).get('Code', 'Unknown')}"
            except Exception as exc:  # pragma: no cover - diagnostic
                console_access = f"Error: {type(exc).__name__}"

            # Access keys (up to two)
            key_entries: list[str] = []
            try:
                keys = iam.list_access_keys(UserName=user_name).get("AccessKeyMetadata", [])
                keys = sorted(keys, key=lambda k: k.get("CreateDate"))
                for key in keys[:2]:
                    key_entries.append(f"{key.get('AccessKeyId', '')} ({key.get('Status', '')})")
            except Exception:
                pass
            while len(key_entries) < 2:
                key_entries.append("")

            # Policies (attached + inline)
            policy_names: list[str] = []
            try:
                attached = iam.list_attached_user_policies(UserName=user_name).get("AttachedPolicies", [])
                policy_names.extend(p.get("PolicyName", "") for p in attached)
            except Exception:
                pass
            try:
                inline = iam.list_user_policies(UserName=user_name).get("PolicyNames", [])
                policy_names.extend(inline)
            except Exception:
                pass
            policies_str = "\n".join([p for p in policy_names if p])

            # Groups
            group_names = ""
            try:
                groups = iam.list_groups_for_user(UserName=user_name).get("Groups", [])
                group_names = "\n".join(g.get("GroupName", "") for g in groups if g.get("GroupName"))
            except Exception:
                pass

            users.append(
                {
                    "UserName": user_name,
                    "ConsoleAccess": console_access,
                    "AccessKey1": key_entries[0],
                    "AccessKey2": key_entries[1],
                    "PolicyNames": policies_str,
                    "GroupNames": group_names,
                }
            )

    return pd.DataFrame(users)
