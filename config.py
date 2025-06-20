import json
from pathlib import Path

CONFIG_FILE = '.config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    
    # 默认配置
    default_config = {
        'default_model': 'ollama/mistral:7b-instruct',
        'last_model': None,
        'model': 'ollama/mistral:7b-instruct',
        'workspace_files': [],
        'supported_models': [
            'ollama/mistral:7b-instruct',
            'openai/gpt-4',
            'anthropic/claude-2', 
            'cohere/command-nightly',
            'gemini/gemini-2.0-flash'
        ]
    }
    
    # 合并默认配置（保留现有配置字段）
    for key in default_config:
        if key not in config:
            config[key] = default_config[key]
            
    return config

def get_model():
    config = load_config()
    return config.get("model", "ollama/mistral:7b-instruct")

def set_model(model):
    # 放宽模型名称格式验证，允许无版本号
    if '/' not in model:
        raise ValueError("模型名称格式应为 provider/model[:version]")
    
    config = load_config()
    if model not in config.get('supported_models', []):
        raise ValueError(f"不支持该模型，请使用/model ls查看支持列表")
    config["model"] = model
    save_config(config)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
