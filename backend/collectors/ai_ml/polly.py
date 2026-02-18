"""
Polly Collector
Collects AWS Polly lexicons
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class PollyCollector(BaseCollector):
    """Collector for AWS Polly resources"""
    
    category = "ai_ml"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Polly collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'polly')
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Polly resources
        
        Returns:
            Dictionary containing Polly data
        """
        try:
            logger.info(f"Collecting Polly lexicons from {self.region_name}")
            
            resources = []
            
            # Collect lexicons
            lexicons = self._collect_lexicons()
            resources.extend(lexicons)
            
            logger.info(f"Collected {len(resources)} Polly lexicons from {self.region_name}")
            
            summary = {
                'total_lexicons': len(lexicons)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Polly resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_lexicons(self) -> List[Dict[str, Any]]:
        """Collect Polly lexicons"""
        lexicons = []
        try:
            response = self.client.list_lexicons()
            
            for lexicon in response.get('Lexicons', []):
                lexicon_name = lexicon.get('Name')
                
                # Get lexicon details
                try:
                    detail = self.client.get_lexicon(Name=lexicon_name)
                    
                    lexicons.append({
                        'resource_id': lexicon_name,
                        'resource_type': 'polly-lexicon',
                        'resource_name': lexicon_name,
                        'region': self.region_name,
                        'language_code': lexicon.get('Attributes', {}).get('LanguageCode'),
                        'lexemes_count': lexicon.get('Attributes', {}).get('LexemesCount'),
                        'size': lexicon.get('Attributes', {}).get('Size'),
                        'last_modified': lexicon.get('Attributes', {}).get('LastModified'),
                        'tags': {}
                    })
                except Exception as e:
                    logger.warning(f"Error getting lexicon details for {lexicon_name}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Polly lexicons: {e}")
        
        return lexicons
