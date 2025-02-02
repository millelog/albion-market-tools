# api_client.py
import requests
from config import API_HOSTS, API_ENDPOINTS, MAX_URL_LENGTH
from utils import split_into_batches


class APIClient:
    def __init__(self, region='Europe'):
        self.base_url = API_HOSTS[region]
        self.session = requests.Session()
        # Request Gzip-compressed responses
        self.session.headers.update({
            "Accept-Encoding": "gzip, deflate"
        })

    def build_url(self, endpoint_name, items, location):
        """Build API URL for a specific location."""
        items_str = ",".join(items)

        endpoint_template = API_ENDPOINTS[endpoint_name]
        return self.base_url + endpoint_template.format(
            items=items_str,
            locations=location
        )

    def get_market_data(self, items, location):
        """
        Fetch market data for the given items in a specific location.
        Filters out entries with zero prices.
        
        Parameters:
            items: list of unique_name identifiers
            location: single city name
            
        Returns:
            List of market data entries with non-zero prices for the location
        """
        # Split items into batches to stay within URL length limits
        batches = split_into_batches(
            items=items,
            max_url_length=MAX_URL_LENGTH,
            base_url=self.base_url,
            endpoint_template=API_ENDPOINTS['current_prices_json']
        )

        results = []
        for batch in batches:
            url = self.build_url('current_prices_json', batch, location)
            response = self.session.get(url)
            response.raise_for_status()
            
            # Filter out entries with zero prices
            valid_entries = [
                entry for entry in response.json()
                if entry.get("buy_price_max", 0) > 0 
                and entry.get("sell_price_min", 0) > 0
            ]
            results.extend(valid_entries)

        return results
