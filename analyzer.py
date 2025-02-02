# analyzer.py

def calculate_flip_opportunities(market_data, popular_items):
    """
    Given market data from the API and a dictionary of popular items per city,
    compute the flip opportunities.
    
    Parameters:
      market_data: dict mapping city names to lists of market data entries
                  Each market data entry contains price info for an item in that city
      popular_items: dict mapping city names to lists of popular item entries.
                     Each popular item entry includes:
                        - "unique_name": the item identifier
                        - "volume": estimated daily volume
                        - "average_price": average item price
                        - "name": human readable name

    Returns:
      A dictionary mapping each city to a list of flip opportunities, sorted by potential profit.
    """
    # Market fees
    MARKET_TAX = 0.025  # 2.5% tax on both buy and sell orders
    VOLUME_CAPTURE = 0.10  # Assume we can capture 10% of daily volume
    
    opportunities = {}
    
    for city, city_market_data in market_data.items():
        opportunities[city] = []
        
        # Build an index for quick lookup of market data by item_id
        data_index = {record["item_id"]: record for record in city_market_data}
        
        # Process each popular item in this city
        for item in popular_items[city]:
            item_id = item.get("unique_name")
            if not item_id:
                continue

            record = data_index.get(item_id)
            if not record:
                continue  # No market data for this item

            # Calculate actual volume we expect to flip
            daily_volume = round(item.get("volume", 0))
            expected_volume = round(daily_volume * VOLUME_CAPTURE)

            # Calculate costs and fees for one unit
            buy_price = round(record["buy_price_max"])
            sell_price = round(record["sell_price_min"])
            
            # Calculate fees per unit
            buy_order_fee = round(buy_price * MARKET_TAX)
            sell_order_fee = round(sell_price * MARKET_TAX)
            
            # Calculate actual margin per unit after fees
            flip_margin = round(sell_price - buy_price - buy_order_fee - sell_order_fee)

            if flip_margin <= 0:
                continue  # Skip if not profitable

            # Calculate total potential profit including volume and fees
            potential_profit = round(flip_margin * expected_volume)
            
            # Calculate return on investment (ROI)
            total_investment = round((buy_price + buy_order_fee + sell_order_fee) * expected_volume)
            roi_percent = round((potential_profit / total_investment) * 100 if total_investment > 0 else 0, 1)

            opportunities[city].append({
                "item_id": item_id,
                "name": item.get("name"),
                "flip_margin": flip_margin,
                "daily_volume": daily_volume,
                "expected_volume": expected_volume,
                "potential_profit": potential_profit,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "buy_order_fee": buy_order_fee,
                "sell_order_fee": sell_order_fee,
                "total_fees": round(buy_order_fee + sell_order_fee),
                "total_investment": total_investment,
                "roi_percent": roi_percent,
                "average_price": round(item.get("average_price") or 0),
                "timestamp": record.get("sell_price_min_date")
            })

        # Sort opportunities for each city by potential profit
        opportunities[city].sort(key=lambda x: x["potential_profit"], reverse=True)

    return opportunities
