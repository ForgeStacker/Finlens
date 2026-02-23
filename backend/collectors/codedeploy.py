"""AWS CodeDeploy collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_codedeploy(session, cost_map) -> pd.DataFrame:
    client = session.client("codedeploy", region_name=REGION)
    rows = []

    app_names = safe_call(lambda: client.list_applications().get("applications", []), [])
    for app_name in app_names or []:
        detail = safe_call(
            lambda n=app_name: client.get_application(applicationName=n).get("application", {}), {}
        )
        # Deployment groups
        dg_names = safe_call(
            lambda n=app_name: client.list_deployment_groups(applicationName=n).get("deploymentGroups", []), []
        )
        if dg_names:
            for dg_name in dg_names:
                dg = safe_call(
                    lambda an=app_name, dgn=dg_name: client.get_deployment_group(
                        applicationName=an, deploymentGroupName=dgn
                    ).get("deploymentGroupInfo", {}),
                    {},
                )
                rows.append({
                    "ApplicationName": app_name,
                    "ApplicationId": detail.get("applicationId", ""),
                    "ComputePlatform": detail.get("computePlatform", ""),
                    "DeploymentGroupName": dg_name,
                    "DeploymentGroupId": dg.get("deploymentGroupId", ""),
                    "DeploymentConfigName": dg.get("deploymentConfigName", ""),
                    "DeploymentStyle": dg.get("deploymentStyle", {}).get("deploymentType", ""),
                    "ServiceRoleArn": dg.get("serviceRoleArn", ""),
                    "Status": "Active",
                    "CreatedAt": str(detail.get("createTime", "") or ""),
                })
        else:
            rows.append({
                "ApplicationName": app_name,
                "ApplicationId": detail.get("applicationId", ""),
                "ComputePlatform": detail.get("computePlatform", ""),
                "DeploymentGroupName": "",
                "DeploymentGroupId": "",
                "DeploymentConfigName": "",
                "DeploymentStyle": "",
                "ServiceRoleArn": "",
                "Status": "No DeploymentGroups",
                "CreatedAt": str(detail.get("createTime", "") or ""),
            })

    return pd.DataFrame(rows)
