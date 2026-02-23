"""AWS Service Catalog collectors."""
from __future__ import annotations

import pandas as pd

from aws_utils import safe_call
from config import REGION


def collect_servicecatalog(session, cost_map) -> pd.DataFrame:
    client = session.client("servicecatalog", region_name=REGION)
    rows = []

    # Portfolios
    portfolios = safe_call(
        lambda: client.list_portfolios().get("PortfolioDetails", []), []
    )
    for portfolio in portfolios or []:
        portfolio_id = portfolio.get("Id", "")
        # Products in this portfolio
        products = safe_call(
            lambda pid=portfolio_id: client.search_products_as_admin(
                PortfolioId=pid
            ).get("ProductViewDetails", []),
            [],
        )
        if products:
            for prod in products:
                pv = prod.get("ProductViewSummary", {})
                rows.append({
                    "PortfolioId": portfolio_id,
                    "PortfolioName": portfolio.get("DisplayName", ""),
                    "PortfolioDescription": portfolio.get("Description", ""),
                    "ProductId": pv.get("ProductId", ""),
                    "ProductName": pv.get("Name", ""),
                    "ProductType": pv.get("Type", ""),
                    "Owner": pv.get("Owner", ""),
                    "ShortDescription": pv.get("ShortDescription", ""),
                    "CreatedTime": str(portfolio.get("CreatedTime", "") or ""),
                })
        else:
            rows.append({
                "PortfolioId": portfolio_id,
                "PortfolioName": portfolio.get("DisplayName", ""),
                "PortfolioDescription": portfolio.get("Description", ""),
                "ProductId": "",
                "ProductName": "",
                "ProductType": "",
                "Owner": "",
                "ShortDescription": "",
                "CreatedTime": str(portfolio.get("CreatedTime", "") or ""),
            })

    return pd.DataFrame(rows)
