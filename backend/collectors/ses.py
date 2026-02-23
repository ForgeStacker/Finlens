"""Amazon SES collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_ses(session, cost_map) -> pd.DataFrame:
    client = session.client("sesv2", region_name=REGION)
    rows = []

    # Email identities
    identities = safe_call(
        lambda: client.list_email_identities().get("EmailIdentities", []), []
    )
    for identity in identities or []:
        identity_name = identity.get("IdentityName", "")
        detail = safe_call(
            lambda n=identity_name: client.get_email_identity(EmailIdentity=n), {}
        )
        dkim = detail.get("DkimAttributes", {})
        rows.append({
            "IdentityName": identity_name,
            "IdentityType": identity.get("IdentityType", ""),
            "SendingEnabled": detail.get("SendingEnabled", ""),
            "DkimEnabled": dkim.get("SigningEnabled", ""),
            "DkimStatus": dkim.get("Status", ""),
            "VerifiedForSendingStatus": detail.get("VerifiedForSendingStatus", ""),
            "MailFromDomain": detail.get("MailFromAttributes", {}).get("MailFromDomain", ""),
        })

    # Configuration sets
    config_sets = safe_call(
        lambda: client.list_configuration_sets().get("ConfigurationSets", []), []
    )
    for cs in config_sets or []:
        rows.append({
            "IdentityName": f"[ConfigSet] {cs}",
            "IdentityType": "ConfigurationSet",
            "SendingEnabled": "",
            "DkimEnabled": "",
            "DkimStatus": "",
            "VerifiedForSendingStatus": "",
            "MailFromDomain": "",
        })

    return pd.DataFrame(rows)
