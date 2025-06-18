import json
from pathlib import Path

CONFIG_FILE = Path.home() / 'config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        config = {}
    
    # 合并默认配置保证新增字段兼容
    default_config = {
        'default_model': 'ollama/mistral:7b-instruct',
        'last_model': None,
        'model': 'ollama/mistral:7b-instruct',
        'workspace_files': []
    }
    default_config.update(config)
    return default_config

def get_model():
    config = load_config()
    return config.get("model", "ollama/mistral:7b-instruct")

def set_model(model):
    config = load_config()
    config["model"] = model
    save_config(config)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
