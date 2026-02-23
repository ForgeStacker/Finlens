"""EKS collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import get_instance_type_specs, safe_call
from config import REGION


def collect_eks(session, cost_map):
    eks = session.client("eks", region_name=REGION)
    ec2 = session.client("ec2", region_name=REGION)
    cw = session.client("cloudwatch", region_name=REGION)
    rows = []
    clusters = safe_call(lambda: eks.list_clusters().get("clusters", []), [])
    print(f"[DEBUG][EKS] Clusters found: {clusters}")
    if not clusters:
        return pd.DataFrame()
    for c in clusters:
        cluster = safe_call(lambda: eks.describe_cluster(name=c).get("cluster", {}), {})

        # --- EKS CloudWatch Metrics ---
        now = pd.Timestamp.utcnow()
        start = now - pd.Timedelta(hours=1)
        metrics = {}
        def get_metric(metric_name):
            resp = safe_call(lambda: cw.get_metric_statistics(
                Namespace='AWS/EKS',
                MetricName=metric_name,
                Dimensions=[{'Name': 'ClusterName', 'Value': c}],
                StartTime=start,
                EndTime=now,
                Period=3600,
                Statistics=['Average']
            ), {})
            return resp.get('Datapoints', [{}])[0].get('Average') if resp.get('Datapoints') else None

        metrics['APIServerLatencyP99'] = get_metric('apiserver_request_duration_seconds_GET_P99')
        metrics['SchedulerPendingPods'] = get_metric('scheduler_pending_pods')
        metrics['StorageSizeBytes'] = get_metric('apiserver_storage_size_bytes')

        def safe_join(lst):
            return ", ".join(lst) if lst else None

        cluster_info = {
            "ClusterName": c,
            "Cluster Role": cluster.get("roleArn"),
            "ClusterVersion": cluster.get("version"),
            "UpgradePolicy": cluster.get("upgradePolicy", {}).get("supportType"),
            "DeletionProtection": cluster.get("deletionProtection"),
            "AuthenticationMode": cluster.get("accessConfig", {}).get("authenticationMode"),
            "ClusterSubnet": safe_join(cluster.get("resourcesVpcConfig", {}).get("subnetIds", [])),
            "ClusterSecurityGroupId": cluster.get("resourcesVpcConfig", {}).get("clusterSecurityGroupId"),
            "AdditionalSecurityGroup": safe_join(cluster.get("resourcesVpcConfig", {}).get("securityGroupIds", [])),
            "ClusterAddons": ", ".join(safe_call(lambda: eks.list_addons(clusterName=c).get("addons", []), [])),
            "EndpointAccess": cluster.get("resourcesVpcConfig", {}).get("endpointPublicAccess"),
            "PublicAllowlist": ", ".join(cluster.get("resourcesVpcConfig", {}).get("publicAccessCidrs", [])),
            # --- EKS Metrics for Analysis ---
            "APIServerLatencyP99": metrics['APIServerLatencyP99'],
            "SchedulerPendingPods": metrics['SchedulerPendingPods'],
            "StorageSizeBytes": metrics['StorageSizeBytes'],
        }
        nodegroups = safe_call(lambda: eks.list_nodegroups(clusterName=c).get("nodegroups", []), [])
        print(f"[DEBUG][EKS] Cluster: {c}, Nodegroups: {nodegroups}")
        if not nodegroups:
            row = dict(cluster_info)
            row.update({
                "NodeGroupName": None,
                "Node Role": None,
                "AMI": None,
                "VolumeType": None,
                "InstanceTypes": None,
                "Node_vCPU": None,
                "Node_MemoryMB": None,
                "DiskSizeGB": None,
                "MinSize": None,
                "MaxSize": None,
                "DesiredSize": None,
                "NodeAutoRepair": None,
                "CapacityType": None,
                "NodegroupSubnet": None
            })
            rows.append(row)
            continue

        for ng in nodegroups:
            try:
                print(f"[DEBUG][EKS] Processing nodegroup: {ng}")
                ngd = safe_call(lambda: eks.describe_nodegroup(clusterName=c, nodegroupName=ng).get("nodegroup", {}), {})
                inst_types = ngd.get("instanceTypes", [])
                if not inst_types:
                    lt = ngd.get("launchTemplate")
                    if lt:
                        lt_id = lt.get("id")
                        lt_version = lt.get("version")
                        if lt_id and lt_version:
                            try:
                                lt_resp = ec2.describe_launch_template_versions(LaunchTemplateId=lt_id, Versions=[str(lt_version)])
                                lt_data = lt_resp['LaunchTemplateVersions'][0]['LaunchTemplateData']
                                itype = lt_data.get('InstanceType')
                                if itype:
                                    inst_types = [itype]
                            except Exception as e:
                                print(f"[ERROR][EKS] Error getting instance type from launch template: {e}")
                vcpu = None
                ram_gb = None
                disk_size = None
                vcpus_list = []
                ram_list = []
                for itype in inst_types:
                    spec = get_instance_type_specs(ec2, itype)
                    vcpus = spec.get("vcpus") if spec else None
                    # Safely compute RAM (GB) only when memory_mb is present
                    ram = None
                    if spec:
                        mem_mb = spec.get("memory_mb")
                        if mem_mb is not None:
                            try:
                                ram = int(round(mem_mb / 1024.0))
                            except Exception:
                                ram = None
                    vcpus_list.append(str(vcpus) if vcpus is not None else "")
                    ram_list.append(str(ram) if ram is not None else "")
                vcpu = "\n".join(vcpus_list) if vcpus_list else ""
                ram_gb = "\n".join(ram_list) if ram_list else ""
                disk_size = ngd.get("diskSize")
                if disk_size is None:
                    lt = ngd.get("launchTemplate")
                    if lt:
                        lt_id = lt.get("id")
                        lt_version = lt.get("version")
                        if lt_id and lt_version:
                            try:
                                lt_resp = ec2.describe_launch_template_versions(LaunchTemplateId=lt_id, Versions=[str(lt_version)])
                                lt_data = lt_resp['LaunchTemplateVersions'][0]['LaunchTemplateData']
                                bdms = lt_data.get('BlockDeviceMappings', [])
                                if bdms:
                                    ebs = bdms[0].get('Ebs')
                                    if ebs:
                                        disk_size = ebs.get('VolumeSize')
                            except Exception as e:
                                print(f"[ERROR][EKS] Error getting disk size from launch template: {e}")
                                disk_size = None
                ami = "N/A"
                volume_type = "N/A"
                lt = ngd.get("launchTemplate")
                if lt:
                    lt_id = lt.get("id")
                    lt_version = lt.get("version")
                    if lt_id and lt_version:
                        try:
                            lt_resp = ec2.describe_launch_template_versions(LaunchTemplateId=lt_id, Versions=[str(lt_version)])
                            lt_data = lt_resp['LaunchTemplateVersions'][0]['LaunchTemplateData']
                            ami = lt_data.get("ImageId", "N/A")
                            bdms = lt_data.get("BlockDeviceMappings", [])
                            if bdms:
                                ebs = bdms[0].get("Ebs")
                                if ebs:
                                    volume_type = ebs.get("VolumeType", "N/A")
                        except Exception as e:
                            print(f"[ERROR][EKS] Error getting AMI/VolumeType from launch template: {e}")
                row = dict(cluster_info)
                scaling_cfg = ngd.get("scalingConfig") or {}
                row.update({
                    "NodeGroupName": ng,
                    "Node Role": ngd.get("nodeRole"),
                    "AMI": ami,
                    "VolumeType": volume_type,
                    "InstanceTypes": ", ".join(inst_types) if inst_types else "",
                    "Node_vCPU": vcpu if vcpu is not None else "",
                    "RAM": ram_gb if ram_gb is not None else "",
                    "DiskSizeGB": disk_size if disk_size is not None else "",
                    "MinSize": scaling_cfg.get("minSize"),
                    "MaxSize": scaling_cfg.get("maxSize"),
                    "DesiredSize": scaling_cfg.get("desiredSize"),
                    "NodeAutoRepair": ngd.get("nodeRepairConfig", {}).get("enabled"),
                    "CapacityType": ngd.get("capacityType"),
                    "NodegroupSubnet": safe_join(ngd.get("subnets", []))
                })
                print(f"[DEBUG][EKS] Appending row for nodegroup: {ng} -> {row}")
                rows.append(row)
            except IndexError as e:
                print(f"[ERROR][EKS] IndexError in nodegroup {ng}: {e}")
            except Exception as e:
                print(f"[ERROR][EKS] Unexpected error in nodegroup {ng}: {e}")
    try:
        df = pd.DataFrame(rows)
        print(f"[DEBUG][EKS] DataFrame shape: {df.shape}")
        print(f"[DEBUG][EKS] DataFrame head:\n{df.head()}\n")
        return df
    except IndexError as e:
        print(f"[ERROR][EKS] IndexError when creating DataFrame: {e}")
        print(f"[ERROR][EKS] Rows: {rows}")
        return pd.DataFrame()
