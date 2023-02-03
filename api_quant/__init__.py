import json
import os

with open(os.path.join(os.path.dirname(__file__), '../settings/keys.json')) as f:
    _key_info = json.load(f)

def get_api_key_pair(exchange: str) -> tuple[str, str]:
    return _key_info[exchange]['api'], _key_info[exchange]['secret']

def get_api_key_pairs(exchange: str) -> list[tuple[str, str]]:
    return [(k['api'], k['secret']) for k in _key_info[exchange]]
