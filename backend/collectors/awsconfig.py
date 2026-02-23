"""AWS Config collectors (config rules and recorders)."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_awsconfig(session, cost_map) -> pd.DataFrame:
    client = session.client("config", region_name=REGION)
    rows = []

    # Config rules
    paginator = client.get_paginator("describe_config_rules")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for rule in page.get("ConfigRules", []):
            source = rule.get("Source", {})
            compliance = safe_call(
                lambda n=rule.get("ConfigRuleName", ""): client.describe_compliance_by_config_rule(
                    ConfigRuleNames=[n]
                ).get("ComplianceByConfigRules", [{}])[0].get("Compliance", {}).get("ComplianceType", ""),
                "",
            )
            rows.append({
                "ConfigRuleName": rule.get("ConfigRuleName", ""),
                "ConfigRuleArn": rule.get("ConfigRuleArn", ""),
                "ConfigRuleState": rule.get("ConfigRuleState", ""),
                "SourceOwner": source.get("Owner", ""),
                "SourceIdentifier": source.get("SourceIdentifier", ""),
                "Scope": str(rule.get("Scope", "") or ""),
                "ComplianceType": compliance,
                "Description": rule.get("Description", ""),
            })

    # Configuration recorders
    recorders = safe_call(lambda: client.describe_configuration_recorders().get("ConfigurationRecorders", []), [])
    recorder_statuses = safe_call(
        lambda: {
            s["name"]: s
            for s in client.describe_configuration_recorder_status().get("ConfigurationRecordersStatus", [])
        },
        {},
    )
    for rec in recorders or []:
        name = rec.get("name", "")
        st = recorder_statuses.get(name, {})
        rows.append({
            "ConfigRuleName": f"[Recorder] {name}",
            "ConfigRuleArn": "",
            "ConfigRuleState": "Recording" if st.get("recording") else "Stopped",
            "SourceOwner": "Recorder",
            "SourceIdentifier": rec.get("roleARN", ""),
            "Scope": "AllResources" if rec.get("recordingGroup", {}).get("allSupported") else "Scoped",
            "ComplianceType": "",
            "Description": "",
        })

    return pd.DataFrame(rows)
