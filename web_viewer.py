from flask import Flask, render_template, jsonify, request
from main import process_market_data
import tempfile
import json
import os

app = Flask(__name__)

# Store the current market data in memory
current_data = {}

@app.route('/')
def index():
    # Run the market analysis and capture the output
    temp_dir = tempfile.mkdtemp()
    
    # Run process_market_data with the temporary output location and web flag
    global current_data
    current_data = process_market_data(["--web", "--output", temp_dir])
    
    return render_template('market_viewer.html', data=current_data)

@app.route('/update_prices', methods=['POST'])
def update_prices():
    data = request.json
    city = data['city']
    item_index = int(data['itemIndex'])
    field = data['field']
    value = int(data['value'])
    
    # Update the specified price
    item = current_data[city][item_index]
    item[field] = value
    
    # Recalculate derived values
    updated_item = recalculate_metrics(item)
    current_data[city][item_index] = updated_item
    
    return jsonify(updated_item)

def recalculate_metrics(item):
    """Recalculate all derived metrics based on new buy/sell prices."""
    # Constants from analyzer.py
    SETUP_FEE = 0.025
    PREMIUM_TAX = 0.04
    PRICE_ADJUSTMENTS = 1
    
    buy_price = item['buy_price']
    sell_price = item['sell_price']
    average_price = item['average_price']
    expected_volume = item['expected_volume']
    
    # Recalculate all metrics
    buy_price_ratio = round((buy_price / average_price - 1) * 100, 1) if average_price else 0
    sell_price_ratio = round((sell_price / average_price - 1) * 100, 1) if average_price else 0
    
    buy_setup_fees = round(buy_price * SETUP_FEE * (PRICE_ADJUSTMENTS + 1))
    sell_setup_fees = round(sell_price * SETUP_FEE * (PRICE_ADJUSTMENTS + 1))
    sell_premium_tax = round(sell_price * PREMIUM_TAX)
    
    total_fees = round(buy_setup_fees + sell_setup_fees + sell_premium_tax)
    flip_margin = round(sell_price - buy_price - total_fees)
    
    base_setup_fee = (buy_setup_fees + sell_setup_fees) / 2
    max_adjustments = max(0, int(flip_margin / base_setup_fee) - 1)
    
    potential_profit = round(flip_margin * expected_volume)
    total_investment = round((buy_price + buy_setup_fees) * expected_volume)
    roi_percent = round((potential_profit / total_investment) * 100 if total_investment > 0 else 0, 1)
    
    # Update and return the item with new calculations
    item.update({
        'buy_price_ratio': buy_price_ratio,
        'sell_price_ratio': sell_price_ratio,
        'buy_setup_fees': buy_setup_fees,
        'sell_setup_fees': sell_setup_fees,
        'sell_premium_tax': sell_premium_tax,
        'total_fees': total_fees,
        'flip_margin': flip_margin,
        'max_adjustments': max_adjustments,
        'potential_profit': potential_profit,
        'total_investment': total_investment,
        'roi_percent': roi_percent
    })
    
    return item

def parse_opportunities_file(raw_data):
    """Parse the opportunities text file into structured data."""
    # Implementation to parse the text file format into a dictionary
    # This would need to be implemented based on your exact file format
    # Return format: {city: [item_data, ...], ...}
    pass

if __name__ == '__main__':
    app.run(debug=True) 