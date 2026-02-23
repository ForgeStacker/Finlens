"""AWS CodeBuild collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_codebuild(session, cost_map) -> pd.DataFrame:
    client = session.client("codebuild", region_name=REGION)
    rows = []

    project_names = safe_call(lambda: client.list_projects().get("projects", []), [])
    if not project_names:
        return pd.DataFrame(rows)

    # batch_get_projects supports up to 100 at a time
    for i in range(0, len(project_names), 100):
        batch = project_names[i:i + 100]
        projects = safe_call(
            lambda b=batch: client.batch_get_projects(names=b).get("projects", []), []
        )
        for p in projects or []:
            env = p.get("environment", {})
            source = p.get("source", {})
            tags = {t["key"]: t["value"] for t in (p.get("tags") or [])}
            rows.append({
                "ProjectName": p.get("name", ""),
                "ARN": p.get("arn", ""),
                "Description": p.get("description", ""),
                "SourceType": source.get("type", ""),
                "SourceLocation": source.get("location", ""),
                "ComputeType": env.get("computeType", ""),
                "Image": env.get("image", ""),
                "EnvironmentType": env.get("type", ""),
                "ServiceRole": p.get("serviceRole", ""),
                "ArtifactType": p.get("artifacts", {}).get("type", ""),
                "ConcurrentBuildLimit": p.get("concurrentBuildLimit", ""),
                "Created": str(p.get("created", "") or ""),
                "LastModified": str(p.get("lastModified", "") or ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
            })

    return pd.DataFrame(rows)
