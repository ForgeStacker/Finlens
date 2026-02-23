"""Elastic Load Balancer collectors.

Augments ALB/NLB rows with 24h LCU usage and processed-bytes rate metrics:
- AvgConsumedLCU_24h, MaxConsumedLCU_24h
- AvgProcessedGBph_24h, MaxProcessedGBph_24h
"""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION
from datetime import datetime, timedelta, timezone


def collect_elb(session, cost_map):
    elb = session.client("elbv2", region_name=REGION)
    cw = session.client("cloudwatch", region_name=REGION)
    rows = []
    lbs = safe_call(lambda: elb.describe_load_balancers().get("LoadBalancers", []), [])
    for lb in lbs or []:
        tgs = safe_call(lambda: elb.describe_target_groups(LoadBalancerArn=lb.get("LoadBalancerArn")).get("TargetGroups", []), [])
        tg_arn_to_name = {tg.get("TargetGroupArn"): tg.get("TargetGroupName") for tg in tgs}
        tg_summ = []
        for tg in tgs or []:
            tg_summ.append({
                "Name": tg.get("TargetGroupName"),
                "Protocol": tg.get("Protocol"),
                "Port": tg.get("Port"),
                "TargetType": tg.get("TargetType")
            })
        tags = safe_call(lambda: elb.describe_tags(ResourceArns=[lb.get("LoadBalancerArn")]).get("TagDescriptions", []), [])
        cluster_associated = None
        for td in tags or []:
            for t in td.get("Tags", []):
                k = t.get("Key", "")
                if k.startswith("kubernetes.io/cluster/"):
                    cluster_associated = k.split("/", 1)[1] or t.get("Value")
        listeners = safe_call(lambda: elb.describe_listeners(LoadBalancerArn=lb.get("LoadBalancerArn")).get("Listeners", []), [])
        listener_ports = []
        target_group_names = []
        target_ids = []
        for listener in listeners:
            port = str(listener.get("Port"))
            listener_ports.append(port)
            for action in listener.get("DefaultActions", []):
                tg_arn = action.get("TargetGroupArn")
                if not tg_arn:
                    continue
                tg_name = tg_arn_to_name.get(tg_arn)
                if tg_name:
                    target_group_names.append(tg_name)
                targets = safe_call(lambda arn=tg_arn: elb.describe_target_health(TargetGroupArn=arn).get("TargetHealthDescriptions", []), [])
                for t in targets:
                    target_id = t.get("Target", {}).get("Id")
                    if target_id:
                        target_ids.append(target_id)
        security_groups = ", ".join(lb.get("SecurityGroups", [])) if "SecurityGroups" in lb else ""
        deletion_protection = lb.get("DeletionProtection", False)
        azs = [az.get("ZoneName") for az in lb.get("AvailabilityZones", [])]
        subnets = [az.get("SubnetId") for az in lb.get("AvailabilityZones", [])]
        # CloudWatch metrics (24h window, hourly period)
        avg_lcu = None
        max_lcu = None
        avg_gbph = None
        max_gbph = None
        try:
            lb_type = lb.get("Type")
            lb_arn = lb.get("LoadBalancerArn", "")
            # For ALB/NLB, CloudWatch dimension LoadBalancer is ARN suffix after 'loadbalancer/'
            dim_val = lb_arn.split("loadbalancer/", 1)[-1] if "loadbalancer/" in lb_arn else None
            if dim_val and lb_type in ("application", "network"):
                if lb_type == "application":
                    namespace = "AWS/ApplicationELB"
                else:
                    namespace = "AWS/NetworkELB"
                end = datetime.now(timezone.utc)
                start = end - timedelta(hours=24)
                period = 3600
                # ConsumedLCUs: take average of hourly averages, and maximum of hourly maximums
                lcu_dp = safe_call(lambda: cw.get_metric_statistics(
                    Namespace=namespace,
                    MetricName="ConsumedLCUs",
                    Dimensions=[{"Name": "LoadBalancer", "Value": dim_val}],
                    StartTime=start,
                    EndTime=end,
                    Period=period,
                    Statistics=["Average", "Maximum"],
                ).get("Datapoints", []), []) or []
                if lcu_dp:
                    # average of hourly Average values
                    avg_vals = [d.get("Average", 0) or 0 for d in lcu_dp]
                    max_vals = [d.get("Maximum", 0) or 0 for d in lcu_dp]
                    if avg_vals:
                        avg_lcu = sum(avg_vals) / float(len(avg_vals))
                    if max_vals:
                        max_lcu = max(max_vals)
                # ProcessedBytes -> convert to GB per hour for Avg/Max
                bytes_dp = safe_call(lambda: cw.get_metric_statistics(
                    Namespace=namespace,
                    MetricName="ProcessedBytes",
                    Dimensions=[{"Name": "LoadBalancer", "Value": dim_val}],
                    StartTime=start,
                    EndTime=end,
                    Period=period,
                    Statistics=["Sum", "Maximum"],
                ).get("Datapoints", []), []) or []
                if bytes_dp:
                    sums = [d.get("Sum", 0) or 0 for d in bytes_dp]
                    max_bytes = 0
                    for d in bytes_dp:
                        v = (d.get("Maximum", 0) or 0)
                        if v > max_bytes:
                            max_bytes = v
                    if sums:
                        # average bytes per period to bytes/hour, then GB
                        avg_bytes_per_period = sum(sums) / float(len(sums))
                        avg_bytes_per_hour = (avg_bytes_per_period / period) * 3600.0
                        avg_gbph = avg_bytes_per_hour / (1024.0 ** 3)
                    if max_bytes:
                        max_bytes_per_hour = (max_bytes / period) * 3600.0
                        max_gbph = max_bytes_per_hour / (1024.0 ** 3)
        except Exception:
            pass

        rows.append({
            "LoadBalancerName": lb.get("LoadBalancerName"),
            "Type": lb.get("Type"),
            "Scheme": lb.get("Scheme"),
            "DNSName": lb.get("DNSName"),
            "AZs": ", ".join(azs),
            "Subnets": ", ".join(subnets),
            "Listeners": ", ".join(listener_ports),
            "TargetGroups": ", ".join(target_group_names),
            "Targets": ", ".join(target_ids),
            "SecurityGroups": security_groups,
            "DeletionProtection": deletion_protection,
            "AssociatedCluster": cluster_associated,
            "AvgConsumedLCU_24h": (round(avg_lcu, 6) if isinstance(avg_lcu, (int, float)) else None),
            "MaxConsumedLCU_24h": (round(max_lcu, 6) if isinstance(max_lcu, (int, float)) else None),
            "AvgProcessedGBph_24h": (round(avg_gbph, 6) if isinstance(avg_gbph, (int, float)) else None),
            "MaxProcessedGBph_24h": (round(max_gbph, 6) if isinstance(max_gbph, (int, float)) else None),
        })
    return pd.DataFrame(rows)
