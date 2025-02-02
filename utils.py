# utils.py

def split_into_batches(items, max_url_length, base_url, endpoint_template):
    """
    Splits the list of items into batches so that the URL formed with the given endpoint_template 
    does not exceed max_url_length.
    
    The endpoint_template is expected to be a string with placeholders {items} and {locations}.
    For example: "/api/v2/stats/prices/{items}.json?locations={locations}"
    
    Parameters:
      items: list of unique_name identifiers (strings, e.g., "T4_BAG", "T8_PLANKS")
      max_url_length: maximum allowed URL length (e.g., 4096)
      base_url: base URL string (e.g., "https://west.albion-online-data.com")
      endpoint_template: string template for the endpoint
      
    Returns:
      A list of lists, where each inner list is a batch of items that can be safely inserted into the URL.
    """
    # Build the constant part of the URL (with empty items placeholder)
    dummy_url = base_url + endpoint_template.format(items="", locations="City")
    available_length = max_url_length - len(dummy_url)

    batches = []
    current_batch = []
    current_length = 0

    for item in items:
        # Each item will be separated by a comma (if not the first in the batch)
        additional_length = len(item) + (1 if current_batch else 0)
        if current_length + additional_length > available_length:
            batches.append(current_batch)
            current_batch = [item]
            current_length = len(item)
        else:
            current_batch.append(item)
            current_length += additional_length

    if current_batch:
        batches.append(current_batch)

    return batches
