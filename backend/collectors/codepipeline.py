"""AWS CodePipeline collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_codepipeline(session, cost_map) -> pd.DataFrame:
    client = session.client("codepipeline", region_name=REGION)
    rows = []

    paginator = client.get_paginator("list_pipelines")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for pl in page.get("pipelines", []):
            name = pl.get("name", "")
            detail = safe_call(
                lambda n=name: client.get_pipeline(name=n).get("pipeline", {}), {}
            )
            state = safe_call(
                lambda n=name: client.get_pipeline_state(name=n), {}
            )
            stage_states = [
                f"{s.get('stageName')}:{s.get('latestExecution', {}).get('status', 'N/A')}"
                for s in state.get("stageStates", [])
            ]
            rows.append({
                "PipelineName": name,
                "PipelineArn": f"arn:aws:codepipeline:{REGION}::{name}",
                "RoleArn": detail.get("roleArn", ""),
                "Version": pl.get("version", ""),
                "ExecutionMode": detail.get("executionMode", ""),
                "StagesCount": len(detail.get("stages", [])),
                "StageStatuses": ", ".join(stage_states),
                "Created": str(pl.get("created", "") or ""),
                "Updated": str(pl.get("updated", "") or ""),
            })

    return pd.DataFrame(rows)
