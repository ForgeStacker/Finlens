#!/usr/bin/env python3
"""Generate frontend offline snapshot from Data/CSV inputs.

Output: frontend/src/generated/offlineSnapshot.ts
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
CSV_DIR = ROOT / "Data" / "CSV"
OUTPUT_TS = ROOT / "frontend" / "src" / "generated" / "offlineSnapshot.ts"

sys.path.insert(0, str(BACKEND_DIR))

from api_server import (  # type: ignore  # noqa: E402
    SERVICE_NAME_MAP,
    _get_live_monthly_costs,
    _get_usd_inr_rate,
    _to_float,
    extract_profile_region,
    parse_csv_to_json,
)


def build_snapshot() -> dict:
    profiles = []
    services_index: dict[str, dict] = {}
    profile_data: dict[str, dict] = {}
    profile_overview: dict[str, dict] = {}

    csv_files = sorted(CSV_DIR.glob("*.csv")) if CSV_DIR.exists() else []

    for csv_file in csv_files:
        profile = csv_file.stem
        region = extract_profile_region(csv_file)
        services_data = parse_csv_to_json(csv_file)

        profiles.append(
            {
                "id": profile,
                "name": profile,
                "profile": profile,
                "region": region,
                "csvFile": csv_file.name,
            }
        )

        for sid, svc in services_data.items():
            if sid not in services_index:
                services_index[sid] = {
                    "id": sid,
                    "name": svc.get("serviceName", sid),
                    "collectorFunction": f"collect_{sid.replace('-', '_')}",
                }

        total_resources = sum((svc.get("resourceCount") or 0) for svc in services_data.values())

        profile_data[profile] = {
            "profile": profile,
            "servicesCount": len(services_data),
            "totalResources": total_resources,
            "services": services_data,
        }

        overview_items = []
        for sid, svc in services_data.items():
            item = {
                "id": sid,
                "name": svc.get("serviceName", sid),
                "resourceCount": svc.get("resourceCount", 0),
                "healthStatus": "healthy",
            }
            if svc.get("monthlyCost") is not None:
                item["monthlyCost"] = round(_to_float(svc.get("monthlyCost")), 2)
            overview_items.append(item)

        # Best-effort CE overlay (same as runtime API behavior)
        live_costs = _get_live_monthly_costs(profile)
        live_total = _to_float(live_costs.get("total", 0.0))
        live_by_service = live_costs.get("byService", {}) or {}
        for item in overview_items:
            sid = item.get("id")
            if sid in live_by_service:
                cost = _to_float(live_by_service.get(sid))
                if cost > 0:
                    item["monthlyCost"] = round(cost, 2)

        total_monthly_cost = (
            round(live_total, 2)
            if live_total > 0
            else round(sum(_to_float(item.get("monthlyCost", 0)) for item in overview_items), 2)
        )

        profile_overview[profile] = {
            "profile": profile,
            "services": overview_items,
            "totalServices": len(overview_items),
            "totalResources": total_resources,
            "totalMonthlyCost": total_monthly_cost,
        }

    try:
        fx = _get_usd_inr_rate()
    except Exception:
        fx = {
            "base": "USD",
            "target": "INR",
            "rate": 83.0,
            "cached": True,
            "source": "offline-fallback",
            "warning": "Using fallback exchange rate in offline snapshot.",
        }

    # Keep service order consistent with known map first, then discovered extras
    ordered_service_ids = list(dict.fromkeys(list(SERVICE_NAME_MAP.values()) + sorted(services_index.keys())))
    services = [services_index[sid] for sid in ordered_service_ids if sid in services_index]

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "profiles": sorted(profiles, key=lambda p: p["name"].lower()),
        "services": services,
        "profileData": profile_data,
        "profileOverview": profile_overview,
        "exchangeRate": fx,
    }


def write_typescript(snapshot: dict) -> None:
    OUTPUT_TS.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "import type { ExchangeRateResponse, Profile, ProfileData, ProfileOverview, Service } from \"@/lib/api-client\";\n\n"
        "export interface OfflineSnapshot {\n"
        "  generatedAt: string;\n"
        "  profiles: Profile[];\n"
        "  services: Service[];\n"
        "  profileData: Record<string, ProfileData>;\n"
        "  profileOverview: Record<string, ProfileOverview>;\n"
        "  exchangeRate: ExchangeRateResponse;\n"
        "}\n\n"
        f"export const offlineSnapshot: OfflineSnapshot = {json.dumps(snapshot, ensure_ascii=False, indent=2)};\n"
    )
    OUTPUT_TS.write_text(content, encoding="utf-8")


def main() -> int:
    if not CSV_DIR.exists():
        print(f"CSV directory not found: {CSV_DIR}")
        return 1

    snapshot = build_snapshot()
    write_typescript(snapshot)

    print(f"Offline snapshot generated: {OUTPUT_TS}")
    print(f"Profiles: {len(snapshot['profiles'])}")
    print(f"Services indexed: {len(snapshot['services'])}")
    print(f"Generated at: {snapshot['generatedAt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
