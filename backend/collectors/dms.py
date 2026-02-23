"""Database Migration Service collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_dms(session, cost_map):
    dms = session.client("dms", region_name=REGION)
    rows = []

    instances = safe_call(lambda: dms.describe_replication_instances().get("ReplicationInstances", []), [])
    for inst in instances or []:
        rows.append({
            "ResourceType": "ReplicationInstance",
            "Identifier": inst.get("ReplicationInstanceIdentifier"),
            "EngineVersion": inst.get("EngineVersion"),
            "InstanceClass": inst.get("ReplicationInstanceClass"),
            "StorageAllocatedGB": inst.get("AllocatedStorage"),
            "VpcSecurityGroups": ", ".join(sg.get("VpcSecurityGroupId", "") for sg in inst.get("VpcSecurityGroups", [])),
            "State": inst.get("ReplicationInstanceStatus"),
            "AvailabilityZone": inst.get("AvailabilityZone"),
            "MultiAZ": inst.get("MultiAZ"),
            "PubliclyAccessible": inst.get("PubliclyAccessible")
        })

    tasks = safe_call(lambda: dms.describe_replication_tasks().get("ReplicationTasks", []), [])
    for task in tasks or []:
        rows.append({
            "ResourceType": "ReplicationTask",
            "Identifier": task.get("ReplicationTaskIdentifier"),
            "Status": task.get("Status"),
            "MigrationType": task.get("MigrationType"),
            "TaskCreationDate": str(task.get("ReplicationTaskCreationDate")),
            "TableMappings": task.get("TableMappings")
        })

    return pd.DataFrame(rows)
