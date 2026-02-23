"""EC2 collectors."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from aws_utils import get_instance_type_specs, safe_call
from config import REGION


def _fetch_ec2_cost_per_instance(session) -> dict[str, float]:
    """Fetch per-EC2-instance monthly cost from Cost Explorer (14-day DAILY window scaled to 30 days).

    Returns {instance_id: estimated_monthly_cost_usd}. Falls back to {} on any error.
    """
    from datetime import date, timedelta as td
    try:
        ce = session.client("ce", region_name="us-east-1")
        end_date = date.today()
        start_date = end_date - td(days=14)
        resp = ce.get_cost_and_usage_with_resources(
            TimePeriod={"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            Filter={"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}},
            GroupBy=[{"Type": "DIMENSION", "Key": "RESOURCE_ID"}],
        )
        cost_by_id: dict[str, float] = {}
        for period in resp.get("ResultsByTime", []):
            for grp in period.get("Groups", []):
                rid  = grp["Keys"][0]
                cost = float(grp["Metrics"]["UnblendedCost"]["Amount"])
                cost_by_id[rid] = cost_by_id.get(rid, 0.0) + cost
        scale = 30.0 / 14.0
        # Only real instance IDs (i-xxxx)
        return {k: round(v * scale, 2) for k, v in cost_by_id.items() if k.startswith("i-")}
    except Exception:
        return {}


def _fetch_ec2_cpu_metrics(cloudwatch_client, instance_ids: list[str]) -> dict[str, dict]:
    """Fetch CPUUtilization (avg + max) and NetworkIn/Out (avg) for each instance over the last 30 days.

    Uses a daily period (86400 s) so each datapoint represents one full day.
    CloudWatch stores 1-hour resolution for up to 455 days, so a 30-day window
    with 86400 s granularity gives 30 representative daily averages.

    Returns {instance_id: {cpu_avg, cpu_max, net_in_mb_avg, net_out_mb_avg}}.
    """
    end_time   = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=30)
    # Daily granularity → 30 datapoints per metric; valid for CW extended retention
    CW_PERIOD = 86400
    result: dict[str, dict] = {}

    for inst_id in instance_ids:
        row: dict = {}
        for metric, stat, key, divisor in [
            ("CPUUtilization",  "Average", "cpu_avg",        1.0),
            ("CPUUtilization",  "Maximum", "cpu_max",        1.0),
            ("NetworkIn",       "Average", "net_in_mb_avg",  1024 * 1024),
            ("NetworkOut",      "Average", "net_out_mb_avg", 1024 * 1024),
        ]:
            resp = safe_call(
                lambda m=metric, s=stat, iid=inst_id: cloudwatch_client.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName=m,
                    Dimensions=[{"Name": "InstanceId", "Value": iid}],
                    Statistics=[s],
                    Period=CW_PERIOD,
                    StartTime=start_time,
                    EndTime=end_time,
                ),
                {},
            )
            pts = resp.get("Datapoints", []) if isinstance(resp, dict) else []
            if pts:
                row[key] = round(sum(dp.get(stat, 0.0) for dp in pts) / len(pts) / divisor, 3)
            else:
                row[key] = None
        result[inst_id] = row
    return result


def _ec2_optimization_status(state: str, cpu_avg) -> str:
    """Derive optimization status from instance state and CPU average."""
    if state in ("stopped", "stopping"):
        return "Stopped"
    if cpu_avg is None:
        return "No Data"
    if cpu_avg < 10:
        return "Idle"
    if cpu_avg < 30:
        return "Low Use"
    if cpu_avg <= 85:
        return "Balanced"
    return "High Load"


def _calculate_ec2_savings(current_cost: float, cpu_avg, optimization_status: str) -> float:
    """Estimate monthly savings based on optimization status and CPU average.

    Stopped  → 80% savings (compute stops; EBS remains).
    Idle     → 70% savings on compute portion (×0.65 compute factor).
    Low Use  → proportional downsize savings (one tier, max 50%) ×0.65.
    Others   → $0.
    """
    if current_cost <= 0:
        return 0.0
    if optimization_status == "Stopped":
        return round(current_cost * 0.80, 2)
    if optimization_status == "Idle":
        return round(current_cost * 0.70 * 0.65, 2)
    if optimization_status == "Low Use":
        if not isinstance(cpu_avg, (int, float)):
            return 0.0
        raw_frac = 1.0 - (cpu_avg / 100.0) / 0.70
        savings_frac = max(0.0, min(raw_frac, 0.50))
        return round(current_cost * savings_frac * 0.65, 2)
    return 0.0


def collect_ec2(session, cost_map):
    ec2 = session.client("ec2", region_name=REGION)
    cloudwatch = session.client("cloudwatch", region_name=REGION)
    try:
        iam_client = session.client("iam")
    except Exception:
        iam_client = None
    try:
        elbv2 = session.client("elbv2", region_name=REGION)
    except Exception:
        elbv2 = None
    try:
        elb_classic = session.client("elb", region_name=REGION)
    except Exception:
        elb_classic = None

    lb_subnets_by_instance = {}
    if elbv2:
        try:
            paginator = elbv2.get_paginator("describe_load_balancers")
            pages = safe_call(lambda: paginator.paginate(), [])
            for page in pages or []:
                for lb in page.get("LoadBalancers", []):
                    lb_arn = lb.get("LoadBalancerArn")
                    lb_subnets = [az.get("SubnetId") for az in lb.get("AvailabilityZones", []) if az.get("SubnetId")]
                    if not lb_arn or not lb_subnets:
                        continue
                    target_groups = safe_call(lambda arn=lb_arn: elbv2.describe_target_groups(LoadBalancerArn=arn).get("TargetGroups", []), [])
                    for tg in target_groups or []:
                        if tg.get("TargetType") != "instance":
                            continue
                        tg_arn = tg.get("TargetGroupArn")
                        if not tg_arn:
                            continue
                        health = safe_call(lambda arn=tg_arn: elbv2.describe_target_health(TargetGroupArn=arn).get("TargetHealthDescriptions", []), [])
                        for desc in health or []:
                            target = desc.get("Target") or {}
                            inst_id = target.get("Id")
                            if inst_id:
                                lb_subnets_by_instance.setdefault(inst_id, set()).update(lb_subnets)
        except Exception as exc:
            print(f"  ⚠ Error gathering ELBv2 subnets: {exc}")

    if elb_classic:
        try:
            paginator = elb_classic.get_paginator("describe_load_balancers")
            pages = safe_call(lambda: paginator.paginate(), [])
            for page in pages or []:
                for lb in page.get("LoadBalancerDescriptions", []):
                    subnets = lb.get("Subnets", []) or []
                    instances = lb.get("Instances", []) or []
                    if not subnets or not instances:
                        continue
                    for inst in instances:
                        inst_id = inst.get("InstanceId")
                        if inst_id:
                            lb_subnets_by_instance.setdefault(inst_id, set()).update(subnets)
        except Exception as exc:
            print(f"  ⚠ Error gathering Classic ELB subnets: {exc}")

    rows = []
    # Fetch real per-instance costs from Cost Explorer (Approach B)
    ec2_instance_costs = _fetch_ec2_cost_per_instance(session)

    reservations = safe_call(lambda: ec2.describe_instances().get("Reservations", []), [])
    print(f"[DEBUG][EC2] Reservations found: {len(reservations)}")
    it_cache = {}
    ami_cache = {}
    iam_profile_cache = {}
    termination_cache = {}
    stop_cache = {}
    all_vol_ids = set()
    instance_info = []
    for r in reservations or []:
        for i in r.get("Instances", []):
            instance_id = i.get("InstanceId")
            instance_type = i.get("InstanceType")
            tags = i.get("Tags", [])
            name = next((t["Value"] for t in tags if t["Key"] == "Name"), "")
            # Pre-collect volume ids
            volume_ids = [bd.get("Ebs", {}).get("VolumeId") for bd in i.get("BlockDeviceMappings", []) if bd.get("Ebs", {}).get("VolumeId")]
            for volid in volume_ids:
                all_vol_ids.add(volid)
            instance_info.append((i, instance_id, instance_type, name, volume_ids))
    # describe all volumes in one call
    vol_map = {}
    if all_vol_ids:
        vols = safe_call(lambda: ec2.describe_volumes(VolumeIds=list(all_vol_ids)).get("Volumes", []), [])
        print(f"[DEBUG][EC2] Volumes found: {len(vols)}")
        for vol in vols:
            vol_map[vol["VolumeId"]] = vol
    # Now build rows with instance specs
    for i, instance_id, instance_type, name, volume_ids in instance_info:
        tags = i.get("Tags", []) or []
        state = i.get("State", {}).get("Name")
        primary_private_ip = i.get("PrivateIpAddress")
        primary_private_ips = set()
        if primary_private_ip:
            primary_private_ips.add(primary_private_ip)
        key_name = i.get("KeyName")
        subnet_id = i.get("SubnetId")
        vpc_id = i.get("VpcId")
        image_id = i.get("ImageId")

        ami_name = ""
        if image_id:
            if image_id in ami_cache:
                ami_name = ami_cache[image_id]
            else:
                images = safe_call(lambda img=image_id: ec2.describe_images(ImageIds=[img]).get("Images", []), [])
                if images:
                    ami_name = images[0].get("Name", "")
                ami_cache[image_id] = ami_name

        iam_roles = ""
        profile = i.get("IamInstanceProfile") or {}
        profile_arn = profile.get("Arn")
        if profile_arn:
            if profile_arn in iam_profile_cache:
                iam_roles = iam_profile_cache[profile_arn]
            else:
                profile_name = profile_arn.split("/")[-1]
                roles = []
                if iam_client:
                    resp = safe_call(lambda name=profile_name: iam_client.get_instance_profile(InstanceProfileName=name), {})
                    if resp:
                        roles = [r.get("RoleName") for r in resp.get("InstanceProfile", {}).get("Roles", []) if r.get("RoleName")]
                if roles:
                    iam_roles = ", ".join(sorted(set(roles)))
                else:
                    iam_roles = profile_name
                iam_profile_cache[profile_arn] = iam_roles

        termination_protection = ""
        if instance_id:
            if instance_id in termination_cache:
                termination_protection = termination_cache[instance_id]
            else:
                attr = safe_call(lambda inst=instance_id: ec2.describe_instance_attribute(InstanceId=inst, Attribute='disableApiTermination'), {})
                value = None
                if isinstance(attr, dict):
                    value = (attr.get("DisableApiTermination") or {}).get("Value")
                termination_protection = bool(value) if value is not None else False
                termination_cache[instance_id] = termination_protection

        # Stop protection (disableApiStop)
        stop_protection = False
        if instance_id:
            if instance_id in stop_cache:
                stop_protection = stop_cache[instance_id]
            else:
                try:
                    attr_stop = safe_call(lambda inst=instance_id: ec2.describe_instance_attribute(InstanceId=inst, Attribute='disableApiStop'), {})
                    val = (attr_stop.get("DisableApiStop") or {}).get("Value") if isinstance(attr_stop, dict) else None
                    stop_protection = bool(val) if val is not None else False
                except Exception:
                    stop_protection = False
                stop_cache[instance_id] = stop_protection

        lb_subnets = ""
        lb_subnet_set = lb_subnets_by_instance.get(instance_id)
        if lb_subnet_set:
            lb_subnets = "\n".join(sorted(lb_subnet_set))

        security_groups = ""
        sgs = i.get("SecurityGroups") or []
        if sgs:
            formatted = []
            for sg in sgs:
                sg_name = sg.get("GroupName")
                sg_id = sg.get("GroupId")
                if sg_name and sg_id:
                    formatted.append(f"{sg_name} ({sg_id})")
                elif sg_id:
                    formatted.append(sg_id)
                elif sg_name:
                    formatted.append(sg_name)
            if formatted:
                security_groups = "\n".join(sorted(set(formatted)))

        for eni in i.get("NetworkInterfaces", []) or []:
            eni_primary = eni.get("PrivateIpAddress")
            if eni_primary:
                primary_private_ips.add(eni_primary)
            for priv in eni.get("PrivateIpAddresses", []) or []:
                if priv.get("Primary"):
                    priv_ip_addr = priv.get("PrivateIpAddress")
                    if priv_ip_addr:
                        primary_private_ips.add(priv_ip_addr)
        private_ips_str = "\n".join(sorted(primary_private_ips)) if primary_private_ips else ""

        # Instance type specs
        vcpu = None
        ram_gb = None
        if instance_type:
            if instance_type in it_cache:
                spec = it_cache[instance_type]
            else:
                spec = get_instance_type_specs(ec2, instance_type)
                it_cache[instance_type] = spec
            vcpu = spec.get("vcpus")
            ram_gb = int(round(spec.get("memory_mb", 0) / 1024.0)) if spec and spec.get("memory_mb") else None
        # Volumes attached
        volumes = [vol_map.get(vid, {}) for vid in volume_ids]
        total_vol_size = sum([v.get("Size", 0) for v in volumes if v])
        vol_types = ", ".join(set([v.get("VolumeType", "") for v in volumes if v]))
        # Find EKS cluster name from tags.
        cluster = ""

        def clean(s: str) -> str:
            return s.replace('\n', ' ').replace('\r', ' ').strip()

        if tags and isinstance(tags, list):
            for t in tags:
                k = (t.get("Key") or "").strip()
                if k.lower() in ("aws:eks:cluster-name", "eks:cluster-name"):
                    val = t.get("Value")
                    if val:
                        cluster = clean(str(val))
                        break
            if not cluster:
                for t in tags:
                    k = (t.get("Key") or "")
                    if k.startswith("kubernetes.io/cluster/"):
                        parts = k.split("/", 1)
                        if len(parts) > 1 and parts[1]:
                            cluster = clean(parts[1])
                            break
            if not cluster:
                for t in tags:
                    if (t.get("Key") or "").strip().lower() == "name":
                        v = t.get("Value")
                        if v and "cluster" in v.lower():
                            cluster = clean(str(v))
                            break
        rows.append({
            "InstanceId": instance_id,
            "Name": name,
            "InstanceType": instance_type or "",
            "State": state or "",
            "Node_vCPU": vcpu if vcpu is not None else "",
            "RAM": ram_gb if ram_gb is not None else "",
            "AMIId": image_id or "",
            "AMIName": ami_name,
            "IAMRole": iam_roles,
            "TerminationProtection": termination_protection,
            "StopProtection": stop_protection,
            "KeyName": key_name,
            "PrivateIPs": private_ips_str,
            "SubnetId": subnet_id,
            "SecurityGroups": security_groups,
            "VolumeIds": "\n".join(volume_ids),
            "TotalVolumeSizeGB": total_vol_size,
            "VolumeTypes": "\n".join(set([v.get("VolumeType", "") for v in volumes if v])),
            "Cluster": cluster,
            # Placeholders — filled after bulk CW fetch below
            "CPUUtilizationAvg": None,
            "CPUUtilizationMax": None,
            "NetworkInMBAvg": None,
            "NetworkOutMBAvg": None,
            "OptimizationStatus": "",
            "CurrentMonthlyCostUSD": ec2_instance_costs.get(instance_id, 0.0),
            "MonthlySavingsUSD": 0.0,
            "OptimizedMonthlyCostUSD": 0.0,
        })

    # ── Bulk CloudWatch CPU / Network fetch (one API call per instance) ──
    all_instance_ids = [r["InstanceId"] for r in rows if r.get("InstanceId")]
    cw_metrics = _fetch_ec2_cpu_metrics(cloudwatch, all_instance_ids)

    for row in rows:
        iid   = row.get("InstanceId", "")
        state_val = row.get("State", "")
        m     = cw_metrics.get(iid, {})
        cpu_avg = m.get("cpu_avg")
        cpu_max = m.get("cpu_max")
        net_in  = m.get("net_in_mb_avg")
        net_out = m.get("net_out_mb_avg")

        row["CPUUtilizationAvg"]  = round(cpu_avg, 2)  if isinstance(cpu_avg, (int, float)) else ""
        row["CPUUtilizationMax"]  = round(cpu_max, 2)  if isinstance(cpu_max, (int, float)) else ""
        row["NetworkInMBAvg"]     = round(net_in,  3)  if isinstance(net_in,  (int, float)) else ""
        row["NetworkOutMBAvg"]    = round(net_out, 3)  if isinstance(net_out, (int, float)) else ""

        opt_status = _ec2_optimization_status(state_val, cpu_avg)
        row["OptimizationStatus"] = opt_status

        current_cost = row["CurrentMonthlyCostUSD"]
        savings      = _calculate_ec2_savings(current_cost, cpu_avg, opt_status)
        row["MonthlySavingsUSD"]       = savings
        row["OptimizedMonthlyCostUSD"] = round(current_cost - savings, 2)

    df = pd.DataFrame(rows)
    print(f"[DEBUG][EC2] DataFrame shape: {df.shape}")
    print(f"[DEBUG][EC2] DataFrame head:\n{df.head()}\n")
    return df

