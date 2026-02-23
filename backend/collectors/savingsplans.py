"""AWS Savings Plans collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_savingsplans(session, cost_map) -> pd.DataFrame:
    client = session.client("savingsplans", region_name="us-east-1")
    rows = []

    plans = safe_call(
        lambda: client.describe_savings_plans(states=["active", "queued"]).get("savingsPlans", []), []
    )
    for sp in plans or []:
        rows.append({
            "SavingsPlanId": sp.get("savingsPlanId", ""),
            "SavingsPlanArn": sp.get("savingsPlanArn", ""),
            "SavingsPlanType": sp.get("savingsPlanType", ""),
            "State": sp.get("state", ""),
            "CommitmentAmount": sp.get("commitment", ""),
            "Currency": sp.get("currency", ""),
            "OfferingId": sp.get("offeringId", ""),
            "PaymentOption": sp.get("paymentOption", ""),
            "DurationSeconds": sp.get("durationSeconds", ""),
            "UpfrontPaymentAmount": sp.get("upfrontPaymentAmount", ""),
            "RecurringPaymentAmount": sp.get("recurringPaymentAmount", ""),
            "Start": sp.get("start", ""),
            "End": sp.get("end", ""),
        })

    return pd.DataFrame(rows)
