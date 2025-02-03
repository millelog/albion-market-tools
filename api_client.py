# api_client.py
import requests
import time
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import List, Dict, Any
from config import API_HOSTS, API_ENDPOINTS, MAX_URL_LENGTH

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Tracks and enforces multiple API rate limits."""
    def __init__(self):
        """Initialize rate limiters for both time windows."""
        # Track requests for 1-minute window (180 requests)
        self.requests_1min = deque()
        # Track requests for 5-minute window (300 requests)
        self.requests_5min = deque()
    
    def wait_if_needed(self):
        """
        Check if we need to wait before making another request.
        Enforces both 1-minute and 5-minute rate limits.
        """
        now = datetime.now()
        cutoff_1min = now - timedelta(minutes=1)
        cutoff_5min = now - timedelta(minutes=5)
        
        # Remove old requests from 1-minute window
        while self.requests_1min and self.requests_1min[0] < cutoff_1min:
            self.requests_1min.popleft()
            
        # Remove old requests from 5-minute window
        while self.requests_5min and self.requests_5min[0] < cutoff_5min:
            self.requests_5min.popleft()
        
        # Check 1-minute limit
        if len(self.requests_1min) >= 180:
            wait_time = (self.requests_1min[0] - cutoff_1min).total_seconds()
            if wait_time > 0:
                logger.info(f"1-minute rate limit reached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                # Recursive call to ensure we're now under limit
                self.wait_if_needed()
                return
        
        # Check 5-minute limit
        if len(self.requests_5min) >= 300:
            wait_time = (self.requests_5min[0] - cutoff_5min).total_seconds()
            if wait_time > 0:
                logger.info(f"5-minute rate limit reached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                # Recursive call to ensure we're now under limit
                self.wait_if_needed()
    
    def add_request(self):
        """Record a new request in both time windows."""
        now = datetime.now()
        self.requests_1min.append(now)
        self.requests_5min.append(now)

class APIClient:
    def __init__(self, region='Americas'):
        self.base_url = API_HOSTS[region]
        self.session = requests.Session()
        # Request Gzip-compressed responses
        self.session.headers.update({
            "Accept-Encoding": "gzip, deflate"
        })
        # Initialize rate limiter with both limits
        self.rate_limiter = RateLimiter()

    def _split_into_batches(self, items, max_url_length, endpoint_template):
        """
        Splits the list of items into batches so that the URL formed with the given endpoint_template 
        does not exceed max_url_length.
        
        The endpoint_template is expected to be a string with placeholders {items} and {locations}.
        For example: "/api/v2/stats/prices/{items}.json?locations={locations}"
        
        Parameters:
          items: list of unique_name identifiers (strings, e.g., "T4_BAG", "T8_PLANKS")
          max_url_length: maximum allowed URL length (e.g., 4096)
          endpoint_template: string template for the endpoint
          
        Returns:
          A list of lists, where each inner list is a batch of items that can be safely inserted into the URL.
        """
        # Build the constant part of the URL (with empty items placeholder)
        # Handle both price and history endpoints by providing default values for all possible parameters
        dummy_url = self.base_url + endpoint_template.format(items="", locations="City", time_scale="24")
        available_length = max_url_length - len(dummy_url)

        batches = []
        current_batch = []
        current_length = 0

        for item in items:
            # Each item will be separated by a comma (if not the first in the batch)
            additional_length = len(item) + (1 if current_batch else 0)
            if current_length + additional_length > available_length:
                batches.append(current_batch)
                current_batch = [item]
                current_length = len(item)
            else:
                current_batch.append(item)
                current_length += additional_length

        if current_batch:
            batches.append(current_batch)

        return batches

    def build_url(self, endpoint_name, items, location=None, time_scale=None):
        """
        Build API URL for a specific endpoint.
        
        Args:
            endpoint_name: Name of the endpoint from API_ENDPOINTS
            items: List of item IDs
            location: Optional location parameter
            time_scale: Optional time scale parameter for history endpoint
        """
        items_str = ",".join(items)
        endpoint_template = API_ENDPOINTS[endpoint_name]
        
        # Build URL based on endpoint type
        if endpoint_name == 'history_json':
            return self.base_url + endpoint_template.format(
                items=items_str,
                time_scale=time_scale or "24"
            )
        else:
            return self.base_url + endpoint_template.format(
                items=items_str,
                locations=location
            )

    def _make_request(self, url: str) -> List[Dict[str, Any]]:
        """
        Make an API request with rate limiting.
        
        Args:
            url: The URL to request
            
        Returns:
            JSON response data
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        self.rate_limiter.wait_if_needed()
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            self.rate_limiter.add_request()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def get_market_data(self, items: List[str], location: str) -> List[Dict[str, Any]]:
        """
        Fetch market data for the given items in a specific location.
        Filters out entries with zero prices.
        
        Args:
            items: List of unique_name identifiers
            location: Single city name
            
        Returns:
            List of market data entries with non-zero prices for the location
        """
        # Split items into batches to stay within URL length limits
        batches = self._split_into_batches(
            items=items,
            max_url_length=MAX_URL_LENGTH,
            endpoint_template=API_ENDPOINTS['current_prices_json']
        )

        results = []
        for batch in batches:
            url = self.build_url('current_prices_json', batch, location)
            try:
                response_data = self._make_request(url)
                
                # Filter out entries with zero prices
                valid_entries = [
                    entry for entry in response_data
                    if entry.get("buy_price_max", 0) > 1
                    and entry.get("sell_price_min", 0) > 0
                ]
                results.extend(valid_entries)
                
            except requests.exceptions.RequestException:
                logger.warning(f"Failed to fetch market data for batch of {len(batch)} items")
                continue

        return results

    def get_history_data(self, item_ids: List[str], time_scale: str = "24") -> List[Dict[str, Any]]:
        """
        Fetch historical market data for the given items.
        
        Args:
            item_ids: List of unique_name identifiers
            time_scale: Time scale for historical data (e.g., "24" for 24 hours)
            
        Returns:
            List of historical data records, where each record contains:
            - item_id: The item identifier
            - location: The market location
            - quality: Item quality level
            - data: List of historical snapshots, each containing:
                - timestamp: ISO format timestamp
                - item_count: Number of items
                - avg_price: Average price
        """
        # Split items into batches
        batches = self._split_into_batches(
            items=item_ids,
            max_url_length=MAX_URL_LENGTH,
            endpoint_template=API_ENDPOINTS['history_json']
        )

        total_batches = len(batches)
        logger.info(f"Fetching historical data for {len(item_ids)} items in {total_batches} batches")
        
        results = []
        for batch_num, batch in enumerate(batches, 1):
            url = self.build_url('history_json', batch, time_scale=time_scale)
            try:
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
                batch_data = self._make_request(url)
                
                # Filter out entries with no historical data
                valid_entries = [
                    entry for entry in batch_data
                    if entry.get('data') and len(entry['data']) > 0
                ]
                results.extend(valid_entries)
                
                # Log completion percentage
                progress = (batch_num / total_batches) * 100
                logger.info(f"Progress: {progress:.1f}% complete ({len(results)} valid entries so far)")
                
            except requests.exceptions.RequestException:
                logger.warning(f"Failed to fetch historical data for batch {batch_num} ({len(batch)} items)")
                continue

        logger.info(f"Historical data fetch complete. Retrieved {len(results)} valid entries")
        return results
