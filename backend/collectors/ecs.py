"""Amazon ECS collectors — clusters, services, and task definitions."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_ecs(session, cost_map) -> pd.DataFrame:
    client = session.client("ecs", region_name=REGION)
    rows = []

    cluster_arns = safe_call(lambda: client.list_clusters().get("clusterArns", []), [])
    if not cluster_arns:
        return pd.DataFrame(rows)

    clusters = safe_call(
        lambda: client.describe_clusters(clusters=cluster_arns, include=["STATISTICS", "SETTINGS"]).get("clusters", []), []
    )
    for cluster in clusters or []:
        cluster_arn = cluster.get("clusterArn", "")
        cluster_name = cluster.get("clusterName", "")

        # Services in this cluster
        svc_arns = safe_call(
            lambda ca=cluster_arn: client.list_services(cluster=ca).get("serviceArns", []), []
        )
        services = []
        if svc_arns:
            services = safe_call(
                lambda ca=cluster_arn, sa=svc_arns: client.describe_services(cluster=ca, services=sa).get("services", []), []
            )

        if services:
            for svc in services:
                rows.append({
                    "ClusterName": cluster_name,
                    "ClusterARN": cluster_arn,
                    "ClusterStatus": cluster.get("status", ""),
                    "RunningTasksCount": cluster.get("runningTasksCount", ""),
                    "ActiveServicesCount": cluster.get("activeServicesCount", ""),
                    "ServiceName": svc.get("serviceName", ""),
                    "ServiceARN": svc.get("serviceArn", ""),
                    "ServiceStatus": svc.get("status", ""),
                    "DesiredCount": svc.get("desiredCount", ""),
                    "RunningCount": svc.get("runningCount", ""),
                    "PendingCount": svc.get("pendingCount", ""),
                    "TaskDefinition": (svc.get("taskDefinition") or "").split("/")[-1],
                    "LaunchType": svc.get("launchType", ""),
                    "SchedulingStrategy": svc.get("schedulingStrategy", ""),
                    "CreatedAt": str(svc.get("createdAt", "") or ""),
                })
        else:
            rows.append({
                "ClusterName": cluster_name,
                "ClusterARN": cluster_arn,
                "ClusterStatus": cluster.get("status", ""),
                "RunningTasksCount": cluster.get("runningTasksCount", ""),
                "ActiveServicesCount": cluster.get("activeServicesCount", ""),
                "ServiceName": "",
                "ServiceARN": "",
                "ServiceStatus": "",
                "DesiredCount": "",
                "RunningCount": "",
                "PendingCount": "",
                "TaskDefinition": "",
                "LaunchType": "",
                "SchedulingStrategy": "",
                "CreatedAt": "",
            })

    return pd.DataFrame(rows)
