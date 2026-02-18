import boto3
from backend.collectors.base import BaseCollector

class CostExplorerCollector(BaseCollector):
    def __init__(self, profile, region):
        super().__init__(profile, region, 'ce')
        self.client = boto3.client('ce', region_name=region)

    def collect(self):
        import datetime
        end = datetime.date.today().replace(day=1)
        start = (end - datetime.timedelta(days=1)).replace(day=1)
        # Cost and usage
        cost_usage = self.client.get_cost_and_usage(
            TimePeriod={
                'Start': start.strftime('%Y-%m-%d'),
                'End': end.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost', 'BlendedCost', 'UsageQuantity']
        )
        # Cost categories
        try:
            cost_categories = self.client.get_cost_categories(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                }
            )
        except Exception:
            cost_categories = None
        # Forecast
        try:
            forecast = self.client.get_cost_forecast(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Metric='UNBLENDED_COST',
                Granularity='MONTHLY'
            )
        except Exception:
            forecast = None
        # Usage
        try:
            usage = self.client.get_usage_forecast(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Metric='USAGE_QUANTITY',
                Granularity='MONTHLY'
            )
        except Exception:
            usage = None
        # Reservation coverage
        try:
            reservation_coverage = self.client.get_reservation_coverage(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY'
            )
        except Exception:
            reservation_coverage = None
        # Reservation utilization
        try:
            reservation_utilization = self.client.get_reservation_utilization(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY'
            )
        except Exception:
            reservation_utilization = None
        # Savings plans
        try:
            savings_plans = self.client.get_savings_plans_coverage(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY'
            )
        except Exception:
            savings_plans = None
        # Purchase recommendations
        try:
            purchase_recommendations = self.client.get_reservation_purchase_recommendation(
                Service='AmazonEC2',
                TermInYears='ONE_YEAR',
                PaymentOption='NO_UPFRONT',
                AccountScope='PAYER'
            )
        except Exception:
            purchase_recommendations = None
        # Recommendations
        try:
            recommendations = self.client.get_rightsizing_recommendation()
        except Exception:
            recommendations = None
        return {
            'cost_usage': cost_usage,
            'cost_categories': cost_categories,
            'forecast': forecast,
            'usage': usage,
            'reservation_coverage': reservation_coverage,
            'reservation_utilization': reservation_utilization,
            'savings_plans': savings_plans,
            'purchase_recommendations': purchase_recommendations,
            'recommendations': recommendations
        }
