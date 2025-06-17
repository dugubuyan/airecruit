import json
from pathlib import Path

CONFIG_FILE = Path.home() / 'config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'default_model': 'gpt-3.5-turbo', 'last_model': None}

def get_model():
    config = load_config()
    return config.get("model", "gpt-4")

def set_model(model):
    config = load_config()
    config["model"] = model
    save_config(config)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
