"""AWS CodeCommit collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_codecommit(session, cost_map) -> pd.DataFrame:
    client = session.client("codecommit", region_name=REGION)
    rows = []

    paginator = client.get_paginator("list_repositories")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for repo in page.get("repositories", []):
            name = repo.get("repositoryName", "")
            detail = safe_call(
                lambda n=name: client.get_repository(repositoryName=n).get("repositoryMetadata", {}), {}
            )
            rows.append({
                "RepositoryName": name,
                "RepositoryId": detail.get("repositoryId", ""),
                "ARN": detail.get("Arn", ""),
                "Description": detail.get("repositoryDescription", ""),
                "DefaultBranch": detail.get("defaultBranch", ""),
                "CloneUrlHttp": detail.get("cloneUrlHttp", ""),
                "AccountId": detail.get("accountId", ""),
                "CreationDate": str(detail.get("creationDate", "") or ""),
                "LastModifiedDate": str(detail.get("lastModifiedDate", "") or ""),
            })

    return pd.DataFrame(rows)
