# main.py
import logging
from web_viewer import app
from config import CITIES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the Albion Market Tools application."""
    try:
        logger.info("Starting Albion Market Tools web server...")
        logger.info(f"Monitoring markets in cities: {', '.join(CITIES)}")
        
        # Run the Flask application
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        raise

if __name__ == '__main__':
    main()
