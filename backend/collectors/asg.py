"""Auto Scaling Group collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_asg(session, cost_map) -> pd.DataFrame:
    client = session.client("autoscaling", region_name=REGION)
    rows = []

    paginator = client.get_paginator("describe_auto_scaling_groups")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for asg in page.get("AutoScalingGroups", []):
            tags = {t["Key"]: t["Value"] for t in (asg.get("Tags") or [])}
            instance_types = list({
                i.get("InstanceType", "") for i in asg.get("Instances", []) if i.get("InstanceType")
            })
            lt = asg.get("LaunchTemplate", {})
            lc = asg.get("LaunchConfigurationName", "")
            rows.append({
                "AutoScalingGroupName": asg.get("AutoScalingGroupName", ""),
                "ARN": asg.get("AutoScalingGroupARN", ""),
                "Status": asg.get("Status", "Active"),
                "MinSize": asg.get("MinSize", ""),
                "MaxSize": asg.get("MaxSize", ""),
                "DesiredCapacity": asg.get("DesiredCapacity", ""),
                "RunningInstances": sum(
                    1 for i in asg.get("Instances", []) if i.get("LifecycleState") == "InService"
                ),
                "InstanceTypes": ", ".join(instance_types),
                "LaunchTemplate": lt.get("LaunchTemplateName") or lt.get("LaunchTemplateId") or lc,
                "AvailabilityZones": ", ".join(asg.get("AvailabilityZones", [])),
                "VPCZoneIdentifier": asg.get("VPCZoneIdentifier", ""),
                "HealthCheckType": asg.get("HealthCheckType", ""),
                "TerminationPolicies": ", ".join(asg.get("TerminationPolicies", [])),
                "CreatedTime": str(asg.get("CreatedTime", "") or ""),
                "Tags": ", ".join(f"{k}={v}" for k, v in tags.items()),
            })

    return pd.DataFrame(rows)
