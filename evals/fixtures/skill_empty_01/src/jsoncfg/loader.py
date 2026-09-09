import json


def load_config(text: str) -> dict:
    return json.loads(text)
