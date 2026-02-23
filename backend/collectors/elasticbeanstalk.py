"""AWS Elastic Beanstalk collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_elasticbeanstalk(session, cost_map) -> pd.DataFrame:
    client = session.client("elasticbeanstalk", region_name=REGION)
    rows = []

    apps = safe_call(lambda: client.describe_applications().get("Applications", []), [])
    envs = safe_call(lambda: client.describe_environments().get("Environments", []), [])
    env_by_app: dict[str, list] = {}
    for env in envs or []:
        app_name = env.get("ApplicationName", "")
        env_by_app.setdefault(app_name, []).append(env)

    for app in apps or []:
        app_name = app.get("ApplicationName", "")
        app_envs = env_by_app.get(app_name, [])
        if app_envs:
            for env in app_envs:
                rows.append({
                    "ApplicationName": app_name,
                    "Description": app.get("Description", ""),
                    "EnvironmentName": env.get("EnvironmentName", ""),
                    "EnvironmentId": env.get("EnvironmentId", ""),
                    "PlatformArn": env.get("PlatformArn", ""),
                    "SolutionStackName": env.get("SolutionStackName", ""),
                    "Tier": env.get("Tier", {}).get("Name", ""),
                    "Status": env.get("Status", ""),
                    "Health": env.get("Health", ""),
                    "HealthStatus": env.get("HealthStatus", ""),
                    "CNAME": env.get("CNAME", ""),
                    "DateCreated": str(app.get("DateCreated", "") or ""),
                    "DateUpdated": str(app.get("DateUpdated", "") or ""),
                })
        else:
            rows.append({
                "ApplicationName": app_name,
                "Description": app.get("Description", ""),
                "EnvironmentName": "",
                "EnvironmentId": "",
                "PlatformArn": "",
                "SolutionStackName": "",
                "Tier": "",
                "Status": "No Environments",
                "Health": "",
                "HealthStatus": "",
                "CNAME": "",
                "DateCreated": str(app.get("DateCreated", "") or ""),
                "DateUpdated": str(app.get("DateUpdated", "") or ""),
            })

    return pd.DataFrame(rows)
