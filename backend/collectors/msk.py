"""Amazon MSK collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_msk(session, cost_map):
    kafka = session.client("kafka", region_name=REGION)
    rows = []
    clusters = safe_call(lambda: kafka.list_clusters().get("ClusterInfoList", []), [])
    for cluster in clusters or []:
        rows.append(
            {
                "ClusterName": cluster.get("ClusterName"),
                "State": cluster.get("State"),
                "KafkaVersion": cluster.get("CurrentBrokerSoftwareInfo", {}).get("KafkaVersion"),
                "NumberOfBrokerNodes": cluster.get("NumberOfBrokerNodes"),
                "ZookeeperConnectString": cluster.get("ZookeeperConnectString", ""),
            }
        )
    return pd.DataFrame(rows)
