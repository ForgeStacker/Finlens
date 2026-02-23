"""ECR collectors."""
from __future__ import annotations

import json

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_ecr(session, cost_map):
    ecr = session.client("ecr", region_name=REGION)
    rows = []
    paginator = ecr.get_paginator("describe_repositories")
    for page in safe_call(lambda: paginator.paginate(), []):
        for r in page.get("repositories", []):
            repo_name = r.get("repositoryName")
            images = safe_call(lambda: ecr.list_images(repositoryName=repo_name, filter={"tagStatus": "TAGGED"}).get("imageIds", []), [])
            mutability = r.get("imageTagMutability", "UNKNOWN")
            last_image_size = ""
            try:
                if images:
                    image_details = safe_call(lambda: ecr.describe_images(repositoryName=repo_name, imageIds=images[:50]).get("imageDetails", []), [])
                    if image_details:
                        image_details = sorted([img for img in image_details if "imagePushedAt" in img], key=lambda x: x["imagePushedAt"], reverse=True)
                        if image_details:
                            last_image = image_details[0]
                            last_image_size = round(last_image.get("imageSizeInBytes", 0) / (1024.0 ** 2), 2)
            except Exception as e:
                print(f"  ⚠ ECR image size error for {repo_name}: {e}")
                last_image_size = "Error"
            lifecycle_rules = ""
            try:
                lifecycle_resp = ecr.get_lifecycle_policy(repositoryName=repo_name)
                policy_text = lifecycle_resp.get("lifecyclePolicyText") or lifecycle_resp.get("LifecyclePolicyText")
                if policy_text:
                    try:
                        parsed_policy = json.loads(policy_text)
                        summaries = []
                        for rule in parsed_policy.get("rules", []):
                            desc = rule.get("description")
                            sel = rule.get("selection", {})
                            act = rule.get("action", {})
                            if act.get("type") == "expire":
                                if sel.get("countType") == "sinceImagePushed":
                                    days = sel.get("countNumber") or sel.get("countUnit")
                                    summaries.append(f"Delete images older than {days} days")
                                elif sel.get("countType") == "imageCountMoreThan":
                                    count = sel.get("countNumber")
                                    summaries.append(f"Keep minimum {count} images")
                                else:
                                    summaries.append(desc or "Expire images by policy")
                            elif act.get("type") == "retain":
                                if sel.get("countType") == "sinceImagePushed":
                                    days = sel.get("countNumber") or sel.get("countUnit")
                                    summaries.append(f"Keep images for {days} days")
                                elif sel.get("countType") == "imageCountMoreThan":
                                    count = sel.get("countNumber")
                                    summaries.append(f"Keep minimum {count} images")
                                else:
                                    summaries.append(desc or "Retain images by policy")
                            else:
                                summaries.append(desc or "Custom lifecycle rule")
                        lifecycle_rules = "; ".join(summaries) if summaries else desc or policy_text
                    except Exception:
                        lifecycle_rules = policy_text
            except ecr.exceptions.LifecyclePolicyNotFoundException:
                lifecycle_rules = ""
            except Exception as exc:
                print(f"  ⚠ ECR lifecycle policy error for {repo_name}: {exc}")
                lifecycle_rules = ""
            rows.append({
                "RepositoryName": repo_name,
                "ImageCount": len(images or []),
                "ImageTagMutability": mutability,
                "LastImageSizeMB": last_image_size,
                "LifecycleRules": lifecycle_rules
            })
    return pd.DataFrame(rows)
