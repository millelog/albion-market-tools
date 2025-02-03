import logging
from typing import List, Dict, Any, Optional
from api_client import APIClient
from config import CITIES, FLIP_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Market fees and trading parameters
SETUP_FEE = 0.025  # 2.5% setup fee on both buy and sell orders
PREMIUM_TAX = 0.04  # 4% premium tax on sell orders only
PRICE_ADJUSTMENTS = 1  # Number of times we expect to adjust order prices
VOLUME_CAPTURE = 0.01  # Assume we can capture 2% of daily volume with one order

class FlipCalculator:
    def __init__(self, region: str = 'Americas'):
        """
        Initialize the flip calculator with API client.
        
        Args:
            region: API region to use (default: 'Americas')
        """
        self.api_client = APIClient(region=region)
        
    def fetch_current_market_data(self, item_ids: List[str], location: str) -> List[Dict[str, Any]]:
        """
        Fetch current market data for items in a location.
        
        Args:
            item_ids: List of item identifiers
            location: City/location to fetch data for
            
        Returns:
            List of current market data records with non-zero prices
        """
        logger.info(f"Fetching market data for {len(item_ids)} items in {location}")
        
        try:
            market_data = self.api_client.get_market_data(item_ids, location)
            logger.info(f"Retrieved {len(market_data)} market records")
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return []
    
    def calculate_flip_metrics(self, current_data: Dict[str, Any], 
                             historical_volume: float,
                             quality: int) -> Optional[Dict[str, Any]]:
        """
        Calculate flip metrics for an item using current market data.
        
        Args:
            current_data: Current market data for the item
            historical_volume: Historical daily volume (already quality-specific)
            quality: Item quality level
            
        Returns:
            Dictionary containing flip metrics or None if not profitable
        """
        try:
            # Extract base prices
            buy_price = round(current_data.get('buy_price_max', 0))
            sell_price = round(current_data.get('sell_price_min', 0))
            
            # Skip if prices are invalid
            if not all([buy_price, sell_price]):
                return None
                
            # Calculate expected volume based on historical data
            expected_volume = round(historical_volume * VOLUME_CAPTURE)
            
            # Skip if expected volume rounds to 0
            if expected_volume <= 0.5:
                return None
                
            # Calculate fees
            buy_setup_fees = round(buy_price * SETUP_FEE * (PRICE_ADJUSTMENTS + 1))
            sell_setup_fees = round(sell_price * SETUP_FEE * (PRICE_ADJUSTMENTS + 1))
            sell_premium_tax = round(sell_price * PREMIUM_TAX)
            
            total_fees = round(buy_setup_fees + sell_setup_fees + sell_premium_tax)
            
            # Calculate margins and profit
            flip_margin = round(sell_price - buy_price - total_fees)
            
            # Skip if not profitable
            if flip_margin <= 0:
                return None
                
            # Calculate max price adjustments
            base_setup_fee = (buy_setup_fees + sell_setup_fees) / 2
            max_adjustments = max(0, int(flip_margin / base_setup_fee) - 1)
            
            # Calculate final metrics
            potential_profit = round(flip_margin * expected_volume)
            
            # Skip if potential profit is below threshold
            if potential_profit < FLIP_CONFIG['min_profit_threshold']:
                return None
                
            total_investment = round((buy_price + buy_setup_fees) * expected_volume)
            roi_percent = round((potential_profit / total_investment) * 100 if total_investment > 0 else 0, 1)
            
            return {
                'buy_price': buy_price,
                'sell_price': sell_price,
                'flip_margin': flip_margin,
                'expected_volume': expected_volume,
                'buy_setup_fees': buy_setup_fees,
                'sell_setup_fees': sell_setup_fees,
                'sell_premium_tax': sell_premium_tax,
                'total_fees': total_fees,
                'max_adjustments': max_adjustments,
                'potential_profit': potential_profit,
                'total_investment': total_investment,
                'roi_percent': roi_percent,
                'timestamp': current_data.get('sell_price_min_date')
            }
            
        except Exception as e:
            logger.error(f"Error calculating flip metrics: {e}")
            return None
    
    def analyze_flip_opportunities(self, top_items: List[Dict[str, Any]], 
                                 location: str) -> List[Dict[str, Any]]:
        """
        Analyze flip opportunities for top items in a location.
        
        Args:
            top_items: List of top items from analysis module
            location: City/location to analyze
            
        Returns:
            List of items enriched with current market data and flip metrics,
            sorted by potential profit and limited to configured number of opportunities
        """
        # Extract item IDs
        item_ids = [item['item_id'] for item in top_items]
        if not item_ids:
            return []
            
        # Fetch current market data
        current_data = self.fetch_current_market_data(item_ids, location)
        if not current_data:
            return []
            
        # Create lookup for current data
        current_lookup = {
            (record['item_id'], record.get('quality', 1)): record 
            for record in current_data
        }
        
        # Process each item
        opportunities = []
        for item in top_items:
            item_id = item['item_id']
            quality = item.get('quality', 1)
            
            # Get current market data
            current = current_lookup.get((item_id, quality))
            if not current:
                continue
                
            # Calculate flip metrics
            metrics = self.calculate_flip_metrics(
                current_data=current,
                historical_volume=item.get('avg_item_count', 0),
                quality=quality
            )
            
            if metrics:
                opportunities.append({
                    **item,  # Include original item data (including item_name)
                    **metrics  # Add flip metrics
                })
        
        # Sort by potential profit and limit to configured number of opportunities
        opportunities.sort(key=lambda x: x['potential_profit'], reverse=True)
        return opportunities[:FLIP_CONFIG['opportunities_to_show']]

def calculate_flip_opportunities(top_items_by_location: Dict[str, List[Dict[str, Any]]],
                               region: str = 'Americas') -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate flip opportunities for top items across all locations.
    
    Args:
        top_items_by_location: Dictionary mapping locations to their top items
        region: API region to use (default: 'Americas')
        
    Returns:
        Dictionary mapping locations to their flip opportunities
    """
    try:
        calculator = FlipCalculator(region=region)
        
        opportunities = {}
        for location, items in top_items_by_location.items():
            try:
                location_opportunities = calculator.analyze_flip_opportunities(items, location)
                opportunities[location] = location_opportunities
                logger.info(f"Found {len(location_opportunities)} opportunities in {location}")
                
            except Exception as e:
                logger.error(f"Error processing {location}: {e}")
                opportunities[location] = []
                
        return opportunities
        
    except Exception as e:
        logger.error(f"Error calculating flip opportunities: {e}")
        return {} 