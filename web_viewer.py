#web_viewer.py
from flask import Flask, render_template, jsonify, request
from analysis import MarketAnalyzer
from flip_calculator import FlipCalculator, calculate_flip_opportunities, SETUP_FEE, PREMIUM_TAX, PRICE_ADJUSTMENTS, VOLUME_CAPTURE
from history_fetcher import update_history_for_cities
from database import MarketDatabase
from config import CITIES, FLIP_CONFIG
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize core components
analyzer = MarketAnalyzer()
calculator = FlipCalculator()
db = MarketDatabase()

# Store the current market data in memory
current_data = {}

@app.route('/')
def index():
    """Render the main page with current market opportunities."""
    try:
        # Get top items from historical analysis
        top_items = analyzer.get_all_locations_top_items()
        
        # Calculate current flip opportunities
        global current_data
        current_data = calculate_flip_opportunities(top_items)
        
        return render_template('market_viewer.html', data=current_data)
        
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return render_template('error.html', error=str(e))

@app.route('/refresh-history', methods=['POST'])
def refresh_history():
    """Refresh historical market data in the database."""
    try:
        # Update historical data
        update_history_for_cities()
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Historical data refreshed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error refreshing history: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/top-items/<location>')
def get_top_items(location: str):
    """Get top items for a specific location based on historical data."""
    try:
        # Validate location
        if location not in CITIES:
            return jsonify({
                'status': 'error',
                'message': f'Invalid location: {location}'
            }), 400
            
        # Get top items for location
        items = analyzer.get_top_items(
            location=location,
            limit=request.args.get('limit', 50, type=int),
            min_volume=request.args.get('min_volume', None, type=float)
        )
        
        return jsonify({
            'status': 'success',
            'location': location,
            'items': items
        })
        
    except Exception as e:
        logger.error(f"Error getting top items for {location}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/flip-analysis/<location>')
def analyze_flips(location: str):
    """Analyze current flip opportunities for a location."""
    try:
        # Validate location
        if location not in CITIES:
            return jsonify({
                'status': 'error',
                'message': f'Invalid location: {location}'
            }), 400
            
        # Get top items first
        items = analyzer.get_top_items(
            location=location,
            limit=request.args.get('limit', 50, type=int)
        )
        
        # Calculate flip opportunities
        opportunities = calculator.analyze_flip_opportunities(items, location)
        
        return jsonify({
            'status': 'success',
            'location': location,
            'opportunities': opportunities
        })
        
    except Exception as e:
        logger.error(f"Error analyzing flips for {location}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/delete_item', methods=['POST'])
def delete_item():
    """Delete an item from the current market data."""
    try:
        data = request.json
        city = data['city']
        item_index = int(data['itemIndex'])
        
        # Validate the city and index
        if city not in current_data or item_index >= len(current_data[city]):
            return jsonify({
                'status': 'error',
                'message': 'Invalid city or item index'
            }), 400
        
        # Remove the item from the current data
        current_data[city].pop(item_index)
        
        return jsonify({
            'status': 'success',
            'message': 'Item deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/update_prices', methods=['POST'])
def update_prices():
    """Update item prices and recalculate metrics."""
    try:
        data = request.json
        city = data['city']
        item_index = int(data['itemIndex'])
        field = data['field']
        value = int(data['value'])
        
        # Validate the city and index
        if city not in current_data or item_index >= len(current_data[city]):
            return jsonify({
                'status': 'error',
                'message': 'Invalid city or item index'
            }), 400
        
        # Get the item to update
        item = current_data[city][item_index].copy()  # Make a copy to avoid modifying original
        
        # Update the specified price
        item[field] = value
        
        # Recalculate flip metrics
        metrics = calculator.calculate_flip_metrics(
            current_data={
                'buy_price_max': item['buy_price'],
                'sell_price_min': item['sell_price'],
                'sell_price_min_date': item.get('timestamp'),
                'avg_price': item.get('avg_price', 0)  # Include historical average price
            },
            historical_volume=item.get('avg_item_count', 0),
            quality=item.get('quality', 1)
        )
        
        if not metrics:
            # Remove the item if it no longer meets the criteria
            current_data[city].pop(item_index)
            return jsonify({
                'status': 'filtered',
                'message': 'Item removed due to not meeting criteria'
            }), 200
            
        # Update the item with new metrics
        item.update(metrics)
        current_data[city][item_index] = item
        return jsonify(item)
            
    except Exception as e:
        logger.error(f"Error updating prices: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/market-stats')
def get_market_stats():
    """Get overall market statistics."""
    try:
        stats = {
            'total_opportunities': sum(len(items) for items in current_data.values()),
            'opportunities_by_city': {
                city: len(items) for city, items in current_data.items()
            },
            'top_profit_items': [],
            'top_roi_items': []
        }
        
        # Get top items across all cities
        all_items = []
        for city, items in current_data.items():
            for item in items:
                all_items.append({**item, 'city': city})
                
        # Sort by profit and ROI
        profit_sorted = sorted(all_items, key=lambda x: x['potential_profit'], reverse=True)
        roi_sorted = sorted(all_items, key=lambda x: x['roi_percent'], reverse=True)
        
        # Take top 10 for each metric
        stats['top_profit_items'] = profit_sorted[:10]
        stats['top_roi_items'] = roi_sorted[:10]
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting market stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 