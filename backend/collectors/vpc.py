"""Amazon VPC collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_vpc(session, cost_map):
    ec2 = session.client("ec2", region_name=REGION)
    rows = []
    vpcs = safe_call(lambda: ec2.describe_vpcs().get("Vpcs", []), [])
    for vpc in vpcs or []:
        vpc_id = vpc.get("VpcId")
        cidr_blocks = [assoc.get("CidrBlock") for assoc in vpc.get("CidrBlockAssociationSet", []) if assoc.get("CidrBlock")]
        cidrs = "\n".join(cidr_blocks) if cidr_blocks else None
        is_default = vpc.get("IsDefault")
        name = ""
        for tag in vpc.get("Tags", []) or []:
            if tag.get("Key") == "Name":
                name = tag.get("Value", "")
                break
        if name and "aws-controltower" in name.lower():
            continue
        subnets = safe_call(
            lambda: ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]).get("Subnets", []),
            [],
        )
        first = True
        for subnet in subnets or []:
            rows.append(
                {
                    "VPC Name": name if first else "",
                    "VpcId": vpc_id if first else "",
                    "CIDRs": cidrs if first else "",
                    "IsDefault": is_default if first else "",
                    "SubnetId": subnet.get("SubnetId"),
                    "SubnetCIDR": subnet.get("CidrBlock"),
                    "AvailabilityZone": subnet.get("AvailabilityZone"),
                }
            )
            first = False
        if not subnets:
            rows.append(
                {
                    "VPC Name": name,
                    "VpcId": vpc_id,
                    "CIDRs": cidrs,
                    "IsDefault": is_default,
                    "SubnetId": None,
                    "SubnetCIDR": None,
                    "AvailabilityZone": None,
                }
            )
    return pd.DataFrame(rows)
