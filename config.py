# config.py

# API Hosts by region
API_HOSTS = {
    'Americas': "https://west.albion-online-data.com",
    'Asia':     "https://east.albion-online-data.com",
    'Europe':   "https://europe.albion-online-data.com",
}

# Endpoints (using format-string templates)
API_ENDPOINTS = {
    'current_prices_json': "/api/v2/stats/prices/{items}.json?locations={locations}",
    'history_json': "/api/v2/stats/history/{items}.json?time-scale={time_scale}",
    # Add other endpoints as needed.
}

# Rate limit settings
RATE_LIMITS = {
    'per_minute': 180,
    'per_5_minutes': 300,
}

# Maximum URL length allowed
MAX_URL_LENGTH = 4096

# Cities to analyze
CITIES = [
    "Lymhurst",
    "Fort Sterling",
    "Martlock",
    "Thetford",
    "Bridgewatch",
    "Caerleon"    
]

# Database settings
DB = {
    'path': 'data/market_history.db',
    'min_data_points': 5,  # Minimum number of data points needed for valid averages
    'max_history_days': 30  # Maximum number of days of history to consider
}

# Data storage settings
STORAGE = {
    'popular_items_dir': 'popular_items',
    'cache_dir': 'cache',
    'data_refresh_minutes': 15  # How often to refresh market data
}

# Flip calculator configuration
FLIP_CONFIG = {
    'min_profit_threshold': 100000,  # Minimum potential profit to be considered an opportunity
    'items_to_analyze': 500,  # Number of top items to analyze per location
    'opportunities_to_show': 50,  # Number of top opportunities to display per location
}
