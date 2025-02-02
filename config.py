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
    "Fort Sterling"
]


# Data storage settings
STORAGE = {
    'popular_items_dir': 'popular_items',
    'cache_dir': 'cache',
    'data_refresh_minutes': 15  # How often to refresh market data
}
