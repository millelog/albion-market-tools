
# Albion Online Market Flipping Tool

A Python-based tool for analyzing Albion Online market data to identify profitable flip opportunities. The tool fetches current market prices from the Albion Online API, compares these prices against a curated list of popular items (with daily volume estimates), and calculates the potential daily profit for flipping items across various cities.

---

## Table of Contents

- [Features](#features)
- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Development & Maintenance](#development--maintenance)
- [License](#license)

---

## Features

- **API Integration:** Retrieves market data from Albion Online endpoints using batched API calls to stay within URL length and rate limit constraints.
- **Flip Opportunity Analysis:** Calculates the profit margin between the best available buy and sell prices for popular items.
- **Volume-Weighted Profit:** Uses daily volume estimates to prioritize high-traffic items.
- **Multi-City Support:** Evaluates opportunities across multiple cities (e.g., Caerleon, Bridgewatch).
- **Efficient Data Handling:** Batches API queries and uses gzip compression to minimize bandwidth usage.

---

## Overview

The Albion Online Market Flipping Tool is designed for players and traders who want to automate the process of identifying profitable items to flip on the market. By comparing API data fields such as `sell_price_min` and `buy_price_max` with daily volume estimates stored in a JSON file, the tool computes a "flip margin" and multiplies it by the item’s daily volume to determine potential daily profit.

For example, for each item/city combination:
- **Flip Margin Calculation:**
  ```python
  flip_margin = buy_price_max - sell_price_min
  ```
- **Potential Daily Profit:**
  ```python
  potential_profit = flip_margin * daily_volume
  ```
Only opportunities where `flip_margin > 0` are considered.

The tool uses batching utilities to ensure that each API request URL does not exceed 4096 characters, thereby making efficient use of the API rate limits.

---

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/albion-market-flipper.git
   cd albion-market-flipper
   ```

2. **Create a Virtual Environment (Optional but Recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   The primary dependency is the `requests` library. Install it via pip:
   ```bash
   pip install requests
   ```

---

## Configuration

### API Configuration

- **API Endpoints & Regions:**  
  The API endpoints and base URLs for different regions (Americas, Europe, Asia) are defined in `config.py`. Update these values if the API endpoints change.

- **Rate Limits & URL Length:**  
  Rate limit settings and the maximum URL length (4096 characters) are also maintained in `config.py`.

### Popular Items JSON

- **Data Structure:**  
  The popular items file (e.g., `popular_items.json`) should be structured as follows:
  ```json
  {
      "Caerleon": [
          {
              "item": "T4_BAG",
              "quality": 2,
              "enchantment": 0,
              "daily_volume": 150
          },
          {
              "item": "T5_BAG",
              "quality": 2,
              "enchantment": 0,
              "daily_volume": 75
          }
      ],
      "Bridgewatch": [
          {
              "item": "T4_BAG",
              "quality": 2,
              "enchantment": 0,
              "daily_volume": 120
          }
      ]
  }
  ```
  Adjust the values according to your trading volume estimates and the items you wish to monitor.

---

## Usage

The tool is run via the command line using `main.py`. The following command-line arguments are supported:

- `--region`: The API region to query (default is `Europe`). Valid options include `Europe`, `Americas`, or `Asia`.
- `--popular_items`: Path to the JSON file containing popular items data (default is `popular_items.json`).

### Example

```bash
python main.py --region Europe --popular_items popular_items.json
```

On execution, the tool will:
1. Load the popular items data.
2. Consolidate a unique list of item identifiers.
3. Batch API calls to fetch current market prices.
4. Analyze the fetched data to compute flip opportunities.
5. Print a sorted list of the best flip opportunities per city.

---

## Project Structure

```
market_flipper/
├── __init__.py
├── main.py              # Entry point for running the tool
├── config.py            # Contains API endpoints, rate limits, and other configuration constants
├── api_client.py        # Manages API interactions, URL construction, and batching
├── data_storage.py      # Handles reading/writing the popular items JSON
├── analyzer.py          # Contains business logic for calculating flip opportunities
└── utils.py             # Utility functions (e.g., URL batching)
```

- **main.py:** Orchestrates the overall workflow.
- **config.py:** Centralizes configuration details.
- **api_client.py:** Builds API URLs and retrieves data, ensuring each URL stays within limits.
- **data_storage.py:** Loads and saves the JSON file that contains popular items per city.
- **analyzer.py:** Processes market data, computes margins, and sorts profitable opportunities.
- **utils.py:** Contains helper functions like batching the item list for API calls.

---

## Development & Maintenance

- **Modular Design:**  
  Each component is designed to be modular and testable. Changes to one module (e.g., API endpoint updates) require minimal modifications to others.

- **Batching & Rate Limiting:**  
  The `split_into_batches` function in `utils.py` ensures that the API URL length does not exceed the maximum allowed limit. Adjust this logic if API parameters change.

- **Extensibility:**  
  New features or changes in the API can be managed by updating the corresponding module (e.g., `analyzer.py` for changes in flip calculations).

- **Testing:**  
  Consider adding unit tests to validate individual components such as URL batching, API client requests, and profit calculations.

- **Logging:**  
  Incorporate logging for better traceability of API requests and data processing, especially if running the tool in a production environment.

