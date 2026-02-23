"""Amazon Lex collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_lex(session, cost_map) -> pd.DataFrame:
    client = session.client("lexv2-models", region_name=REGION)
    rows = []

    bots = safe_call(lambda: client.list_bots(filters=[]).get("botSummaries", []), [])
    for bot in bots or []:
        bot_id = bot.get("botId", "")
        # Get aliases for this bot
        aliases = safe_call(
            lambda bid=bot_id: client.list_bot_aliases(botId=bid).get("botAliasSummaries", []), []
        )
        alias_names = ", ".join(a.get("botAliasName", "") for a in (aliases or []))
        rows.append({
            "BotId": bot_id,
            "BotName": bot.get("botName", ""),
            "Status": bot.get("botStatus", ""),
            "LatestBotVersion": bot.get("latestBotVersion", ""),
            "Aliases": alias_names,
            "LastUpdatedDateTime": str(bot.get("lastUpdatedDateTime", "") or ""),
        })

    return pd.DataFrame(rows)
