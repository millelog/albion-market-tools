import json
import re
import os
from pathlib import Path

def load_item_lookup():
    # Load the items reference data
    with open('ids/items.json', 'r', encoding='utf-8') as f:
        items_data = json.load(f)

    # Create a lookup dictionary for faster matching, skipping invalid entries
    item_lookup = {}
    for item in items_data:
        try:
            if item.get('LocalizedNames') and item.get('UniqueName'):
                en_name = item['LocalizedNames'].get('EN-US')
                if en_name:
                    # Store the base UniqueName without any @X suffixes
                    base_unique_name = re.sub(r'@\d+', '', item['UniqueName'])
                    item_lookup[en_name] = base_unique_name
        except Exception as e:
            print(f"Warning: Could not process item: {item}")
            print(f"Error: {e}")
    
    return item_lookup

def process_item(item, item_lookup):
    # Extract the name and tier/enchantment
    match = re.match(r'(.*?)\s*\[([\d.]+)\]', item['name'])
    if match:
        base_name = match.group(1).strip()
        tier_info = match.group(2)
        
        # Find the corresponding UniqueName
        unique_name = item_lookup.get(base_name)
        
        if unique_name:
            # Extract enchantment level (if any)
            enchant_level = tier_info.split('.')[-1]
            # Add enchantment suffix if level > 0
            if enchant_level != '0' and float(enchant_level) > 0:
                unique_name = f"{unique_name}@{enchant_level}"
            
            # Add the UniqueName to the item
            item['unique_name'] = unique_name
            return item
        else:
            print(f"Warning: Could not find UniqueName for {base_name}")
            return None
    return None

def process_city_file(pre_file_path, item_lookup):
    # Load the pre-popular items data
    with open(pre_file_path, 'r', encoding='utf-8') as f:
        pre_data = json.load(f)

    # Process each item in the items list
    processed_items = []
    for item in pre_data['items']:
        processed_item = process_item(item, item_lookup)
        if processed_item:
            processed_items.append(processed_item)

    return processed_items

def main():
    # Create the popular_items directory if it doesn't exist
    Path('popular_items').mkdir(exist_ok=True)

    # Load the item lookup dictionary once
    item_lookup = load_item_lookup()

    # Get all city files from pre_popular_items directory
    pre_popular_dir = Path('pre_popular_items')
    for pre_file in pre_popular_dir.glob('*.json'):
        city_name = pre_file.stem
        output_file = Path(f'popular_items/{city_name}.json')

        # Process the pre-popular items
        new_items = process_city_file(pre_file, item_lookup)

        if output_file.exists():
            # If the output file exists, merge with existing data
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_items = json.load(f)

            # Create a set of existing item names
            existing_names = {item['name'] for item in existing_items}

            # Add only new items that don't exist in the current file
            for item in new_items:
                if item['name'] not in existing_names:
                    existing_items.append(item)

            final_items = existing_items
        else:
            # If the output file doesn't exist, use all new items
            final_items = new_items

        # Save the updated data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_items, f, indent=2)
        
        print(f"Processed {city_name}: {len(final_items)} items total")

if __name__ == "__main__":
    main()