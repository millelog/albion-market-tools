# Context for Albion Online Market Flipping Tool

This repository contains a Python-based tool designed to analyze market data from Albion Online and identify profitable “flip” opportunities. A flip opportunity arises when an item can be purchased at a low price from buy orders and resold at a higher price via sell orders, with the potential profit weighted by its daily trading volume.

---

## 1. Project Overview

- **Purpose:**  
  The tool aggregates market data from the Albion Online API and compares it against a locally maintained JSON file of popular items (with associated daily volumes) for various cities. It then calculates the potential daily profit for flipping each item based on the difference between the best available buy and sell prices, and sorts these opportunities by profitability.

- **Profit Calculation:**  
  For each item in a given city:
  - **API Data Fields:**  
    - `sell_price_min`: The lowest sell order price.
    - `buy_price_max`: The highest buy order price.
  - **Flip Margin:**  
    ```python
    flip_margin = buy_price_max - sell_price_min
    ```
  - **Potential Daily Profit:**  
    ```python
    potential_profit = flip_margin * daily_volume
    ```
    This calculation is only considered when the margin is positive.

- **Key Considerations:**  
  - **High-Volume Items:** Only popular items (as defined in the JSON data) are analyzed to ensure that identified opportunities are practical and have sufficient trading volume.
  - **API Rate Limits & URL Length:**  
    - API rate limits: 180 requests per minute and 300 per 5 minutes.
    - Maximum URL length: 4096 characters.  
    The tool batches requests using a helper function to maximize data per call without exceeding this limit.
  - **Gzip Compression:**  
    The API client uses gzip compression (via HTTP headers) to reduce bandwidth usage.

---

## 2. Repository Structure

The repository is organized into modular components to separate concerns and ease maintenance:

market_flipper/ ├── init.py ├── main.py # Orchestrates the overall workflow ├── config.py # Contains API endpoints, base URLs, and rate limit constants ├── api_client.py # Manages API calls, URL construction, and batching ├── data_storage.py # Loads and saves JSON data (e.g., popular items by city) ├── analyzer.py # Processes market data and computes flip opportunities └── utils.py # Helper functions (e.g., URL batching, rate limiting)

markdown
Copy

- **main.py:**  
  Initializes the tool, parses command-line arguments (e.g., API region and popular items file path), and ties together the API client, data storage, and analysis components.

- **config.py:**  
  Defines constants such as:
  - API base URLs (for regions like Americas, Europe, Asia).
  - Endpoint templates (e.g., `/api/v2/stats/prices/{items}.json?locations={locations}&qualities={quality}`).
  - API rate limits and the maximum URL length.

- **api_client.py:**  
  Responsible for:
  - Building the API URL by combining item IDs and locations.
  - Batching items (using `utils.split_into_batches`) so that each URL stays within the 4096‑character limit.
  - Handling HTTP requests with appropriate headers (including gzip compression).

- **data_storage.py:**  
  Provides functions to load and save JSON files containing popular items. Each popular item entry includes:
  - `item` (or `item_id`): The unique identifier (e.g., `"T4_BAG"`).
  - `quality`: Quality level (e.g., `2`).
  - `enchantment`: Optional enchantment level (defaults to 0 if missing).
  - `daily_volume`: Estimated daily trading volume used for profit weighting.

- **analyzer.py:**  
  Implements the business logic:
  - Uses API data (which includes fields like `sell_price_min` and `buy_price_max`) to compute the flip margin and potential profit.
  - Filters out non-profitable opportunities (where margin is ≤ 0).
  - Sorts the opportunities for each city by potential profit in descending order.

- **utils.py:**  
  Contains utility functions such as:
  - `split_into_batches`: Breaks the list of item IDs into batches ensuring that when inserted into the URL template, the final URL does not exceed 4096 characters.
  - (Optional) Other helpers for rate limiting or data formatting as needed.

---

## 3. API Integration Details

- **API Endpoint Example:**  
https://west.albion-online-data.com/api/v2/stats/prices/T4_BAG,T5_BAG?locations=Caerleon,Bridgewatch&qualities=2

kotlin
Copy
This endpoint returns JSON data structured as follows:

```json
[
  {
    "item_id": "T4_BAG",
    "city": "Bridgewatch",
    "quality": 2,
    "sell_price_min": 3325,
    "sell_price_min_date": "2025-02-02T05:10:00",
    "sell_price_max": 3325,
    "sell_price_max_date": "2025-02-02T05:10:00",
    "buy_price_min": 2001,
    "buy_price_min_date": "2025-02-02T05:05:00",
    "buy_price_max": 2547,
    "buy_price_max_date": "2025-02-02T05:05:00"
  },
  {
    "item_id": "T4_BAG",
    "city": "Caerleon",
    "quality": 2,
    "sell_price_min": 4953,
    "sell_price_min_date": "2025-02-02T01:50:00",
    "sell_price_max": 5000,
    "sell_price_max_date": "2025-02-02T01:50:00",
    "buy_price_min": 15,
    "buy_price_min_date": "2025-02-02T01:50:00",
    "buy_price_max": 2695,
    "buy_price_max_date": "2025-02-02T01:50:00"
  },
  ...
]
Data Fields of Interest:
item_id: Identifier for the item.
city: The location for which the data applies.
quality: Quality level of the item.
sell_price_min & sell_price_min_date: Minimum sell price and its timestamp.
buy_price_max & buy_price_max_date: Maximum buy price and its timestamp.
4. Maintenance and Extension Guidelines
Modular Design:
Each component (API client, analyzer, data storage, etc.) is separated to facilitate testing, debugging, and future extension. Changes in one area (for instance, an API update) should only require adjustments in the relevant module (e.g., api_client.py).

Batching & Rate Limiting:
The tool employs batching (in utils.py) to maximize efficiency without exceeding the 4096-character URL limit. It’s important to maintain and update the batching logic if API endpoint structures or parameter requirements change.

API Data Mapping:
The analyzer currently expects specific fields from the API response. If the API’s data structure changes, update the corresponding field names and calculation logic in analyzer.py.

Configuration Updates:
Any changes to API endpoints, regions, or rate limits should be made in config.py to keep all settings centralized.

Testing and Debugging:

Unit Testing: Consider adding tests for each module to verify URL batching, API interactions, and the profit calculations.
Logging: Implement or enhance logging (if needed) to trace API calls, errors, or unexpected data structures.
Documentation: Update this context file and inline code comments as the code evolves.
5. Getting Started
Dependencies:
Ensure that the required libraries (e.g., requests) are installed.

Configuration:

Verify that config.py reflects the correct API endpoints and rate limit settings.
Populate the popular items JSON file with the required structure (per city).
Running the Tool:
Execute main.py from the command line. Example:

bash
Copy
python main.py --region Europe --popular_items popular_items.json






