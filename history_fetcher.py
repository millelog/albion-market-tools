import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from api_client import APIClient
from database import MarketDatabase
from config import CITIES, DB
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoryFetcher:
    def __init__(self, region: str = 'Americas'):
        """Initialize the history fetcher with API client and database connection."""
        self.api_client = APIClient(region=region)
        self.db = MarketDatabase()
        # Load item names from items.json
        try:
            with open('ids/items.json', 'r', encoding='utf-8') as f:
                items_data = json.load(f)
                self.item_names = {}
                for item in items_data:
                    try:
                        unique_name = item.get('UniqueName')
                        localized_names = item.get('LocalizedNames', {})
                        if unique_name and isinstance(localized_names, dict):
                            self.item_names[unique_name] = localized_names.get('EN-US', '')
                    except Exception as e:
                        logger.warning(f"Skipping malformed item entry: {e}")
        except Exception as e:
            logger.error(f"Error loading item names from items.json: {e}")
            self.item_names = {}
        
    def fetch_history_data(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch historical data for the given item IDs.
        
        Args:
            item_ids: List of item identifiers (e.g., ["T4_BAG", "T5_BAG"])
            
        Returns:
            List of historical data records from the API
        """
        logger.info(f"Fetching historical data for {len(item_ids)} items")
        
        try:
            # Use the new get_history_data method from API client
            return self.api_client.get_history_data(item_ids)
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []

    def aggregate_history_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregate historical data into statistics per location/item/quality.
        
        Args:
            raw_data: List of historical data records from the API
            
        Returns:
            List of dictionaries containing aggregated statistics
        """
        logger.info("Aggregating historical data")
        aggregated_stats = []
        
        for record in raw_data:
            location = record.get('location')
            item_id = record.get('item_id')
            quality = record.get('quality', 1)  # Default to normal quality if not specified
            
            if not all([location, item_id, quality]):
                logger.warning(f"Skipping record with missing key data: {record}")
                continue
                
            # Process the time series data
            data_points = record.get('data', [])
            if not data_points:
                continue
                
            # Filter out entries older than max_history_days
            cutoff_date = datetime.utcnow() - timedelta(days=DB['max_history_days'])
            valid_points = [
                point for point in data_points
                if point.get('item_count', 0) > 0 
                and point.get('avg_price', 0) > 0
                and datetime.fromisoformat(point['timestamp']) > cutoff_date
            ]
            
            if len(valid_points) < DB['min_data_points']:
                logger.debug(f"Insufficient data points for {item_id} in {location}")
                continue
                
            # Calculate averages
            total_count = sum(point['item_count'] for point in valid_points)
            total_price = sum(point['avg_price'] for point in valid_points)
            num_points = len(valid_points)
            
            # Parse enchantment level from item_id
            enchant_lvl = 0
            if '@' in item_id:
                try:
                    enchant_lvl = int(item_id.split('@')[1])
                except (IndexError, ValueError):
                    logger.warning(f"Failed to parse enchantment level from {item_id}")
            
            aggregated_stats.append({
                'location': location,
                'item_id': item_id,
                'item_name': self.item_names.get(item_id, ''),
                'quality': quality,
                'enchant_lvl': enchant_lvl,
                'avg_item_count': round(total_count / num_points, 2),
                'avg_price': round(total_price / num_points, 2),
                'data_points': num_points
            })
            
        return aggregated_stats

    def fetch_and_store_history(self, item_ids: List[str]):
        """
        Fetch historical data for items, aggregate it, and store in the database.
        
        Args:
            item_ids: List of item identifiers to process
        """
        try:
            # Fetch raw historical data
            raw_data = self.fetch_history_data(item_ids)
            if not raw_data:
                logger.warning("No historical data retrieved")
                return
                
            logger.info(f"Retrieved {len(raw_data)} historical records")
            
            # Aggregate the data
            aggregated_stats = self.aggregate_history_data(raw_data)
            if not aggregated_stats:
                logger.warning("No valid aggregated statistics generated")
                return
                
            logger.info(f"Generated {len(aggregated_stats)} aggregated statistics")
            
            # Store in database
            self.db.insert_or_update_history_stats(aggregated_stats)
            logger.info("Successfully stored historical statistics in database")
            
        except Exception as e:
            logger.error(f"Error in fetch_and_store_history: {e}")
            raise

def update_history_for_cities(region: str = 'Americas'):
    """
    Update historical data for all items in all configured cities.
    
    Args:
        region: API region to use (default: 'Americas')
    """    
    try:
        # Load items from items.json
        try:
            with open('ids/items.json', 'r', encoding='utf-8') as f:
                items_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading items.json: {e}")
            return
            
        # Get unique item IDs from items.json
        unique_items = {item['UniqueName'] for item in items_data if 'UniqueName' in item}
            
        if not unique_items:
            logger.warning("No items found to process")
            return
            
        logger.info(f"Processing {len(unique_items)} unique items from items.json")
        
        # Initialize fetcher and process items
        fetcher = HistoryFetcher(region=region)
        fetcher.fetch_and_store_history(list(unique_items))
        
    except Exception as e:
        logger.error(f"Error updating history for cities: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update historical market data")
    parser.add_argument("--region", default="Americas", 
                      choices=["Europe", "Americas", "Asia"],
                      help="API region to use")
    
    args = parser.parse_args()
    update_history_for_cities(region=args.region) 