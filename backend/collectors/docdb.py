"""DocumentDB collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_docdb(session, cost_map):
    doc = session.client("rds", region_name=REGION)
    rows = []
    clusters = safe_call(lambda: doc.describe_db_clusters().get("DBClusters", []), [])
    for c in clusters or []:
        # instance count
        icount = len(c.get("DBClusterMembers", []))
        rows.append({
            "DBClusterIdentifier": c.get("DBClusterIdentifier"),
            "Engine": c.get("Engine"),
            "Status": c.get("Status"),
            "InstanceCount": icount,
            "Endpoint": c.get("Endpoint")
        })
    return pd.DataFrame(rows)
