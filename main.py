# main.py
import argparse
from api_client import APIClient
from data_storage import load_popular_items
from analyzer import calculate_flip_opportunities
from config import CITIES
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request


def process_market_data(args=None):
    """
    Process market data and return opportunities. Can be called directly or via command line.
    
    Args:
        args: Optional list of command line arguments. If None, uses sys.argv[1:]
    """
    parser = argparse.ArgumentParser(description="Market Flipping Tool")
    parser.add_argument("--region", default="Americas", help="API region (Europe, Americas, Asia)")
    parser.add_argument("--sort", choices=["profit", "roi"], default="profit", 
                      help="Sort by total profit or return on investment")
    parser.add_argument("--output", default="market_opportunities",
                      help="Output folder path")
    parser.add_argument("--web", action="store_true",
                      help="Launch web interface instead of writing to file")
    
    parsed_args = parser.parse_args(args)

    # Load the popular items for all configured cities
    popular_items = load_popular_items()

    # Initialize API client
    client = APIClient(region=parsed_args.region)
    
    # Process each city separately
    market_data = {}
    for city in CITIES:
        city_items = [item["unique_name"] for item in popular_items[city]]
        city_market_data = client.get_market_data(city_items, city)
        market_data[city] = city_market_data

    # Analyze the data
    profit_opportunities = calculate_flip_opportunities(market_data, popular_items)

    # Sort based on user preference
    sort_key = "roi_percent" if parsed_args.sort == "roi" else "potential_profit"
    for city in profit_opportunities:
        profit_opportunities[city].sort(key=lambda x: x[sort_key], reverse=True)

    if parsed_args.web:
        # Return the data for web viewer
        return profit_opportunities
    else:
        # Write to file as before
        write_opportunities_to_file(profit_opportunities, parsed_args.output)


def write_opportunities_to_file(profit_opportunities, output_dir):
    """Write opportunities to a text file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"opportunities_{timestamp}.txt")

    with open(output_file, "w") as f:
        for location, items in profit_opportunities.items():
            f.write(f"\n{'='*120}\n")
            f.write(f"Location: {location}\n")
            f.write(f"{'='*120}\n\n")
            
            # Header
            f.write(f"{'Item Name':<40} | {'Qual':>4} | "
                   f"{'Buy@':>10} | {'Sell@':>10} | "
                   f"{'Avg@':>10} | {'B/Avg%':>7} | "
                   f"{'S/Avg%':>7} | {'Margin':>8} | "
                   f"{'Volume':>6} | {'Max Adj':>8} | "
                   f"{'ROI %':>8} | {'Profit/day':>12} | {'Investment':>12}\n")
            
            f.write(f"{'-'*125}\n")
            
            # Data rows (top 50)
            for entry in items[:50]:
                f.write(
                    f"{entry['name']:<40} | "
                    f"{entry['quality']:>4d} | "
                    f"{entry['buy_price']:>10,} | "
                    f"{entry['sell_price']:>10,} | "
                    f"{entry['average_price']:>10,} | "
                    f"{entry['buy_price_ratio']:>7.1f}% | "
                    f"{entry['sell_price_ratio']:>7.1f}% | "
                    f"{entry['flip_margin']:>8,} | "
                    f"{entry['expected_volume']:>6.0f} | "
                    f"{entry['max_adjustments']:>8d} | "
                    f"{entry['roi_percent']:>8.1f}% | "
                    f"{entry['potential_profit']:>12,} | "
                    f"{entry['total_investment']:>12,}\n"
                )
            
            f.write("\n")
            f.write("Note: 'Max Adj' shows how many additional price adjustments can be made before losing profitability\n")
            f.write("      'B/Avg%' and 'S/Avg%' show how buy/sell prices compare to average (negative = below average)\n\n")

    print(f"\nResults have been written to {output_file}")


def main():
    """Entry point that handles both web and file output modes."""
    parser = argparse.ArgumentParser(description="Market Flipping Tool")
    parser.add_argument("--web", action="store_true",
                      help="Launch web interface instead of writing to file")
    args, remaining_args = parser.parse_known_args()

    if args.web:
        # Import Flask-related code only if web mode is requested
        from web_viewer import app
        app.run(debug=True)
    else:
        # Process market data and write to file
        process_market_data(remaining_args)


if __name__ == "__main__":
    main()
