"""AWS WAF collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_waf(session, cost_map):
    waf = session.client("waf", region_name=REGION)
    rows = []
    web_acls = safe_call(lambda: waf.list_web_acls().get("WebACLs", []), [])
    for acl in web_acls or []:
        rows.append({
            "WebACLId": acl.get("WebACLId"),
            "Name": acl.get("Name"),
        })
    return pd.DataFrame(rows)
