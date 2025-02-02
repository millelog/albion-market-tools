# main.py
import argparse
from api_client import APIClient
from data_storage import load_popular_items
from analyzer import calculate_flip_opportunities
from config import CITIES


def main():
    parser = argparse.ArgumentParser(description="Market Flipping Tool")
    parser.add_argument("--region", default="Americas", help="API region (Europe, Americas, Asia)")
    parser.add_argument("--sort", choices=["profit", "roi"], default="roi", 
                      help="Sort by total profit or return on investment")
    args = parser.parse_args()

    # Load the popular items for all configured cities
    popular_items = load_popular_items()

    # Initialize API client
    client = APIClient(region=args.region)
    
    # Process each city separately
    market_data = {}
    for city in CITIES:
        # Get unique items for this city
        city_items = [item["unique_name"] for item in popular_items[city]]
        
        # Get market data for this city
        city_market_data = client.get_market_data(city_items, city)
        market_data[city] = city_market_data

    # Analyze the data to compute potential profit per day per location
    profit_opportunities = calculate_flip_opportunities(market_data, popular_items)

    # Sort based on user preference
    sort_key = "roi_percent" if args.sort == "roi" else "potential_profit"
    for city in profit_opportunities:
        profit_opportunities[city].sort(key=lambda x: x[sort_key], reverse=True)

    # Output results (top 20 for each location)
    for location, items in profit_opportunities.items():
        print(f"\nLocation: {location}")
        print(f"{'Item Name':<40} | {'Margin':>8} | {'Volume':>8} | {'ROI %':>8} | {'Profit/day':>12} | {'Investment':>12}")
        print("-" * 95)
        for entry in items[:20]:
            print(
                f"{entry['name']:<40} | "
                f"{entry['flip_margin']:>8,} | "
                f"{entry['expected_volume']:>8,.0f} | "
                f"{entry['roi_percent']:>8.1f} | "
                f"{entry['potential_profit']:>12,} | "
                f"{entry['total_investment']:>12,}"
            )


if __name__ == "__main__":
    main()
