import json
from datetime import datetime
from pathlib import Path





def write_quote_in_json(response_of_ai):
    """
    Will save the date to the quote, so we can track the quotes.
    """
    DATA_FILE = Path("data.json")
    if quote_written_today():
        return 
    todaysdate = datetime.today().strftime('%Y-%m-%d')
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            quotes = json.load(f)
            if not isinstance(quotes, dict):
                raise ValueError
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        quotes = {}
    if todaysdate in quotes:
        return 
    
    quotes[todaysdate] = response_of_ai 
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(quotes, f, ensure_ascii=False, indent=4)
    return response_of_ai


def quote_written_today():
    todaysdate = datetime.today().strftime('%Y-%m-%d')
    with open("data.json") as json_file:
        json_data = json.load(json_file)
    if (str(todaysdate)) not in str(json_data):
        return False
    return True

          # ← your JSON now lives in “data”

def all_values(obj):
    """
    Recursively yield every primitive value that appears anywhere
    inside a JSON structure (dicts, lists, nested mixtures).
    """
    if isinstance(obj, dict):
        for v in obj.values():
            yield from all_values(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from all_values(item)
    else:                         # str, int, float, bool, None
        yield obj

def get_values():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        return  list(all_values(data))   # materialize the generator if you need a list
    
def motivational(response):
    return write_quote_in_json(response)

        
        