import json
from pathlib import Path

CONFIG_FILE = '.config.json'

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
        'workspace_files': [],  # 每个文件项格式：{path: str, type: 'resume'|'jd', content: str}
        'supported_models': [
            'ollama/mistral:7b-instruct',
            'openai/gpt-4',
            'anthropic/claude-2',
            'cohere/command-nightly',
            'gemini/gemini-2.0-flash'  # 修正模型名称格式
        ]
    }
    # 初始化config保证包含supported_models字段
    config = default_config.copy()
    default_config.update(config)
    return default_config

def get_model():
    config = load_config()
    return config.get("model", "ollama/mistral:7b-instruct")

def set_model(model):
    # 放宽模型名称格式验证，允许无版本号
    if '/' not in model:
        raise ValueError("模型名称格式应为 provider/model[:version]")
    
    config = load_config()
    config["model"] = model
    save_config(config)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
