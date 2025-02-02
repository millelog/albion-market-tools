# data_storage.py
import json
import os
from config import CITIES


def load_popular_items():
    """
    Load popular items data from individual city JSON files in the popular_items directory.
    Returns a dict mapping city names to their popular items lists.
    """
    popular_items = {}
    
    for city in CITIES:
        file_path = os.path.join("popular_items", f"{city}.json")
        try:
            with open(file_path, "r") as f:
                popular_items[city] = json.load(f)
        except FileNotFoundError:
            print(f"Warning: No popular items file found for {city}")
            popular_items[city] = []
            
    return popular_items


def save_popular_items(city, data):
    """
    Save popular items data for a specific city.
    
    Parameters:
        city: Name of the city (e.g., "Lymhurst")
        data: List of popular items for that city
    """
    file_path = os.path.join("popular_items", f"{city}.json")
    os.makedirs("popular_items", exist_ok=True)
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
