"""Amazon OpenSearch Service collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_opensearch(session, cost_map) -> pd.DataFrame:
    client = session.client("opensearch", region_name=REGION)
    rows = []

    domain_names = safe_call(
        lambda: [d.get("DomainName", "") for d in client.list_domain_names().get("DomainNames", [])], []
    )
    if not domain_names:
        return pd.DataFrame(rows)

    details = safe_call(
        lambda: client.describe_domains(DomainNames=domain_names).get("DomainStatusList", []), []
    )
    for d in details or []:
        cluster_cfg = d.get("ClusterConfig", {})
        ebs_cfg = d.get("EBSOptions", {})
        rows.append({
            "DomainName": d.get("DomainName", ""),
            "DomainId": d.get("DomainId", ""),
            "ARN": d.get("ARN", ""),
            "EngineVersion": d.get("EngineVersion", ""),
            "InstanceType": cluster_cfg.get("InstanceType", ""),
            "InstanceCount": cluster_cfg.get("InstanceCount", ""),
            "DedicatedMasterEnabled": cluster_cfg.get("DedicatedMasterEnabled", ""),
            "DedicatedMasterType": cluster_cfg.get("DedicatedMasterType", ""),
            "EBSEnabled": ebs_cfg.get("EBSEnabled", ""),
            "VolumeType": ebs_cfg.get("VolumeType", ""),
            "VolumeSize": ebs_cfg.get("VolumeSize", ""),
            "Endpoint": d.get("Endpoint", ""),
            "Processing": d.get("Processing", ""),
            "Created": d.get("Created", ""),
            "Deleted": d.get("Deleted", ""),
            "MultiAZ": cluster_cfg.get("ZoneAwarenessEnabled", ""),
        })

    return pd.DataFrame(rows)
