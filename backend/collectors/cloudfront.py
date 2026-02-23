"""CloudFront collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call


def collect_cloudfront(session, cost_map):
    cf = session.client("cloudfront")
    rows = []
    dist_list = safe_call(lambda: cf.list_distributions().get("DistributionList", {}).get("Items", []), [])
    for d in dist_list or []:
        # Get origin details
        origins = d.get("Origins", {}).get("Items", [])
        # Each origin as a single line: DomainName [OriginPath]
        origin_lines = []
        for o in origins:
            domain = o.get("DomainName", "")
            path = o.get("OriginPath", "")
            if path:
                origin_lines.append(f"{domain} [{path}]")
            else:
                origin_lines.append(f"{domain}")
        origins_str = "\n".join(origin_lines)

        alt_domains = d.get("Aliases", {}).get("Items", [])
        alt_domains_str = "\n".join(alt_domains)
        price_class = d.get("PriceClass")

        rows.append({
            "Id": d.get("Id"),
            "DomainName": d.get("DomainName"),
            "AlternateDomainNames": alt_domains_str,
            "PriceClass": price_class,
            "Status": d.get("Status"),
            "Enabled": d.get("Enabled"),
            "Origins": origins_str
        })
    return pd.DataFrame(rows)
