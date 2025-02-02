import json
import re

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

# Load the Lymhurst data
with open('popular_items/Lymhurst.json', 'r', encoding='utf-8') as f:
    items_list = json.load(f)

# Process each item
for item in items_list:
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
        else:
            print(f"Warning: Could not find UniqueName for {base_name}")

# Save the updated data
with open('popular_items/Lymhurst.json', 'w', encoding='utf-8') as f:
    json.dump(items_list, f, indent=2)