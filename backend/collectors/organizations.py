"""AWS Organizations collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_organizations(session, cost_map) -> pd.DataFrame:
    # Organizations API is global, use us-east-1
    client = session.client("organizations", region_name="us-east-1")
    rows = []

    org = safe_call(lambda: client.describe_organization().get("Organization", {}), {})
    if not org:
        return pd.DataFrame(rows)

    # Accounts
    paginator = client.get_paginator("list_accounts")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for acct in page.get("Accounts", []):
            rows.append({
                "AccountId": acct.get("Id", ""),
                "AccountName": acct.get("Name", ""),
                "Email": acct.get("Email", ""),
                "Status": acct.get("Status", ""),
                "JoinedMethod": acct.get("JoinedMethod", ""),
                "JoinedTimestamp": str(acct.get("JoinedTimestamp", "") or ""),
                "OrganizationId": org.get("Id", ""),
                "MasterAccountId": org.get("MasterAccountId", ""),
                "FeatureSet": org.get("FeatureSet", ""),
            })

    return pd.DataFrame(rows)
