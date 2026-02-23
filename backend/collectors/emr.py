"""Amazon EMR collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_emr(session, cost_map) -> pd.DataFrame:
    client = session.client("emr", region_name=REGION)
    rows = []

    clusters = safe_call(
        lambda: client.list_clusters().get("Clusters", []), []
    )
    for cl in clusters or []:
        cluster_id = cl.get("Id", "")
        detail = safe_call(
            lambda cid=cluster_id: client.describe_cluster(ClusterId=cid).get("Cluster", {}), {}
        )
        ec2 = detail.get("Ec2InstanceAttributes", {})
        rows.append({
            "ClusterId": cluster_id,
            "ClusterName": cl.get("Name", ""),
            "Status": cl.get("Status", {}).get("State", ""),
            "StatusReason": cl.get("Status", {}).get("StateChangeReason", {}).get("Message", ""),
            "ReleaseLabel": detail.get("ReleaseLabel", ""),
            "InstanceCollectionType": detail.get("InstanceCollectionType", ""),
            "MasterPublicDnsName": detail.get("MasterPublicDnsName", ""),
            "AvailabilityZone": ec2.get("Ec2AvailabilityZone", ""),
            "SubnetId": ec2.get("Ec2SubnetId", ""),
            "LogUri": detail.get("LogUri", ""),
            "AutoTerminate": detail.get("AutoTerminate", ""),
            "TerminationProtected": detail.get("TerminationProtected", ""),
            "CreationDateTime": str(cl.get("Status", {}).get("Timeline", {}).get("CreationDateTime", "") or ""),
        })

    return pd.DataFrame(rows)
