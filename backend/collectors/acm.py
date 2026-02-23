"""AWS Certificate Manager (ACM) collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_acm(session, cost_map) -> pd.DataFrame:
    client = session.client("acm", region_name=REGION)
    rows = []

    paginator = client.get_paginator("list_certificates")
    for page in safe_call(lambda: list(paginator.paginate()), []) or []:
        for cert_summary in page.get("CertificateSummaryList", []):
            arn = cert_summary.get("CertificateArn", "")
            detail = safe_call(
                lambda a=arn: client.describe_certificate(CertificateArn=a).get("Certificate", {}), {}
            )
            sans = detail.get("SubjectAlternativeNames", [])
            rows.append({
                "CertificateArn": arn,
                "DomainName": cert_summary.get("DomainName", ""),
                "SubjectAlternativeNames": ", ".join(sans),
                "Status": detail.get("Status", ""),
                "Type": detail.get("Type", ""),
                "KeyAlgorithm": detail.get("KeyAlgorithm", ""),
                "SignatureAlgorithm": detail.get("SignatureAlgorithm", ""),
                "InUseBy": ", ".join(detail.get("InUseBy", [])),
                "DomainValidationStatus": ", ".join(
                    f"{dv.get('DomainName')}:{dv.get('ValidationStatus', '')}"
                    for dv in detail.get("DomainValidationOptions", [])
                ),
                "Issuer": detail.get("Issuer", ""),
                "NotBefore": str(detail.get("NotBefore", "") or ""),
                "NotAfter": str(detail.get("NotAfter", "") or ""),
                "RenewalEligibility": detail.get("RenewalEligibility", ""),
                "CreatedAt": str(detail.get("CreatedAt", "") or ""),
            })

    return pd.DataFrame(rows)
