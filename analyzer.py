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
    # Market fees and trading parameters
    SETUP_FEE = 0.025  # 2.5% setup fee on both buy and sell orders
    PREMIUM_TAX = 0.04  # 4% premium tax on sell orders only
    PRICE_ADJUSTMENTS = 1  # Number of times we expect to adjust order prices
    VOLUME_CAPTURE = 0.02  # Assume we can capture 2% of daily volume with one order
    
    # Quality-based volume distribution (percentage of total volume)
    QUALITY_VOLUME_DISTRIBUTION = {
        1: 1.0,    # Normal quality gets full volume
        2: 0.40,   # 40% of total volume
        3: 0.30,   # 25% of total volume
        4: 0.30,   # 10% of total volume
        5: 0.01    # 5% of total volume
    }
    
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

            # Get quality from the record
            quality = record.get("quality", 0)

            # Calculate quality-adjusted volume
            daily_volume = round(item.get("volume", 0))
            
            # Apply quality-based volume adjustment
            quality_multiplier = QUALITY_VOLUME_DISTRIBUTION.get(quality, 0)
            quality_adjusted_volume = round(daily_volume * quality_multiplier)
            
            # Then apply standard volume capture
            expected_volume = round(quality_adjusted_volume * VOLUME_CAPTURE)

            # Calculate base prices
            buy_price = round(record["buy_price_max"])
            sell_price = round(record["sell_price_min"])
            average_price = round(item.get("average_price") or 0)
            
            # Calculate price position relative to average
            buy_price_ratio = round((buy_price / average_price - 1) * 100, 1) if average_price else 0
            sell_price_ratio = round((sell_price / average_price - 1) * 100, 1) if average_price else 0
            
            # Calculate fees per unit including price adjustments
            buy_setup_fees = round(buy_price * SETUP_FEE * (PRICE_ADJUSTMENTS + 1))
            sell_setup_fees = round(sell_price * SETUP_FEE * (PRICE_ADJUSTMENTS + 1))
            sell_premium_tax = round(sell_price * PREMIUM_TAX)
            
            total_fees = round(buy_setup_fees + sell_setup_fees + sell_premium_tax)
            
            # Calculate actual margin per unit after all fees
            flip_margin = round(sell_price - buy_price - total_fees)

            if flip_margin <= 0:
                continue  # Skip if not profitable

            # Calculate max possible price adjustments before profit is gone
            base_setup_fee = (buy_setup_fees + sell_setup_fees) / 2
            max_adjustments = int(flip_margin / base_setup_fee) - 1  # -1 because one adjustment is already included
            max_adjustments = max(0, max_adjustments)

            # Calculate total potential profit including volume
            potential_profit = round(flip_margin * expected_volume)
            
            # Calculate return on investment (ROI)
            total_investment = round((buy_price + buy_setup_fees) * expected_volume)
            roi_percent = round((potential_profit / total_investment) * 100 if total_investment > 0 else 0, 1)

            opportunities[city].append({
                "item_id": item_id,
                "name": item.get("name"),
                "quality": quality,
                "flip_margin": flip_margin,
                "daily_volume": daily_volume,
                "expected_volume": expected_volume,
                "potential_profit": potential_profit,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "buy_setup_fees": buy_setup_fees,
                "sell_setup_fees": sell_setup_fees,
                "sell_premium_tax": sell_premium_tax,
                "total_fees": total_fees,
                "total_investment": total_investment,
                "roi_percent": roi_percent,
                "average_price": average_price,
                "buy_price_ratio": buy_price_ratio,
                "sell_price_ratio": sell_price_ratio,
                "max_adjustments": max_adjustments,
                "timestamp": record.get("sell_price_min_date")
            })

        # Sort opportunities for each city by potential profit
        opportunities[city].sort(key=lambda x: x["potential_profit"], reverse=True)

    return opportunities
