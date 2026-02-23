"""Amazon Polly collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_polly(session, cost_map) -> pd.DataFrame:
    client = session.client("polly", region_name=REGION)
    rows = []

    lexicons = safe_call(lambda: client.list_lexicons().get("Lexicons", []), [])
    for lex in lexicons or []:
        attrs = lex.get("Attributes", {})
        rows.append({
            "LexiconName": lex.get("Name", ""),
            "LanguageCode": attrs.get("LanguageCode", ""),
            "LastModified": str(attrs.get("LastModified", "") or ""),
            "LexemesCount": attrs.get("LexemesCount", ""),
            "Size": attrs.get("Size", ""),
            "Alphabet": attrs.get("Alphabet", ""),
        })

    return pd.DataFrame(rows)
