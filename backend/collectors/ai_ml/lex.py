"""
Lex Collector
Collects AWS Lex bots and bot aliases
"""

from typing import Dict, Any, List
from backend.collectors.base import BaseCollector
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class LexCollector(BaseCollector):
    """Collector for AWS Lex resources"""
    
    category = "ai_ml"
    
    def __init__(self, profile_name: str, region: str):
        """
        Initialize Lex collector
        
        Args:
            profile_name: AWS profile name
            region: AWS region
        """
        super().__init__(profile_name, region, 'lexv2-models')
        self.collector_name = 'lex'
    
    def collect(self) -> Dict[str, Any]:
        """
        Collect Lex resources
        
        Returns:
            Dictionary containing Lex data
        """
        try:
            logger.info(f"Collecting Lex bots from {self.region_name}")
            
            resources = []
            
            # Collect bots
            bots = self._collect_bots()
            resources.extend(bots)
            
            logger.info(f"Collected {len(resources)} Lex bots from {self.region_name}")
            
            summary = {
                'total_bots': len(bots)
            }
            
            metadata = {
                'scan_timestamp': self.scan_timestamp,
                'collector_version': '1.0.0'
            }
            
            return self._build_response_structure(resources, summary, metadata)
            
        except Exception as e:
            logger.error(f"Error collecting Lex resources: {e}")
            return self._build_response_structure([], {'error': str(e)})
    
    def _collect_bots(self) -> List[Dict[str, Any]]:
        """Collect Lex bots"""
        bots = []
        try:
            response = self.client.list_bots()
            
            for bot_summary in response.get('botSummaries', []):
                bot_id = bot_summary.get('botId')
                
                # Get bot details
                try:
                    bot_detail = self.client.describe_bot(botId=bot_id)
                    
                    bots.append({
                        'resource_id': bot_id,
                        'resource_type': 'lex-bot',
                        'resource_name': bot_summary.get('botName'),
                        'region': self.region_name,
                        'status': bot_summary.get('botStatus'),
                        'description': bot_detail.get('description', ''),
                        'bot_type': bot_detail.get('botType'),
                        'role_arn': bot_detail.get('roleArn'),
                        'creation_time': bot_summary.get('creationDateTime'),
                        'last_updated': bot_summary.get('lastUpdatedDateTime'),
                        'tags': bot_detail.get('botTags', {})
                    })
                except Exception as e:
                    logger.warning(f"Error getting bot details for {bot_id}: {e}")
                    
        except Exception as e:
            logger.warning(f"Error collecting Lex bots: {e}")
        
        return bots
