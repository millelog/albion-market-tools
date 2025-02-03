import logging
from typing import List, Dict, Any, Optional
from database import MarketDatabase
from config import CITIES, DB, FLIP_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self):
        """Initialize the market analyzer with database connection."""
        self.db = MarketDatabase()
    
    def get_top_items(self, location: str, limit: int = 50, 
                     min_data_points: Optional[int] = None,
                     min_volume: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get top items for a location based on market activity.
        
        Args:
            location: The city/location to analyze
            limit: Maximum number of items to return
            min_data_points: Minimum number of data points required
            min_volume: Minimum average daily volume required
            
        Returns:
            List of dictionaries containing item statistics and rankings
        """
        return self.db.query_top_items(
            location=location,
            limit=limit,
            min_data_points=min_data_points,
            min_volume=min_volume
        )
    
    def get_all_locations_top_items(self, limit_per_location: Optional[int] = None,
                                  min_data_points: Optional[int] = None,
                                  min_volume: Optional[float] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get top items for all configured locations.
        
        Args:
            limit_per_location: Maximum items per location (defaults to FLIP_CONFIG['items_to_analyze'])
            min_data_points: Minimum number of data points required
            min_volume: Minimum average daily volume required
            
        Returns:
            Dictionary mapping locations to their top items
        """
        if limit_per_location is None:
            limit_per_location = FLIP_CONFIG['items_to_analyze']
            
        results = {}
        for location in CITIES:
            try:
                items = self.get_top_items(
                    location=location,
                    limit=limit_per_location,
                    min_data_points=min_data_points,
                    min_volume=min_volume
                )
                results[location] = items
                logger.info(f"Found {len(items)} top items for {location}")
                
            except Exception as e:
                logger.error(f"Error getting top items for {location}: {e}")
                results[location] = []
                
        return results
    
    def get_item_market_stats(self, item_id: str, quality: int) -> Dict[str, Dict[str, Any]]:
        """
        Get market statistics for a specific item across all locations.
        
        Args:
            item_id: The unique item identifier
            quality: Item quality level
            
        Returns:
            Dictionary mapping locations to item statistics
        """
        results = {}
        for location in CITIES:
            try:
                stats = self.db.get_item_stats(item_id, quality, location)
                if stats:
                    # Calculate market value
                    stats['market_value'] = stats['avg_item_count'] * stats['avg_price']
                    results[location] = stats
                    
            except Exception as e:
                logger.error(f"Error getting stats for {item_id} in {location}: {e}")
                
        return results

def analyze_market_opportunities(region: str = 'Europe', 
                              min_data_points: Optional[int] = None,
                              min_volume: Optional[float] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Analyze market opportunities across all cities.
    
    Args:
        region: API region (for reference)
        min_data_points: Minimum number of data points required
        min_volume: Minimum average daily volume required
        
    Returns:
        Dictionary mapping locations to their market opportunities
    """
    try:
        analyzer = MarketAnalyzer()
        return analyzer.get_all_locations_top_items(
            min_data_points=min_data_points,
            min_volume=min_volume
        )
        
    except Exception as e:
        logger.error(f"Error analyzing market opportunities: {e}")
        return {} 