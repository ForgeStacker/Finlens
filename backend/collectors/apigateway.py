"""API Gateway collectors."""
from __future__ import annotations

import json
import datetime
from collections import OrderedDict
from typing import Dict, Iterable, List
from urllib.parse import urlparse

import pandas as pd

from aws_utils import safe_call
from config import REGION


def _get_paginated_items(client, operation_name: str, result_key: str, **kwargs) -> List[dict]:
    """Run a paginator and return the flattened list of items."""
    def _call():
        paginator = client.get_paginator(operation_name)
        items: List[dict] = []
        for page in paginator.paginate(**kwargs):
            items.extend(page.get(result_key, []) or [])
        return items

    return safe_call(_call, [])


def _extract_load_balancer_hosts(resources: Iterable[dict]) -> List[str]:
    """Return a stable, de-duplicated list of load balancer hostnames used by integrations."""
    hosts: "OrderedDict[str, None]" = OrderedDict()
    for resource in resources or []:
        methods = resource.get("resourceMethods") or {}
        for method_def in methods.values():
            integration = (method_def or {}).get("methodIntegration") or {}
            uri = integration.get("uri")
            if not uri:
                continue
            hostname = urlparse(uri).netloc
            if hostname and hostname not in hosts:
                hosts[hostname] = None
    return list(hosts.keys())


def collect_apigateway_all(session, cost_map):
    rows = []
    cw = session.client("cloudwatch", region_name=REGION)
    # REST APIs
    ag_rest = session.client("apigateway", region_name=REGION)
    rest_apis = _get_paginated_items(ag_rest, "get_rest_apis", "items")
    for a in rest_apis or []:
        api_id = a.get("id")
        resources = safe_call(
            lambda: ag_rest.get_resources(restApiId=api_id, limit=500, embed=["methods", "integrations"]).get("items", []),
            [],
        )
        method_counts = {}
        for r in resources or []:
            rms = r.get("resourceMethods") or {}
            for m in rms:
                method_counts[m] = method_counts.get(m, 0) + 1
        methods_summary = ", ".join(f"{k}: {v}" for k, v in sorted(method_counts.items()))
        # Extract endpoint type from the REST API's endpointConfiguration if present.
        # endpointConfiguration may look like: {"types": ["REGIONAL"]}
        endpoint_types = a.get("endpointConfiguration", {}).get("types") if a else None
        api_endpoint_type = None
        if endpoint_types and isinstance(endpoint_types, (list, tuple)) and len(endpoint_types) > 0:
            api_endpoint_type = endpoint_types[0]
        else:
            # fallback to EDGE to preserve previous behavior when field is absent
            api_endpoint_type = "EDGE"

        load_balancers = _extract_load_balancer_hosts(resources)

        # Determine Stage (prefer 'prod' if present)
        stages_resp = safe_call(lambda: ag_rest.get_stages(restApiId=api_id), {}) or {}
        stage_items = stages_resp.get("item", []) or []
        stage_names = [s.get("stageName") for s in stage_items if s.get("stageName")] if stage_items else []
        preferred_stage = None
        if stage_names:
            preferred_stage = "prod" if "prod" in stage_names else stage_names[0]

        # CloudWatch invocation counts for REST (ApiName + Stage)
        sum_30 = sum_90 = sum_180 = 0
        if preferred_stage:
            end = datetime.datetime.utcnow()
            def _sum_for_days(days: int) -> int:
                start = end - datetime.timedelta(days=days)
                datapoints = safe_call(
                    lambda: cw.get_metric_statistics(
                        Namespace="AWS/ApiGateway",
                        MetricName="Count",
                        Dimensions=[
                            {"Name": "ApiName", "Value": a.get("name")},
                            {"Name": "Stage", "Value": preferred_stage},
                        ],
                        StartTime=start,
                        EndTime=end,
                        Period=86400,
                        Statistics=["Sum"],
                    ).get("Datapoints", []),
                    [],
                ) or []
                return int(sum(dp.get("Sum", 0) for dp in datapoints))

            sum_30 = _sum_for_days(30)
            sum_90 = _sum_for_days(90)
            sum_180 = _sum_for_days(180)

        rows.append({
            "Name": a.get("name"),
            "ApiId": api_id,
            "ApiType": "REST",
            "ApiEndpointType": api_endpoint_type,
            "ApiCount": len(resources or []),
            "Methods": methods_summary,
            "Stage": preferred_stage or "",
            "Last 30d Invocations": sum_30,
            "Last 90d Invocations": sum_90,
            "Last 180d Invocations": sum_180,
            "LoadBalancers": "\n".join(load_balancers) if load_balancers else "",
        })
    # HTTP & WebSocket APIs
    ag_v2 = session.client("apigatewayv2", region_name=REGION)
    v2_apis = _get_paginated_items(ag_v2, "get_apis", "Items")
    for a in v2_apis or []:
        api_id = a.get("ApiId")
        protocol = a.get("ProtocolType")
        endpoint_type = a.get("ApiEndpointType", "REGIONAL")
        routes = _get_paginated_items(ag_v2, "get_routes", "Items", ApiId=api_id)
        method_counts = {}
        for route in routes or []:
            m = route.get("RouteKey")
            if m:
                method_counts[m] = method_counts.get(m, 0) + 1
        methods_summary = ", ".join(f"{k}: {v}" for k, v in sorted(method_counts.items()))

        # Determine Stage for v2 APIs
        v2_stages_resp = safe_call(lambda: ag_v2.get_stages(ApiId=api_id), {}) or {}
        v2_stage_items = v2_stages_resp.get("Items", []) or []
        v2_stage_names = [s.get("StageName") for s in v2_stage_items if s.get("StageName")] if v2_stage_items else []
        v2_preferred_stage = None
        if v2_stage_names:
            v2_preferred_stage = "prod" if "prod" in v2_stage_names else v2_stage_names[0]

        # CloudWatch invocation counts for v2 (ApiId + Stage)
        v2_sum_30 = v2_sum_90 = v2_sum_180 = 0
        if v2_preferred_stage:
            end = datetime.datetime.utcnow()
            def _v2_sum_for_days(days: int) -> int:
                start = end - datetime.timedelta(days=days)
                datapoints = safe_call(
                    lambda: cw.get_metric_statistics(
                        Namespace="AWS/ApiGateway",
                        MetricName="Count",
                        Dimensions=[
                            {"Name": "ApiId", "Value": api_id},
                            {"Name": "Stage", "Value": v2_preferred_stage},
                        ],
                        StartTime=start,
                        EndTime=end,
                        Period=86400,
                        Statistics=["Sum"],
                    ).get("Datapoints", []),
                    [],
                ) or []
                return int(sum(dp.get("Sum", 0) for dp in datapoints))

            v2_sum_30 = _v2_sum_for_days(30)
            v2_sum_90 = _v2_sum_for_days(90)
            v2_sum_180 = _v2_sum_for_days(180)
        rows.append({
            "Name": a.get("Name"),
            "ApiId": api_id,
            "ApiType": protocol,
            "ApiEndpointType": endpoint_type,
            "ApiCount": len(routes or []),
            "Methods": methods_summary,
            "Stage": v2_preferred_stage or "",
            "Last 30d Invocations": v2_sum_30,
            "Last 90d Invocations": v2_sum_90,
            "Last 180d Invocations": v2_sum_180,
        })
    return pd.DataFrame(rows)


def collect_apigateway_v2(session, cost_map):
    ag = session.client("apigatewayv2", region_name=REGION)
    rows = []
    apis = _get_paginated_items(ag, "get_apis", "Items")
    for a in apis or []:
        api_id = a.get("ApiId")
        routes = _get_paginated_items(ag, "get_routes", "Items", ApiId=api_id)
        rows.append({
            "APIType": a.get("ProtocolType"),
            "APIId": api_id,
            "Name": a.get("Name"),
            "RouteCount": len(routes or []),
            "Routes": json.dumps(routes or [])
        })
    return pd.DataFrame(rows)
