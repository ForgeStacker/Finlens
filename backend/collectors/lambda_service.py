"""AWS Lambda collectors."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

import pandas as pd
from botocore.exceptions import ClientError

from aws_utils import safe_call
from config import REGION

RETENTION_WINDOW_DAYS = 455
DAILY_PERIOD_SECONDS = 24 * 60 * 60
HOURLY_PERIOD_SECONDS = 60 * 60
LAST_15_DAYS = 15


def _get_last_invocation_plus_one_day(cloudwatch_client, function_name: str) -> str:
    """Return the last invocation timestamp converted to IST."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=RETENTION_WINDOW_DAYS)
    response = safe_call(
        lambda: cloudwatch_client.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Invocations",
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            Statistics=["Sum"],
            Period=DAILY_PERIOD_SECONDS,
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    if not datapoints:
        return ""
    latest = max(datapoints, key=lambda dp: dp.get("Timestamp") or datetime.min.replace(tzinfo=timezone.utc))
    timestamp = latest.get("Timestamp")
    if not isinstance(timestamp, datetime):
        return ""
    # Convert to IST (UTC+5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = timestamp.astimezone(timezone.utc) + ist_offset
    return ist_time.strftime("%Y-%m-%d %H:%M:%S IST")


def _get_eventbridge_triggers(events_client, target_arn: str) -> list[str]:
    triggers: list[str] = []
    rule_names = safe_call(
        lambda: events_client.list_rule_names_by_target(TargetArn=target_arn).get("RuleNames", []),
        [],
    )
    for rule in rule_names or []:
        label = f"EventBridge:{rule}"
        details = safe_call(lambda: events_client.describe_rule(Name=rule), {})
        schedule = details.get("ScheduleExpression") if isinstance(details, dict) else None
        if schedule:
            label = f"{label} ({schedule})"
        triggers.append(label)
    return triggers


def _get_invocation_sum(cloudwatch_client, function_name: str, lookback_days: int) -> int:
    """Return total invocation count over the requested lookback window."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=lookback_days)
    response = safe_call(
        lambda: cloudwatch_client.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Invocations",
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            Statistics=["Sum"],
            Period=HOURLY_PERIOD_SECONDS,
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    total = 0.0
    for datapoint in datapoints:
        try:
            total += float(datapoint.get("Sum", 0.0))
        except Exception:
            continue
    return int(total)


def _get_average_duration_ms_all_time(cloudwatch_client, function_name: str) -> float:
    """Return average execution duration (ms) across CloudWatch retention (~15 months).

    Computes average as sum(Duration) / sum(SampleCount) using daily aggregation
    over RETENTION_WINDOW_DAYS.
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=RETENTION_WINDOW_DAYS)
    response = safe_call(
        lambda: cloudwatch_client.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Duration",
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            Statistics=["Sum", "SampleCount"],
            Period=DAILY_PERIOD_SECONDS,
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    total_sum = 0.0
    total_count = 0.0
    for dp in datapoints:
        try:
            total_sum += float(dp.get("Sum", 0.0))
            total_count += float(dp.get("SampleCount", 0.0))
        except Exception:
            continue
    if total_count <= 0:
        return 0.0
    # Duration metric unit is milliseconds
    return round(total_sum / total_count, 2)


def _get_metric_30d_sum(cloudwatch_client, function_name: str, metric_name: str) -> float:
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=30)
    response = safe_call(
        lambda: cloudwatch_client.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName=metric_name,
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            Statistics=["Sum"],
            Period=24 * 60 * 60,
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    total = 0.0
    for dp in datapoints:
        try:
            total += float(dp.get("Sum", 0.0))
        except Exception:
            continue
    return total


def _get_metric_30d_avg(cloudwatch_client, function_name: str, metric_name: str) -> float:
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=30)
    response = safe_call(
        lambda: cloudwatch_client.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName=metric_name,
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            Statistics=["Average"],
            Period=24 * 60 * 60,
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    values = []
    for dp in datapoints:
        try:
            values.append(float(dp.get("Average", 0.0)))
        except Exception:
            continue
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _get_metric_30d_max(cloudwatch_client, function_name: str, metric_name: str) -> float:
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=30)
    response = safe_call(
        lambda: cloudwatch_client.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName=metric_name,
            Dimensions=[{"Name": "FunctionName", "Value": function_name}],
            Statistics=["Maximum"],
            Period=24 * 60 * 60,
            StartTime=start_time,
            EndTime=end_time,
        ),
        {},
    )
    datapoints = response.get("Datapoints", []) if isinstance(response, dict) else []
    max_vals = []
    for dp in datapoints:
        try:
            max_vals.append(float(dp.get("Maximum", 0.0)))
        except Exception:
            continue
    if not max_vals:
        return 0.0
    return max(max_vals)


def _get_max_memory_from_logs(logs_client, function_name: str) -> float:
    try:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=30)
        try:
            resp = logs_client.filter_log_events(
                logGroupName=f"/aws/lambda/{function_name}",
                startTime=int(start.timestamp() * 1000),
                endTime=int(now.timestamp() * 1000),
                filterPattern="REPORT",
                limit=50,
            )
        except ClientError as exc:
            code = (exc.response or {}).get("Error", {}).get("Code", "")
            if code in {"ResourceNotFoundException", "ResourceNotFound"}:
                # Expected for functions with no CloudWatch log group yet.
                return 0.0
            raise

        events = resp.get("events", []) if isinstance(resp, dict) else []
        max_used = 0.0
        for ev in events:
            msg = str(ev.get("message", ""))
            m = re.search(r"Max Memory Used: ([\d.]+) MB", msg)
            if m:
                try:
                    val = float(m.group(1))
                    if val > max_used:
                        max_used = val
                except Exception:
                    continue
        return max_used
    except Exception:
        return 0.0


def _calculate_lambda_cost(memory_mb: int, avg_duration_ms: float, invocations: float) -> float:
    if not invocations or not avg_duration_ms:
        return 0.0
    memory_gb = float(memory_mb) / 1024.0
    duration_seconds = float(avg_duration_ms) / 1000.0
    request_cost_usd = (float(invocations) / 1_000_000.0) * 0.20
    gb_seconds = memory_gb * duration_seconds * float(invocations)
    duration_cost_usd = gb_seconds * 0.0000166667
    return request_cost_usd + duration_cost_usd


def _get_recommended_memory(allocated_memory: int, max_memory_used: float) -> int:
    if not max_memory_used or max_memory_used <= 0:
        return allocated_memory
    options = [128, 256, 512, 1024, 1536, 2048, 3008, 5120, 7680, 10240]
    target = max_memory_used * 1.2
    for m in options:
        if m >= target:
            return m
    return 10240


def _get_timeout_recommendation(timeout_seconds: int, max_duration_ms: float, timeout_ratio: float) -> str:
    if not max_duration_ms or max_duration_ms <= 0:
        if timeout_seconds > 30:
            return f"Consider reducing from {timeout_seconds}s to 30s - no recent execution data"
        return ""
    max_s = max_duration_ms / 1000.0
    if timeout_ratio > 10.0:
        rec = max(int(max_s * 1.5), 3)
        rec = min(rec, 900)
        if rec < timeout_seconds:
            return f"Reduce from {timeout_seconds}s to {rec}s (max execution {max_s:.1f}s, large buffer)"
    elif timeout_ratio < 1.2:
        rec = min(int(max_s * 2.0), 900)
        if rec > timeout_seconds:
            return f"Increase from {timeout_seconds}s to {rec}s (risk of timeout - max execution {max_s:.1f}s)"
    return f"Keep {timeout_seconds}s (appropriate for max execution {max_s:.1f}s)"


def _get_memory_recommendation(allocated_memory: int, max_memory_used: float) -> str:
    if not max_memory_used or max_memory_used <= 0:
        return f"Current: {allocated_memory}MB - No recent usage data available"
    util = (max_memory_used / float(allocated_memory)) * 100.0
    options = [128, 256, 512, 1024, 1536, 2048, 3008, 5120, 7680, 10240]
    target = max_memory_used * 1.2
    chosen = None
    for m in options:
        if m >= target:
            chosen = m
            break
    if not chosen:
        if allocated_memory > 10240:
            return f"Reduce from {allocated_memory}MB to 10240MB (max AWS limit)"
        return f"Current: {allocated_memory}MB - Consider optimizing code for lower memory"
    if chosen < allocated_memory:
        savings_pct = round(((allocated_memory - chosen) / float(allocated_memory)) * 100.0, 1)
        return f"Reduce from {allocated_memory}MB to {chosen}MB (save {savings_pct}% cost - using {util:.1f}%)"
    if util > 80.0:
        next_opt = None
        for m in options:
            if m > allocated_memory:
                next_opt = m
                break
        if next_opt:
            return f"Increase from {allocated_memory}MB to {next_opt}MB (high utilization {util:.1f}%)"
        return f"Current: {allocated_memory}MB - High utilization {util:.1f}%, consider code optimization"
    return f"Keep {allocated_memory}MB (optimal utilization {util:.1f}%)"


def collect_lambda(session, cost_map):
    lam = session.client("lambda", region_name=REGION)
    events = session.client("events", region_name=REGION)
    cloudwatch = session.client("cloudwatch", region_name=REGION)
    logs = session.client("logs", region_name=REGION)
    rows = []
    paginator = lam.get_paginator("list_functions")
    for page in safe_call(lambda: paginator.paginate(), []):
        for fn in page.get("Functions", []):
            fname = fn.get("FunctionName")
            arn = fn.get("FunctionArn")
            full_cfg = safe_call(lambda: lam.get_function_configuration(FunctionName=fname), {})
            timeout = full_cfg.get("Timeout", fn.get("Timeout"))
            memory = full_cfg.get("MemorySize", fn.get("MemorySize"))
            runtime = full_cfg.get("Runtime", fn.get("Runtime"))
            mappings = safe_call(lambda: lam.list_event_source_mappings(FunctionName=fname).get("EventSourceMappings", []), [])
            triggers = []
            for mapping in mappings or []:
                if mapping.get("EventSourceArn"):
                    triggers.append(mapping["EventSourceArn"])
            triggers.extend(_get_eventbridge_triggers(events, arn))
            policy_str = None
            try:
                policy_str = lam.get_policy(FunctionName=fname).get("Policy")
            except lam.exceptions.ResourceNotFoundException:
                pass
            except Exception as exc:
                print(f"  ⚠ Warning: {type(exc).__name__}: {exc}")
            if policy_str:
                try:
                    policy = json.loads(policy_str)
                    for stmt in policy.get("Statement", []):
                        principal = stmt.get("Principal", {})
                        service = principal.get("Service") if isinstance(principal, dict) else None
                        
                        if service == "sns.amazonaws.com":
                            cond = stmt.get("Condition", {})
                            arnlike = cond.get("ArnLike", {})
                            sns_arn = arnlike.get("AWS:SourceArn")
                            if sns_arn:
                                triggers.append(sns_arn)
                        
                        elif service == "apigateway.amazonaws.com":
                            cond = stmt.get("Condition", {})
                            arnlike = cond.get("ArnLike", {})
                            source_arn = arnlike.get("AWS:SourceArn") if arnlike else None
                            if source_arn:
                                # Extract API Gateway ID from ARN like arn:aws:execute-api:region:account:api-id/...
                                api_id_match = source_arn.split(":")[-1].split("/")[0] if "/" in source_arn else None
                                if api_id_match:
                                    triggers.append(f"API Gateway:{api_id_match}")
                except Exception:
                    pass
            trigger_label = "Manual"
            if triggers:
                trigger_label = ", ".join(sorted(set(str(t) for t in triggers)))
            timeout_value = timeout
            role = full_cfg.get("Role", fn.get("Role"))
            destination = None
            try:
                invoke_cfg = lam.get_function_event_invoke_config(FunctionName=fname)
                dest_cfg = invoke_cfg.get("DestinationConfig")
                if dest_cfg:
                    for key in ("OnSuccess", "OnFailure"):
                        if key in dest_cfg and dest_cfg[key] and "Destination" in dest_cfg[key]:
                            destination = dest_cfg[key]["Destination"]
                            break
            except lam.exceptions.ResourceNotFoundException:
                pass
            except Exception as exc:
                print(f"  ⚠ Warning: {type(exc).__name__}: {exc}")
            last_invocation_plus_one = _get_last_invocation_plus_one_day(cloudwatch, fname)
            invocations_15d = _get_invocation_sum(cloudwatch, fname, LAST_15_DAYS)
            avg_duration_ms = _get_average_duration_ms_all_time(cloudwatch, fname)
            avg_duration_sec = round(avg_duration_ms / 1000.0, 2) if avg_duration_ms else 0.0

            inv_30 = _get_metric_30d_sum(cloudwatch, fname, "Invocations")
            err_30 = _get_metric_30d_sum(cloudwatch, fname, "Errors")
            thr_30 = _get_metric_30d_sum(cloudwatch, fname, "Throttles")
            dur_avg_30 = _get_metric_30d_avg(cloudwatch, fname, "Duration")
            dur_max_30 = _get_metric_30d_max(cloudwatch, fname, "Duration")
            mem_used_max = _get_max_memory_from_logs(logs, fname)
            mem_util_pct = round((mem_used_max / float(memory)) * 100.0, 1) if mem_used_max and memory else 0.0
            timeout_buffer_ratio = round(((timeout * 1000.0) / dur_max_30), 2) if dur_max_30 > 0 else 0.0
            mem_note = _get_memory_recommendation(memory, mem_used_max)
            to_note = _get_timeout_recommendation(timeout, dur_max_30, timeout_buffer_ratio)
            opt_notes = " | ".join([n for n in [mem_note, to_note] if n])
            current_cost = _calculate_lambda_cost(memory, dur_avg_30, inv_30)
            rec_mem = _get_recommended_memory(memory, mem_used_max)
            optimized_cost = _calculate_lambda_cost(rec_mem, dur_avg_30, inv_30)
            monthly_savings = max(current_cost - optimized_cost, 0.0)
            cost_reduction_pct = round(((current_cost - optimized_cost) / current_cost) * 100.0, 1) if current_cost > 0 else 0.0
            
            # Get environment variables
            env_vars = full_cfg.get("Environment", {}).get("Variables", {})
            env_var_str = ""
            if env_vars:
                env_var_str = ", ".join([f"{k}={v}" for k, v in env_vars.items()])
            
            # Get function URL
            function_url = ""
            try:
                url_config = lam.get_function_url_config(FunctionName=fname)
                function_url = url_config.get("FunctionUrl", "")
            except lam.exceptions.ResourceNotFoundException:
                pass
            except Exception:
                pass
            
            # Get code/package size
            code_size = fn.get("CodeSize", 0)
            code_size_mb = round(code_size / (1024 * 1024), 2) if code_size else 0
            
            rows.append({
                "FunctionName": fname,
                "Runtime": runtime,
                "Architectures": ", ".join(full_cfg.get("Architectures", [])) if full_cfg.get("Architectures") else "",
                "PackageSizeMB": code_size_mb,
                "MemoryMB": memory,
                "TimeoutSec": timeout_value,
                "Triggers": trigger_label,
                "PermissionRoleName": role,
                "Destination": destination,
                "EnvironmentVariables": env_var_str,
                "FunctionURL": function_url,
                "LastInvocationIST": last_invocation_plus_one,
                "InvocationsLast15Days": invocations_15d,
                "AverageExecutionTimeSeconds": avg_duration_sec,
                "InvocationsLast30Days": int(inv_30),
                "ErrorsLast30Days": int(err_30),
                "ThrottlesLast30Days": int(thr_30),
                "AverageDurationMs30Days": round(dur_avg_30, 2),
                "MaxDurationMs30Days": round(dur_max_30, 2),
                "MemoryUsedMaxMB": round(mem_used_max, 2) if mem_used_max > 0 else 0.0,
                "MemoryUtilizationPercent": mem_util_pct,
                "TimeoutBufferRatio": timeout_buffer_ratio,
                "OptimizationNotes": opt_notes,
                "CurrentMonthlyCostUSD": round(current_cost, 4),
                "OptimizedMonthlyCostUSD": round(optimized_cost, 4),
                "MonthlySavingsUSD": round(monthly_savings, 4),
                "CostReductionPercent": cost_reduction_pct,
                "DailyAverageInvocations": round((inv_30 / 30.0), 2) if inv_30 > 0 else 0.0,
            })
    return pd.DataFrame(rows)
