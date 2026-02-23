import argparse
import json
import math
from datetime import date, timedelta

import boto3


def get_resource_ids(client, start_date, end_date):
    resource_ids = []
    next_token = None

    while True:
        params = {
            "TimePeriod": {"Start": start_date, "End": end_date},
            "Dimension": "RESOURCE_ID",
            "MaxResults": 100
        }
        if next_token:
            params["NextPageToken"] = next_token

        response = client.get_dimension_values(**params)
        resource_ids.extend([item["Value"] for item in response["DimensionValues"]])
        next_token = response.get("NextPageToken")

        if not next_token:
            break

    return resource_ids


def get_resource_cost(client, resource_id, start_date, end_date):
    response = client.get_cost_and_usage_with_resources(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={
            "Dimensions": {
                "Key": "RESOURCE_ID",
                "Values": [resource_id]
            }
        }
    )

    total = 0.0
    for result in response["ResultsByTime"]:
        amount = float(result["Total"]["UnblendedCost"]["Amount"])
        total += amount

    return total


def main():
    parser = argparse.ArgumentParser(description="Get top cost resources")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--top", type=int, default=50)
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile)
    ce_client = session.client("ce", region_name="us-east-1")

    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    resource_ids = get_resource_ids(ce_client, start_str, end_str)
    print(f"Found {len(resource_ids)} resource ids")

    cost_data = []
    for idx, resource_id in enumerate(resource_ids, start=1):
        cost = get_resource_cost(ce_client, resource_id, start_str, end_str)
        cost_data.append({"resource_id": resource_id, "cost_usd": cost})

        if idx % 10 == 0:
            print(f"Processed {idx}/{len(resource_ids)} resources")

    cost_data.sort(key=lambda x: x["cost_usd"], reverse=True)

    MAX_ID_WIDTH = 60
    def format_resource_id(rid):
        if len(rid) > MAX_ID_WIDTH:
            return rid[:MAX_ID_WIDTH-3] + "..."
        return rid

    header = f"Top {args.top} cost resources in profile {args.profile} for last {args.days} days"
    print("\n" + header)
    print("-" * len(header))
    print(f"{'#':>3} | {'Resource ID':<{MAX_ID_WIDTH}} | {'Cost (USD)':>12}")
    print("-" * (3 + 2 + MAX_ID_WIDTH + 3 + 12))

    for idx, entry in enumerate(cost_data[:args.top], start=1):
        resource_id = format_resource_id(entry["resource_id"] or "<no-resource-id>")
        print(f"{idx:>3} | {resource_id:<{MAX_ID_WIDTH}} | {entry['cost_usd']:>12.2f}")


if __name__ == "__main__":
    main()
