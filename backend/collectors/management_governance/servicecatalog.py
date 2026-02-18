"""
Service Catalog Collector
Collects AWS Service Catalog portfolios and products
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ServiceCatalogCollector(BaseCollector):
    """Collector for AWS Service Catalog resources"""
    
    category = "management_governance"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Service Catalog collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'servicecatalog')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Service Catalog resources
        
        Returns:
            Dictionary containing Service Catalog data
        """
        try:
            logger.info(f"Collecting Service Catalog resources from {self.region_name}")
            
            resources = []
            
            # Collect portfolios
            portfolios = self._collect_portfolios()
            resources.extend(portfolios)
            
            # Collect products
            products = self._collect_products()
            resources.extend(products)
            
            logger.info(f"Collected {len(resources)} Service Catalog resources from {self.region_name}")
            
            summary = {
                'total_resources': len(resources),
                'portfolios': len(portfolios),
                'products': len(products)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Service Catalog resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_portfolios(self) -> List[Dict[str, Any]]:
        """Collect Service Catalog portfolios"""
        portfolios = []
        try:
            response = self.client.list_portfolios()
            
            for portfolio in response.get('PortfolioDetails', []):
                portfolio_id = portfolio.get('Id')
                
                # Get portfolio details
                try:
                    detail = self.client.describe_portfolio(Id=portfolio_id)
                    portfolio_detail = detail.get('PortfolioDetail', {})
                    
                    portfolios.append({
                        'resource_id': portfolio_id,
                        'resource_type': 'servicecatalog-portfolio',
                        'resource_name': portfolio.get('DisplayName'),
                        'region': self.region_name,
                        'provider_name': portfolio.get('ProviderName'),
                        'description': portfolio.get('Description'),
                        'arn': portfolio_detail.get('ARN'),
                        'created_time': portfolio.get('CreatedTime'),
                        'tags': portfolio_detail.get('Tags', [])
                    })
                except Exception as e:
                    logger.warning(f"Error getting portfolio details for {portfolio_id}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Service Catalog portfolios: {e}")
        
        return portfolios
    
    def _collect_products(self) -> List[Dict[str, Any]]:
        """Collect Service Catalog products"""
        products = []
        try:
            response = self.client.search_products_as_admin()
            
            for product in response.get('ProductViewDetails', []):
                product_view = product.get('ProductViewSummary', {})
                product_id = product_view.get('ProductId')
                
                products.append({
                    'resource_id': product_id,
                    'resource_type': 'servicecatalog-product',
                    'resource_name': product_view.get('Name'),
                    'region': self.region_name,
                    'type': product_view.get('Type'),
                    'owner': product_view.get('Owner'),
                    'short_description': product_view.get('ShortDescription'),
                    'distributor': product_view.get('Distributor'),
                    'has_default_path': product_view.get('HasDefaultPath'),
                    'tags': {}
                })
                    
        except Exception as e:
            logger.warning(f"Error collecting Service Catalog products: {e}")
        
        return products
